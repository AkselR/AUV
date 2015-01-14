#!/usr/bin/python
# -*- coding: utf-8 -*-

import cv2
import cv2.cv as cv
import numpy as np 
import argparse

height = 480
width = 640

cap = cv2.VideoCapture(0)
cap.set(cv.CV_CAP_PROP_FPS, 1.0)
cap.set(cv.CV_CAP_PROP_FRAME_HEIGHT,height)
cap.set(cv.CV_CAP_PROP_FRAME_WIDTH, width)

listOfRect = list()
listeOfCirles = list()
frame = None
rectCnt = None

centerX = None
centerY = None

class Circles:
	def _init(self): pass

	def lookForCir(self, frame):
		gaussianblur = cv2.GaussianBlur(frame,(5,5),0)
		#hsv = cv2.cvtColor(gaussianblur,cv2.COLOR_BGR2HSV)
	
		lower_color = np.array([0,0,175])
		upper_color = np.array([100,100,256])

		#Threshold the HSV image to get only blue colors
		mask = cv2.inRange(gaussianblur, lower_color,upper_color)
	
	
		#Takes matrix(3,3) and find a average pixel. Images gets more smooth
		kernel = np.ones((5,5),np.float32)/25
		dst = cv2.filter2D(mask,-1,kernel)

		#Find circles
		circles = cv2.HoughCircles(dst, cv.CV_HOUGH_GRADIENT, 1, 500,param1 = 50, param2 =30, minRadius=15, maxRadius=400)
	
		#Draw circles in original images
		if circles is not None:
			circles = np.uint16(np.around(circles))
			for i in circles [0,:]:
				#Draw outer circle and center
				cv2.circle(frame, (i[0],i[1]), i[2],(0,255,0),2)
				cv2.circle(frame, (i[0],i[1]),2,(0,255,0),4)
				#Center of circle
				centerX = i[0]
				centerY = i[1]
			
				listeOfCirles.append(centerX)
				#Calculate what direction the AUV need to go to get the object in center.
				navigate(1,centerX,centerY)



				#listeOfCirles.append(center)

			#Find center of every circle found in last iteration
			#for index in range(len(listeOfCirles))

				#print c

			del listeOfCirles[:]

		cir.showCircles(frame)
		cir.showMask(mask)
		cir.showBitWiseRes(frame,mask)

	def showCircles(self, frame):
		self.frame = frame
		cv2.imshow('frame' , frame)
	
	def showBitWiseRes(self, frame, mask):
		self.frame = frame
		self.mask = mask
		
		#mask image and original image togethers
		res = cv2.bitwise_and(frame,frame, mask = mask)
		cv2.imshow('res', res)

	def showMask(self, mask):
		self.mask = mask
		cv2.imshow('mask', mask)


class Rectangles:
	def _init_(self):pass
	
	def lookForRect(self,frame):

		self.frame = frame
		
		
		medianblur = cv2.medianBlur(frame,5)
		#gaussianblur = cv2.GaussianBlur(medianblur,(7,7),0)

		lower_color = np.array([0,190,210])
		upper_color = np.array([99,231,252])

		mask = cv2.inRange(medianblur,lower_color,upper_color)

		edged = cv2.Canny(mask,150,300)
	#Find contours in the image and each relationship and the compress the result to save space
		(contours,_) = cv2.findContours(edged.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
	
	#sort out the 10 larges contours
		contours = sorted(contours, key = cv2.contourArea, reverse = True)[:1]


		if contours is not None:
			for c in contours:

				bx,by,bw,bh = cv2.boundingRect(c)
				if bx and by and bw and bh is not None:
					if bw>30 and bh>30:
						centerX =int(bx+(bw/2))
						centerY = int(by+(bh/2))

						cv2.rectangle(frame, (bx,by),(bx+bw,by+bh),(255,0,0),1)
						cv2.circle(frame,(centerX,centerY), 2, (0,0,255), 1)

						navigate(1,centerX,centerY)

				#Gjelder sirkler hvis ønskelig
				#(cx,cy),radius = cv2.minEnclosingCircle(c)
        	  # draw contours in green color
        		#cv2.circle(frame,(int(cx),int(cy)),int(radius),(0,0,255),2) 

				#peri = cv2.arcLength(c,True)
				#2% of precision
				#approx = cv2.approxPolyDP(c,0.0*peri,True) 

				#if len(approx) == 4:
				#	rectCnt = approx


				#	M = cv2.moments(c)
				#	if M['m00'] == 0.0:
				#		continue
				#	centerX = int(M['m10']/M['m00'])
				#	centerY = int(M['m01']/M['m00'])
				#	print centerX
				
				#	break

		rec.drawRectangles(frame)
		#rec.showMask(mask)
		rec.showEdge(edged)

	def drawRectangles(self,frame):
		self.frame = frame
		#cv2.drawContours(frame, [rectCnt], -1, (0,255,0),3)
		cv2.imshow('frame',frame)
	
	def showMask(self,mask):
		self.mask = mask
		cv2.imshow('mask', mask)

	def showEdge(self, edged):
		self.edged = edged
		cv2.imshow('edged', edged)



def navigate(number,centerX,centerY):
	number = number
	centerX = centerX
	centerY = centerY
	if number == 1:
		if centerX> 0 and centerX < (width/2) -20:
			print 'sving til venstre'
				
		if centerX > ((width/2) + 20) and centerX <= width:
			print 'Sving til høyre'
					
		if centerY > 0 and centerY < ((height/2) - 20):
			print 'kjør opp'
                    
        if centerY >((height/2) + 20) and centerY <= height:
           	print 'kjør lavere'


rec = Rectangles()
cir = Circles()

while(1):
	
	_, frame = cap.read()

	rec.lookForRect(frame)
	#cir.lookForCir(frame)

	k= cv2.waitKey(5)& 0xFF
	if k == 27:
		break

	#cv2.waitKey(1000)

cv2.destroyAllWindows()

#cv2.GaussoanBlur /otsu binarization
#cv2.Canny /fins the edges
#adaptiveThreshold
#medianBlur
#bilateral filering is slower but doesn't blur the image
