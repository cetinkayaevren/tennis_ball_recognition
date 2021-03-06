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

"""
Before use !

You might be need this command for terminal  ->  'sudo rmmod peaq_wmi'

"""
coordinates_x = []
coordinates_y = []
mean_x = None
mean_y = None
pxTopic = rospy.get_param('RoverReachImage/ImageProcessing/pub_pxCoordinates','/px_coordinates')
resize = rospy.get_param('RoverReachImage/ImageProcessing/resize',False)
resize_width = rospy.get_param('RoverReachImage/ImageProcessing/resize_width',640)
resize_height = rospy.get_param('RoverReachImage/ImageProcessing/resize_height',480)

# Low Pass Filter with a Period = 0.5 seconds
def mean_value(co_x, co_y):
	global mean_x
	global mean_y
	global coordinates_x
	global coordinates_y
	#print("-----------------------")
	#print("Length of arrays before cleaning..\nx,y : {0}--{1}".format(len(co_x),len(co_y)))

	mean_x = float(sum(co_x) / max(len(co_x), 1))
	mean_y = float(sum(co_y) / max(len(co_y), 1))

	#print("Latest Coordinates:{0}--{1}\n ".format(mean_x, mean_y))
	#print("Center : {0}--{1}\n ".format(mean_x, mean_y))           !!!!
	#frees arrays of coordinates
	coordinates_x = []
	coordinates_y = []
	

class LowPassFilter(Thread):
	global coordinates_x
	global coordinates_y
	def __init__(self, event):
		Thread.__init__(self)
		self.stopped = event

	def run(self):
		while not self.stopped.wait(0.1):
			# Call the function if any coordinates detected
			if len(coordinates_y) + len(coordinates_x) != 0:
				mean_value(coordinates_x,coordinates_y)



def main():
	#Coordinates
	global coordinates_x
	global coordinates_y
	coordinates_x = [0]
	coordinates_y = [0]
	global xCoordinate
	global yCoordinate
	global resize
	global resize_width, resize_height
	global mean_x
	global mean_y

	#Start Timer
	stopFlag = Event()
	thread = LowPassFilter(stopFlag)
	thread.start()

	#Video Path
	#video_path = '' #Enter any video path relative to the script file

	#Treshold for Green in BGR Color Space
	greenLower = (19,56, 80)  # Less accurate -> (29,86,6)  kullanilan(29,50,150)   med cim (15,0, 156)
	greenUpper = (69,255,255)  #kullanilan   (64,255,255)        med cim (88,255,255)

	#Detection in real time
	camera=cv2.VideoCapture(0)

	bridge = CvBridge()   
	kernel = np.ones((5,5),np.uint8)

	#camera.set(3, 920)
	#camera.set(4, 1080)

	#Detection over video
	#camera = cv2.VideoCapture("video path")

	while not rospy.is_shutdown():#Use this command for detection over a video instead 'True' --> 'camera.isOpened()'


		#Read Frame
		ret, frame = camera.read()
		height, width = frame.shape[:2] #frame = frame[0:height,0:int(width*0.5)]

		# Resize and Add Noise
		if resize == True:
			frame = imutils.resize(frame,width = resize_width, height= resize_height)

		# blurring the frame that's captured
		frame_gau_blur = cv2.GaussianBlur(frame, (3, 3), 1) 

		hsv = cv2.cvtColor(frame_gau_blur, cv2.COLOR_BGR2HSV)

		green_range = cv2.inRange(hsv, greenLower, greenUpper)
		res_green = cv2.bitwise_and(frame_gau_blur,frame_gau_blur, mask=green_range)
		kernel = np.ones((5, 5), np.uint8)


		# Masking
		mask = cv2.erode(res_green, kernel, iterations=2)
		mask = cv2.dilate(mask, kernel, iterations=3)
		#mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


		blue_s_gray = cv2.cvtColor(res_green, cv2.COLOR_BGR2GRAY)
		blue_s_gray= cv2.morphologyEx(blue_s_gray, cv2.MORPH_OPEN, kernel)
		#blue_s_gray = cv2.morphologyEx(blue_s_gray, cv2.MORPH_CLOSE, kernel)
		canny_edge = cv2.Canny(blue_s_gray, 200,210)  #100,110
		canny_edge = cv2.GaussianBlur(canny_edge, (5, 5), 0)
		#canny_edge = cv2.adaptiveThreshold(canny_edge, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 115, 1)
		# applying HoughCircles
		rows=blue_s_gray.shape[0]
		circles = cv2.HoughCircles(canny_edge, cv2.HOUGH_GRADIENT, dp=2, minDist=9, param1=10, param2=20, minRadius=0, maxRadius=0)
		cnts = cv2.findContours(blue_s_gray.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]  #blue_s_gray.copy
		#cnts = imutils.grab_contours(cnts)
		center = None
	

		#Execute only at least one contour found
		if len(cnts) > 0 and circles is not None:	
			c = max(cnts, key=cv2.contourArea)
			(x, y), radius = cv2.minEnclosingCircle(c)
			M = cv2.moments(c)
			if M["m00"] !=0:
				center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
			else:
				center=(0,0)
			# Select contours with a size bigger than 0.1
			if radius > 0.1 :
				# draw the circle and center
				cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
				cv2.circle(frame, center, 5, (0, 0, 255), -1)
				#print(radius)

				img = Image()
				#height, width = frame.shape[:2]
				img = bridge.cv2_to_imgmsg(frame,"bgr8")
				imagePublisher.publish(img)

				#Hold Coordinates
				coordinates_x.append(center[0])
				coordinates_y.append(center[1])
		
				#Free Coordinates if timer is up
				if set == 0:
					coordinates_x = []
					coordinates_y = []
					xCoordinate = 0
					yCoordinate = 0

				frameHeight = frame.shape[0]
				frameWidth = frame.shape[1]
				coordinatePublisher.publish(str(mean_x) +","+ str(mean_y) + "," + str(frameWidth) + "," + str(frameHeight)+ "," + str(radius))

		else:
			coordinatePublisher.publish("-")
			print("-")
				

		cv2.imshow("Frame", frame)
		cv2.imshow("canny", canny_edge)
		cv2.imshow("blue_s_gray", blue_s_gray)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			stopFlag.set()
			break

	stopFlag.set()
	camera.release()
	cv2.destroyAllWindows()


if __name__ == '__main__':

	try:
		rospy.init_node('rover_detect_ball')        
		coordinatePublisher = rospy.Publisher(pxTopic,String,queue_size = 1)        
		imagePublisher = rospy.Publisher("/image_elevation",Image,queue_size = 10)

		while not rospy.is_shutdown():
			main()
	except rospy.ROSInterruptException:
		pass
