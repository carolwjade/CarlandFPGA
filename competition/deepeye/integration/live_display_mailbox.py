"""Single native reader publishes actual state to one separate display IO owner.

This mailbox has no native RPC, transport, clock renewal or motion authority.
The caller publishes only samples validated by its existing NativeClient.
"""
import copy
import threading


class LatestDisplayMailbox:
    def __init__(self, *, run_id, world_epoch, admission_mode):
        if not all(type(v) is str and v and len(v)<=160 for v in (run_id,world_epoch)):
            raise ValueError('explicit run and epoch required')
        if admission_mode not in ('BOARD_PWM','PC_DIRECT'):
            raise ValueError('actual frozen admission mode required')
        self.run_id,self.world_epoch=run_id,world_epoch
        self.admission_mode=admission_mode
        self.source='FPGA_OUTPUT' if admission_mode=='BOARD_PWM' else 'PC_DIRECT'
        self._condition=threading.Condition()
        self._version=0
        self._latest=None
        self._closed=False
        self._reason=None

    def publish(self, actual_sample, *, world_epoch):
        if world_epoch!=self.world_epoch:
            raise ValueError('new epoch requires a new mailbox')
        if type(actual_sample) is not dict or set(actual_sample)!={'native','host'}:
            raise ValueError('original native-client state sample required')
        if actual_sample['native'].get('admission_mode')!=self.admission_mode:
            raise ValueError('actual native mode differs from frozen display source')
        # Deep copy before locking: consumers cannot mutate Root's accepted state.
        packet=dict(run_id=self.run_id,source=self.source,**copy.deepcopy(actual_sample))
        with self._condition:
            if self._closed:raise RuntimeError('closed mailbox cannot restart')
            self._latest=packet
            self._version+=1
            self._condition.notify()
            return self._version

    def receive(self, after_version=0, *, timeout=None):
        """Returns only the latest publication; old frames never queue for replay."""
        with self._condition:
            self._condition.wait_for(lambda:self._closed or self._version>after_version,timeout)
            return dict(version=self._version,
                packet=copy.deepcopy(self._latest) if not self._closed and self._version>after_version else None,
                closed=self._closed,reason=self._reason)

    def close(self, reason):
        if type(reason) is not str or not reason:raise ValueError('explicit terminal reason required')
        with self._condition:
            if not self._closed:
                self._closed=True;self._reason=reason
                self._condition.notify_all()
