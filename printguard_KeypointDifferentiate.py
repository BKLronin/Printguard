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
sensor.set_gainceiling(2)
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)

sensor.set_vflip(False) #Doesnt work for Apriltag
#sensor.set_windowing((100, 100))
sensor.skip_frames(time = 500)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False) # Turn off white balance.
clock = time.clock()



#extra_fb = sensor.alloc_extra_fb(sensor.width(), sensor.height(), sensor.GRAYSCALE)
start = time.clock()
#Initialize the TOF Sensor
i2c = machine.I2C(sda=pyb.Pin('P5'), scl=pyb.Pin('P4'), freq=400000)
tof = vl53l0x.VL53L0X(i2c)
tof.start()


MIN_TRIGGER_THRESHOLD =0.4

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

def blobscan(interest):
    #sensor.set_pixformat(sensor.RGB565)
    #sensor.skip_frames(time = 500)

    #print("Blobactive")

    thresholds = [(30, 100, 15, 127, 15, 127), # generic_red_thresholds
                  (30, 100, -64, -8, -32, 32), # generic_green_thresholds
                  ((0, 100, -128, 127, -127, 12))] # generic_blue_threshold

    x,y = interest
    for blob in img.find_blobs(thresholds, pixels_threshold=100, area_threshold=200, merge=False
    , roi = (x-80,y-80,160,160)):

        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        dist = str(depthSense())
        #print(dist)
        img.draw_string(10,10, dist, 0)
    sensor.set_pixformat(sensor.GRAYSCALE)


def aprilscan():
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QQVGA)
    img= sensor.snapshot()
    f_x = (2.8 / 3.984) * 160 # find_apriltags defaults to this if not set
    f_y = (2.8 / 2.952) * 120 # find_apriltags defaults to this if not set
    c_x = 160 * 0.5 # find_apriltags defaults to this if not set (the image.w * 0.5)
    c_y = 120 * 0.5 # find_apriltags defaults to this if not set (the image.h * 0.5)
    for tag in img.find_apriltags(fx=f_x, fy=f_y, cx=c_x, cy=c_y): # defaults to TAG36H11
        #img.draw_rectangle(tag.rect(), color = (255, 0, 0))
        img.draw_cross(tag.cx(), tag.cy(), color = (0, 255, 0))
        print("test")

        if tag.cx() != None:

            scanFrameX = tag.cx()
            scanFrameY = tag.cy() -100
            region = [scanFrameX, scnaFrameY]
            #img.draw_rectangle(scanFrameX,-scanFrameY,100,70)
            print("Found Apriltag")
        else:
            print("No Tag found")

        return region

def kpScan(img):
    kpts1 = None
    if kpts1 == None:
        #img.find_edges(image.EDGE_CANNY, threshold=(50, 80))
        kpts1 = img.find_keypoints(max_keypoints=30, threshold=12, scale_factor=1.2)


        return kpts1

def kpMatch(kpts1,kpts2):

    match = image.match_descriptor(kpts1, kpts2, threshold=85)
    if (match.count()>1):
        # If we have at least n "good matches"
        # Draw bounding rectangle and cross.

        #img.draw_rectangle(match.rect())
        img.draw_cross(match.cx(), match.cy(), size=10)
        mCount = match.count()

        return mCount


    print(kpts2, "matched:%d dt:%d"%(match.count(), match.theta()))

def printDetected():
    sim = img.get_similarity("temp/bg.bmp")
    #print(sim)
    change = "Yes" if sim.min() < MIN_TRIGGER_THRESHOLD else "No"

def transform(kpts, n):
    listlength = 10

    for i in range(0,29):
        x,y, *rest = kpts[i]
        while len(kpBook[n]) <100 and (x,y) not in kpBook[n]:
            kpBook[n].append((x,y))
            print("KPBook:",kpBook)

    return x,y

def kpScanObject():
    #sensor.set_pixformat(sensor.GRAYSCALE)
    #sensor.skip_frames(time = 500)
    kptsObj = kpScan(img)
    kptsObjXY = transform(kptsObj,'obj')

    #print("kptsObj XY pos",kptsObjXY)

    x,y = kptsObjXY
    if kptsObjXY not in kptsBG:
        img.draw_circle(x,y,20)
    else:
        img.draw_arrow(x,y,x+10,y+10)

    return x,y



if not "temp" in os.listdir(): os.mkdir("temp") # Make a temp directory
#Analyse Background
print("About to save background image...")
sensor.skip_frames(time = 2000) # Give the user time to get ready.
sensor.snapshot().save("temp/bg.bmp")
print("Saved background image!")

#"Database" init
kptsList1 = []
kptsList2 = []
kptsList3 = []
kpBook = {'bg': kptsList1, 'dyn': kptsList2, 'obj': kptsList3}

#Main Loop


img = sensor.snapshot()
kpts1 = kpScan(img)
kptsBG = transform(kpts1,'bg')
#print("background:",kptsBG)
img.draw_cross(kptsBG,(0,0,0))

#img.draw_keypoints(kpts1,(0,0,0))
while (True):
    sensor.set_pixformat(sensor.GRAYSCALE)
    sensor.skip_frames(time = 500)
    img = sensor.snapshot()
    sim = img.get_similarity("temp/bg.bmp")
    change = "Yes" if sim.stdev() > MIN_TRIGGER_THRESHOLD else "No"

    #print("kpts XY pos",kptsBG)

    if change == "Yes" :

        interest = kpScanObject()
        blobscan(interest)


#for m in match.match():
#print(kpts1[m[0]], kpts2[m[1]])

#The keypoint is a tuple of (x, y, score, octave, angle).




