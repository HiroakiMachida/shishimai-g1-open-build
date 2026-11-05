"""ROS 2 Foxy adapter for the public HIM safety interface, no motor transport."""
import json,time,sys
sys.path.insert(0,'/submission')
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile,ReliabilityPolicy,DurabilityPolicy
from std_msgs.msg import String
from std_srvs.srv import Trigger
from him_safety_interfaces.msg import RobotFeedback,JointCommand,Abort
from policy import Policy,KP,KD

class Shishimai(Node):
    def __init__(self):
        super().__init__('shishimai_g1')
        self.policy=Policy();self.session=None;self.sequence=0;self.done=False
        self.feedback=None;self.state=None;self.state_at=0;self.feedback_at=0;self.last=0
        self.arm_future=None;self.arm_at=0;self.sent=False
        feedback_qos=QoSProfile(depth=8,reliability=ReliabilityPolicy.BEST_EFFORT)
        abort_qos=QoSProfile(depth=1,reliability=ReliabilityPolicy.RELIABLE,durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.pub=self.create_publisher(JointCommand,'/safety/precheck',QoSProfile(depth=1,reliability=ReliabilityPolicy.RELIABLE))
        self.create_subscription(RobotFeedback,'/safety/policy_observation',self.on_feedback,feedback_qos)
        self.create_subscription(String,'/safety/policy_state',self.on_state,feedback_qos)
        self.create_subscription(Abort,'/safety/abort',self.on_abort,abort_qos)
        self.arm=self.create_client(Trigger,'/safety/checker/arm')
        self.create_timer(.02,self.tick)

    def on_feedback(self,msg):self.feedback=msg;self.feedback_at=time.monotonic()
    def on_state(self,msg):
        try:self.state=json.loads(msg.data);self.state_at=time.monotonic()
        except (ValueError,TypeError):self.done=True
    def on_abort(self,msg):
        self.get_logger().error('Safety abort: '+str(msg.reason));self.done=True

    def tick(self):
        if self.done:return
        now=time.monotonic()
        if self.session is None:
            if self.arm_future is not None and self.arm_future.done():
                result=self.arm_future.result();self.arm_future=None
                if result and result.success:self.session=result.message
            elif self.arm_future is None and now-self.arm_at>.5 and self.arm.service_is_ready():
                self.arm_at=now;self.arm_future=self.arm.call_async(Trigger.Request())
            if self.session is None:return
        if self.feedback is None or self.state is None:return
        if max(now-self.feedback_at,now-self.state_at)>.12:
            if self.sent:self.get_logger().error('Stale telemetry; stop publishing');self.done=True
            return
        state=self.state;feedback=self.feedback
        # Read-only host readiness prevents the choreography clock advancing during setup.
        obs={'q':np.array(feedback.q),'dq':np.array(feedback.dq),
             'quat':np.array(state['quat']),'gyro':np.array(state['gyro'])}
        try:
            if not state.get('control_ready',False):
                cmd={'q':obs['q'],'dq':np.zeros(29),'kp':KP,'kd':KD,'tau':np.zeros(29)}
            else:cmd=self.policy.act(obs)
            message=JointCommand();message.session_id=self.session;message.observation_id=feedback.observation_id
            message.sequence=self.sequence
            for k in ('q','dq','kp','kd','tau'):setattr(message,k,[float(v) for v in cmd[k]])
            self.pub.publish(message);self.sequence+=1;self.sent=True
        except Exception as exc:
            self.get_logger().error(str(exc));self.done=True

def main():
    rclpy.init();node=Shishimai()
    try:
        while rclpy.ok() and not node.done:rclpy.spin_once(node,timeout_sec=.02)
    finally:node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
