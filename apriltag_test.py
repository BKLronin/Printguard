import machine
import os
import vl53l0x
import pyb
import struct
import utime, time
import math
import sensor, image
import micropython


sensor.reset()
sensor.set_contrast(3)
sensor.set_gainceiling(4)
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(False) #Doesnt work for Apriltag
#sensor.set_windowing((100, 100))
sensor.skip_frames(time = 500)
sensor.set_auto_gain(True)
sensor.set_auto_whitebal(False) # Turn off white balance.
clock = time.clock()



#extra_fb = sensor.alloc_extra_fb(sensor.width(), sensor.height(), sensor.GRAYSCALE)
start = time.clock()
#Initialize the TOF Sensor
i2c = machine.I2C(sda=pyb.Pin('P5'), scl=pyb.Pin('P4'), freq=400000)
tof = vl53l0x.VL53L0X(i2c)
tof.start()

kpts1 = None
MIN_TRIGGER_THRESHOLD = -0.5

def depthSense():
    #Get TOF Sensor distance and smooth it out
    dist = tof.read()
    avg = []
    if (len(avg) < 1):
        avg.append(dist)
    else:
       del avg[0]
    smooth = math.floor(sum(avg) / 3)

    return smooth

if not "temp" in os.listdir(): os.mkdir("temp") # Make a temp directory
print("About to save background image...")
sensor.skip_frames(time = 2000) # Give the user time to get ready.
sensor.snapshot().save("temp/bg.bmp")
print("Saved background image!")

img = sensor.snapshot()
if kpts1 == None:

    img.find_edges(image.EDGE_CANNY, threshold=(50, 80))
    kpts1 = img.find_keypoints(max_keypoints=150, threshold=10, scale_factor=1.2)
    print(kpts1)

while(True):

    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QQVGA)

    img = sensor.snapshot()

    thresholds = [(30, 100, 15, 127, 15, 127), # generic_red_thresholds
                  (30, 100, -64, -8, -32, 32), # generic_green_thresholds
                  ((0, 100, -128, 127, -127, 12))] # generic_blue_threshold

    f_x = (2.8 / 3.984) * 160 # find_apriltags defaults to this if not set
    f_y = (2.8 / 2.952) * 120 # find_apriltags defaults to this if not set
    c_x = 160 * 0.5 # find_apriltags defaults to this if not set (the image.w * 0.5)
    c_y = 120 * 0.5 # find_apriltags defaults to this if not set (the image.h * 0.5)

    for tag in img.find_apriltags(fx=f_x, fy=f_y, cx=c_x, cy=c_y): # defaults to TAG36H11
        #img.draw_rectangle(tag.rect(), color = (255, 0, 0))
        img.draw_cross(tag.cx(), tag.cy(), color = (0, 255, 0))

        if tag.cx() != None:

            thresholds = [(30, 100, 15, 127, 15, 127), # generic_red_thresholds
                          (30, 100, -64, -8, -32, 32), # generic_green_thresholds
                          ((0, 100, -128, 127, -127, 12))] # generic_blue_threshold

            f_x = (2.8 / 3.984) * 160 # find_apriltags defaults to this if not set
            f_y = (2.8 / 2.952) * 120 # find_apriltags defaults to this if not set
            c_x = 160 * 0.5 # find_apriltags defaults to this if not set (the image.w * 0.5)
            c_y = 120 * 0.5 # find_apriltags defaults to this if not set (the image.h * 0.5)

            scanFrameX = tag.cx()
            scanFrameY = tag.cy() -100
            #img.draw_rectangle(scanFrameX,-scanFrameY,100,70)
            print("Found Apriltag")

            sensor.set_pixformat(sensor.GRAYSCALE)
            sensor.set_framesize(sensor.QVGA)

            img= sensor.snapshot()
            sim = img.get_similarity("temp/bg.bmp")
            change = "Yes" if sim.min() < MIN_TRIGGER_THRESHOLD else "No"


            if change == "Yes" :
                print("Picture has changed")
                img.find_edges(image.EDGE_CANNY, threshold=(50, 80))
                kpts2 = img.find_keypoints(max_keypoints=150, threshold=10, normalized=True)
                match = image.match_descriptor(kpts1, kpts2, threshold=85)
                if (match.count()>10):
                    # If we have at least n "good matches"
                    # Draw bounding rectangle and cross.
                    img.draw_rectangle(match.rect())
                    img.draw_cross(match.cx(), match.cy(), size=10)

                print(kpts2, "matched:%d dt:%d"%(match.count(), match.theta()))

                # NOTE: uncomment if you want to draw the keypoints
                #img.draw_keypoints(kpts2, size=KEYPOINTS_SIZE, matched=True)
                for blob in img.find_blobs(thresholds, pixels_threshold=100, area_threshold=200, merge=False
                , roi = (scanFrameX-40,-scanFrameY,80,80)):

                    img.draw_rectangle(blob.rect())
                    img.draw_cross(blob.cx(), blob.cy())
                    dist = str(depthSense())
                    #print(dist)
                    img.draw_string(10,10, dist, 0)

            elif change == "No":
                print("No Print detected")




