import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock
from tracker import Tracker
from navigation_config import load_navigation
from quadrotor_msgs.msg import PositionCommand
from nav_msgs.msg import Odometry

class PhaseSafety(unittest.TestCase):
    def node(self,flag):
        tuning=load_navigation()['tracker'];odom=Odometry();odom.pose.pose.position.z=1.;odom.pose.pose.orientation.w=1.
        ref=PositionCommand();ref.position.x=-.1;ref.position.z=1.;ref.trajectory_flag=flag
        return NS(get_clock=lambda:NS(now=lambda:NS(nanoseconds=10_000_000_000)),odom=odom,reference=ref,
            last_odom=10.,last_reference=10.,tuning=tuning,config={'max_velocity':.3},semantic_enabled=False,
            previous_update=9.97,previous_rate=.2,publisher=NS(publish=Mock()),last_status=0.,status_pub=NS(publish=Mock()))
    def test_stale_phase_cannot_rotate_towards_old_reference(self):
        n=self.node(PositionCommand.TRAJECTORY_STATUS_EMPTY);Tracker.update(n)
        command=n.publisher.publish.call_args.args[0]
        self.assertEqual(command.angular.z,0.);self.assertEqual(command.linear.x,0.)
        self.assertIn('STALE_PHASE',n.status_pub.publish.call_args.args[0].data)
    def test_valid_phase_retains_controller(self):
        n=self.node(PositionCommand.TRAJECTORY_STATUS_READY);Tracker.update(n)
        self.assertNotEqual(n.publisher.publish.call_args.args[0].angular.z,0.)
if __name__=='__main__':unittest.main()
