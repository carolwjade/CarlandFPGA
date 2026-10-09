import unittest

from scripts.smoke_parent_child import build_smoke_message


class ParentChildSmokeTests(unittest.TestCase):
    def test_b_and_c_smoke_messages_address_their_local_astra(self):
        for node in ("B", "C"):
            with self.subTest(node=node):
                message = build_smoke_message(node)
                self.assertEqual(message.recipient, f"{node}/Astra-{node}")
                self.assertIn("fpga_child_delegate", message.payload["text"])
                self.assertIn("CHILD_OK", message.payload["text"])


if __name__ == "__main__":
    unittest.main()
