import asyncio
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fpga_mesh.controller import ActionResult, Controller
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind, task_id_from_message
from fpga_mesh.store import SQLiteStore


def instruction(message_id: str = "msg-1", text: str = "work") -> Envelope:
    return Envelope(
        message_id=message_id,
        project_id="fpga-main",
        sender="human-1",
        recipient="A/Astra-A",
        task_id=task_id_from_message("group-1", "om_123"),
        task_version=1,
        sent_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
        kind=MessageKind.HUMAN_INSTRUCTION,
        source=SourceKind.HUMAN,
        payload={"text": text},
        platform_group_id="group-1",
        platform_message_id="om_123",
    )


def stop_instruction() -> Envelope:
    return Envelope(
        message_id="stop-1",
        project_id="fpga-main",
        sender="human-1",
        recipient="*",
        task_id=task_id_from_message("group-1", "om_stop"),
        task_version=1,
        sent_at=datetime(2026, 9, 30, 8, 1, tzinfo=timezone.utc),
        kind=MessageKind.STOP_REQUEST,
        source=SourceKind.HUMAN,
        payload={"scope": "all"},
        platform_group_id="group-1",
        platform_message_id="om_stop",
    )


def resume_instruction(sent_at: datetime) -> Envelope:
    return Envelope(
        message_id=f"resume-{sent_at.isoformat()}",
        project_id="fpga-main",
        sender="human-1",
        recipient="*",
        task_id=task_id_from_message("group-1", "om_resume"),
        task_version=1,
        sent_at=sent_at,
        kind=MessageKind.RESUME_REQUEST,
        source=SourceKind.HUMAN,
        payload={"scope": "all"},
        platform_group_id="group-1",
        platform_message_id=f"om_resume_{sent_at.isoformat()}",
    )


class FakeGateway:
    def __init__(self, fail_first: bool = False, delay: float = 0.0):
        self.calls = []
        self.fail_first = fail_first
        self.delay = delay

    async def handle(self, message: Envelope):
        self.calls.append(message.message_id)
        if self.fail_first:
            self.fail_first = False
            raise RuntimeError("temporary failure")
        if self.delay:
            await asyncio.sleep(self.delay)
        return ActionResult(accepted=True, output={"message_id": message.message_id})


class ControllerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "state.sqlite"
        self.store = SQLiteStore(self.db_path)
        self.gateway = FakeGateway()
        self.controller = Controller(self.store, self.gateway)

    async def asyncTearDown(self):
        await self.controller.stop()
        self.store.close()
        self.tmp.cleanup()

    async def test_duplicate_platform_event_causes_one_model_call(self):
        first = instruction("internal-1")
        duplicate = replace(
            first,
            message_id="internal-2",
            platform_event_id="event-2",
        )
        await self.controller.offer(first)
        await self.controller.offer(duplicate)
        await self.controller.run_until_idle()
        self.assertEqual(self.gateway.calls, ["internal-1"])

    async def test_idle_wait_makes_no_model_calls(self):
        await self.controller.offer(instruction())
        await self.controller.run_until_idle()
        calls = list(self.gateway.calls)
        await self.controller.wait_for_work(timeout=0.05)
        self.assertEqual(self.gateway.calls, calls)

    async def test_stop_request_blocks_new_dispatch_immediately(self):
        await self.controller.offer(stop_instruction())
        await self.controller.run_until_idle()
        await self.controller.offer(instruction("later", "new task"))
        await self.controller.run_until_idle()
        self.assertEqual(self.gateway.calls, [])
        self.assertTrue(self.controller.dispatch_blocked)

    async def test_only_a_later_resume_can_release_a_human_pause(self):
        stop = stop_instruction()
        await self.controller.offer(stop)
        await self.controller.run_until_idle()

        early = resume_instruction(stop.sent_at - timedelta(minutes=1))
        await self.controller.offer(early)
        await self.controller.run_until_idle()
        self.assertTrue(self.controller.dispatch_blocked)

        later = resume_instruction(stop.sent_at + timedelta(minutes=1))
        await self.controller.offer(later)
        await self.controller.run_until_idle()
        self.assertFalse(self.controller.dispatch_blocked)

    async def test_failure_is_retried_after_restart_without_duplicate_processing(self):
        failing_gateway = FakeGateway(fail_first=True)
        controller = Controller(self.store, failing_gateway)
        await controller.offer(instruction("internal-1"))
        await controller.run_until_idle()
        self.assertEqual(failing_gateway.calls, ["internal-1"])
        self.assertEqual(len(self.store.pending_inbound()), 1)

        restart_gateway = FakeGateway()
        restarted = Controller(self.store, restart_gateway)
        await restarted.run_until_idle()
        self.assertEqual(restart_gateway.calls, ["internal-1"])
        self.assertEqual(self.store.pending_inbound(), [])

    async def test_short_wait_returns_when_event_arrives(self):
        async def deliver():
            await asyncio.sleep(0.02)
            await self.controller.offer(instruction())

        task = asyncio.create_task(deliver())
        received = await self.controller.wait_for_work(timeout=0.5)
        self.assertTrue(received)
        await task

    async def test_controller_does_not_wake_on_expired_message(self):
        expired = replace(
            instruction("expired"),
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        await self.controller.offer(expired)
        await self.controller.run_until_idle()
        self.assertEqual(self.gateway.calls, [])


if __name__ == "__main__":
    unittest.main()
