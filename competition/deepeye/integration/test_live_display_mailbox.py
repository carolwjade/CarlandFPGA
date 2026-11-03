import threading
import unittest
from competition.deepeye.integration.live_display_mailbox import LatestDisplayMailbox


class MailboxChecks(unittest.TestCase):
    def box(self):return LatestDisplayMailbox(run_id='run',world_epoch='epoch',admission_mode='BOARD_PWM')
    def sample(self,n):return {'native':{'revision':str(n),'speed_m_s':.1,'admission_mode':'BOARD_PWM'},'host':{'receive_qpc_ns':n}}
    def test_latest_and_copy_do_not_change_actual_source(self):
        b=self.box();first=self.sample(1);b.publish(first,world_epoch='epoch')
        first['native']['speed_m_s']=99
        for n in range(2,20):b.publish(self.sample(n),world_epoch='epoch')
        r=b.receive(timeout=0);self.assertEqual(r['packet']['host']['receive_qpc_ns'],19)
        self.assertEqual(r['packet']['source'],'FPGA_OUTPUT')
        r['packet']['native']['speed_m_s']=88
        self.assertEqual(b.receive(timeout=0)['packet']['native']['speed_m_s'],.1)
    def test_repeated_poll_does_not_publish_or_renew_time(self):
        b=self.box();b.publish(self.sample(1),world_epoch='epoch')
        self.assertIsNone(b.receive(1,timeout=0)['packet'])
        self.assertEqual(b.receive(timeout=0)['packet']['host']['receive_qpc_ns'],1)
    def test_terminal_wakes_waiter_and_never_restarts(self):
        b=self.box();ready=threading.Event();received=[]
        def wait():
            ready.set();received.append(b.receive(timeout=2))
        t=threading.Thread(target=wait);t.start();ready.wait(1);b.close('actual_arrived');t.join(2)
        self.assertFalse(t.is_alive());self.assertTrue(received[0]['closed'])
        self.assertEqual(received[0]['reason'],'actual_arrived')
        with self.assertRaises(RuntimeError):b.publish(self.sample(2),world_epoch='epoch')
    def test_new_epoch_is_never_silently_rebound(self):
        b=self.box()
        with self.assertRaises(ValueError):b.publish(self.sample(1),world_epoch='other')

    def test_close_discards_unconsumed_positive_sample(self):
        b=self.box();b.publish(self.sample(1),world_epoch='epoch');b.close('actual_stop')
        self.assertIsNone(b.receive(timeout=0)['packet'])

    def test_actual_mode_cannot_be_relabeled(self):
        b=self.box();p=self.sample(1);p['native']['admission_mode']='PC_DIRECT'
        with self.assertRaises(ValueError):b.publish(p,world_epoch='epoch')


if __name__=='__main__':unittest.main()
