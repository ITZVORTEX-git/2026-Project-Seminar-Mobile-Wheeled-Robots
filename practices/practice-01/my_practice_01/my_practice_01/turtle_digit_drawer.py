import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist 
from turtlesim.msg import Pose 
import math

class digitDrawer(Node):
    def __init__(self):
        super().__init__("turtle_digit_drawer")
        self.declare_parameter("turtle_name", "turtle1")
        self.declare_parameter("digit", 1)
        self.turtleName = self.get_parameter("turtle_name").value
        digit = self.get_parameter("digit").value
        if digit == 1:
            self.actions = [
                ('t', -math.pi / 2),
                ('d', 3.0)
            ]
        else:
            self.actions = [
                ('t', 0.0),
                ('d', 2.0),
                ('t', -math.pi / 2),
                ('d', 3.0)
            ]
        self.actionIndex = 0
        self.dStart = None
        self.publisher = self.create_publisher(Twist, f'/{self.turtleName}/cmd_vel', 1)
        self.subscription = self.create_subscription(Pose, f'/{self.turtleName}/pose', self.poseCallback, 10)
    
    def poseCallback(self, message):
        if self.actionIndex >= len(self.actions):
            self.stop()
            return
        actionType, target = self.actions[self.actionIndex]
        match actionType:
            case "t":
                self.turn(message, target)
            case "d":
                self.drive(message, target)
    
    def turn(self, message, target):
        diff = target - message.theta
        diff = math.atan2(math.sin(diff), math.cos(diff))
        if abs(diff) < 0.01:
            self.stop()
            self.actionIndex += 1
            return
        twist = Twist()
        twist.angular.z = 1.0 if diff > 0 else -1.0
        self.publisher.publish(twist)
    
    def drive(self, message, distance):
        if self.dStart == None:
            self.dStart = (message.x, message.y)
        travelled = math.dist(self.dStart, (message.x, message.y))
        if travelled >= distance - 0.05:
            self.stop()
            self.dStart = None
            self.actionIndex += 1
            return
        twist = Twist()
        twist.linear.x = 1.0
        self.publisher.publish(twist)
    
    def stop(self):
        self.publisher.publish(Twist())

def main(args=None):
    rclpy.init(args=args)
    node = digitDrawer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()



if __name__ == '__main__':
    main()
