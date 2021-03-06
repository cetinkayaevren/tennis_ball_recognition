#!/usr/bin/env python


from threading import Timer,Thread,Event
import numpy as np
import imutils
import cv2
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image
import cv2
import rosparam
from cv_bridge import CvBridge, CvBridgeError
import rosparam

def main():
    camera=cv2.VideoCapture(0)
    bridge = CvBridge()   
    camera.set(3, 480)
    camera.set(4, 360)
    
    while not rospy.is_shutdown():#Use this command for detection over a video instead 'True' --> 'camera.isOpened()'


        #Read Frame
        ret, frame = camera.read()

        img = Image()
        #height, width = frame.shape[:2]
        img = bridge.cv2_to_imgmsg(frame,"bgr8")
        imagePublisher.publish(img)



        cv2.imshow("Frame", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':

    try:
        rospy.init_node('cozunurluk')        
        imagePublisher = rospy.Publisher("/image_elevation",Image,queue_size = 10)

        while not rospy.is_shutdown():
            main()
    except rospy.ROSInterruptException:
        pass
