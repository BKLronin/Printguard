import machine
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
sensor.set_windowing((320, 240))
sensor.skip_frames(time = 500)
sensor.set_auto_gain(False, value=100)
sensor.set_auto_whitebal(False) # Turn off white balance.
clock = time.clock()
extra_fb = sensor.alloc_extra_fb(sensor.width(), sensor.height(), sensor.GRAYSCALE)
illuminate = pyb.LED(4)
start = time.clock()
#Initialize the TOF Sensor
i2c = machine.I2C(sda=pyb.Pin('P5'), scl=pyb.Pin('P4'), freq=400000)
tof = vl53l0x.VL53L0X(i2c)
tof.start()

def background():
    print("About to save background image...")
    sensor.skip_frames(time = 2000) # Give the user time to get ready.
    extra_fb.replace(sensor.snapshot())

    print("Saved background image - Now frame differencing!")

def draw_keypoints(img, kpts):
    if kpts:
        print(kpts)
        img.draw_keypoints(kpts)
        img = sensor.snapshot()
        time.sleep(1000)

def drawHUD():
    distStr = str(depthSense()) + "mm"
    img.draw_string(250,200, distStr)
    img.draw_cross(160, 120, 30,30)

def depthSense():
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
    kpts1 = None
    TRIGGER_THRESHOLD = 5
    findDepthX = []
    findDepthY = []
    depthBars = []
    illuminate.off()

    img = sensor.snapshot()
    img.draw_string(30,50,"READY! No Target",255,2, monospace = True)
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
                        kpts2 = img.find_keypoints(max_keypoints=150, threshold=5, normalized=True)
                        if (kpts2):
                            match = image.match_descriptor(kpts1, kpts2, threshold=70)
                            if (match.count()>10):
                                # If we have at least n "good matches"
                                # Draw bounding rectangle and cross.
                                #img.draw_rectangle(match.rect())
                                #img.draw_cross(match.cx(), match.cy(), size=10)
                                print(kpts2, "matched:%d dt:%d"%(match.count(), match.theta()))
                            # NOTE: uncomment if you want to draw the keypoints
                            #img.draw_keypoints(kpts2, size=10, matched=True)
                            average = 20
                            posX = match.x()
                            posY = match.y()
                            #Die letzten 5 Werte anhängen
                            if (len(findDepthX) < 20 and posX > 0):
                                findDepthX.append(posX)
                            else:
                                if posX > 0:
                                    del findDepthX[0]

                            if (len(findDepthY) < average and posY > 0):
                                findDepthY.append(posY)
                            else:
                                if posY > 0:
                                    del findDepthY[0]

                            #Mittelwert aus 5 Werten
                            midX = math.floor(sum(findDepthX) / average)
                            midY = math.floor(sum(findDepthY) / average)
                            midAll = []
                            if (len(midAll) < average):
                                midAll.extend([midX, midY, depthSense()])
                                print(midAll)
                                midAllStr = str(midAll)
                                img.draw_string(midX,midY, midAllStr)
                                print(midAll)
                            else:
                                del midAll
                            #Draws a cross with the depthinforamtion
                            img.draw_cross(midX, midY, 255, size = 10)
                            #print("X:",findDepthX,"Y:" ,findDepthY)



                            drawHUD()
                            #print(micropython.mem_info())


