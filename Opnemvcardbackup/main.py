import machine
import vl53l0x
import pyb
import struct
import utime, time
import math
import sensor, image
import micropython


sensor.reset()
sensor.set_contrast(-3)
sensor.set_gainceiling(8)
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((320, 240))
sensor.skip_frames(time = 500)
#sensor.set_auto_gain(False, value=50)
sensor.set_auto_whitebal(False) # Turn off white balance.
clock = time.clock()
#Create extra frame buffer for comparison
extra_fb = sensor.alloc_extra_fb(sensor.width(), sensor.height(), sensor.GRAYSCALE)
illuminate = pyb.LED(4)
start = time.clock()
#Initialize the TOF Sensor
i2c = machine.I2C(sda=pyb.Pin('P5'), scl=pyb.Pin('P4'), freq=400000)
tof = vl53l0x.VL53L0X(i2c)
tof.start()

def background():
    #Get background image to differenciate
    print("About to save background image...")
    sensor.skip_frames(time = 500) # Give the user time to get ready.
    extra_fb.replace(sensor.snapshot())

    print("Saved background image - Now frame differencing!")

def draw_keypoints(img, kpts):
    if kpts:
        #print(kpts)
        img.draw_keypoints(kpts)
        img = sensor.snapshot()
        time.sleep(1000)

def drawHUD():
    distStr = str(depthSense()) + "mm"
    img.draw_string(250,200, distStr)
    img.draw_circle(160, 110, 40,255)

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

background()
while (True):
    #parameter and global dicts
    kpts1 = None
    TRIGGER_THRESHOLD = 5
    findDepthX = []
    findDepthY = []
    depthBars = []
    illuminate.off()
    img = sensor.snapshot()
    drawHUD()
    img.draw_string(30,50,"READY! No Target",255,2, monospace = True)
    #Main loop, as long there is something in the range of the sensor try to track
    while(depthSense() in range(50,300)):
                    illuminate.on()
                    img = sensor.snapshot()

                    img.difference(extra_fb)
                    hist = img.get_histogram()
                    # This code below works by comparing the 99th percentile value (e.g. the
                    # non-outlier max value against the 90th percentile value (e.g. a non-max
                    # value. The difference between the two values will grow as the difference
                    # image seems more pixels change.
                    diff = hist.get_percentile(0.99).l_value() - hist.get_percentile(0.90).l_value()
                    triggered = diff > TRIGGER_THRESHOLD

                    if (kpts1 == None):
                        # NOTE: By default find_keypoints returns multi-scale keypoints extracted from an image pyramid.
                        kpts1 = img.find_keypoints(max_keypoints=150, threshold=5, scale_factor=1.2)
                        draw_keypoints(img, kpts1)
                    else:

                        # NOTE: When extracting keypoints to match the first descriptor, we use normalized=True to extract
                        # keypoints from the first scale only, which will match one of the scales in the first descriptor.
                        kpts2 = img.find_keypoints(max_keypoints=150, threshold=5, normalized=True, corner_detector=image.CORNER_AGAST)
                        if (kpts2):
                            match = image.match_descriptor(kpts1, kpts2, threshold=80, filter_outliers = True)
                            if (match.count()>10):
                                # If we have at least n "good matches"
                                # Draw bounding rectangle and cross.
                                img.draw_rectangle(match.rect())
                                img.draw_cross(match.cx(), match.cy(), size=10)
                                #print(kpts2, "matched:%d dt:%d"%(match.count(), match.theta()))
                            # NOTE: uncomment if you want to draw the keypoints
                            img.draw_keypoints(kpts2, size=5, matched=True, fill=True)
                            average = 10
                            #print(kpts2)
                            posX = match.cx()
                            posY = match.cy()
                            #print(posX, posY)
                            #Attach the last 10(average) values into the dictionary for smoothing
                            findDepthX.append(posX)
                            if (len(findDepthX) > average):
                                del findDepthX[0]
#
                            findDepthY.append(posY)
                            if (len(findDepthY) > average):
                                del findDepthY[0]
                            #print(findDepthX, findDepthY)
                            #Sum the values for X,Y in the dictionary and divide by count

                            midX = int(sum(findDepthX) / average)
                            midY = int(sum(findDepthY) / average)
                            midAll = []
                            if (len(midAll) < average)and posX != 0 and posY != 0 :
                                midAll.extend([midX, midY, depthSense()])
                                #print(midAll)
                                midAllStr = str(midAll)
                                img.draw_string(midX,midY, midAllStr)

                            else:
                                del midAll
                            #Draws a cross with the depthinforamtion
                            img.draw_cross(midX, midY, 255, size = 10)
                            #print("X:",findDepthX,"Y:" ,findDepthY)
                            drawHUD()



