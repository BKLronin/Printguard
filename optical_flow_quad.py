# Optical Flow Example
#
# Your OpenMV Cam can use optical flow to determine the displacement between
# two images. This allows your OpenMV Cam to track movement like how your laser
# mouse tracks movement. By tacking the difference between successive images
# you can determine instaneous displacement with your OpenMV Cam too!
import sensor, image, time, os
import pyb, network, usocket, sys

SSID='mux'              # Network SSID
KEY='VkMspH%E\iYVax7'   # Network key
HOST = ''   # Use first available interface
PORT = 8080 # Arbitrary non-privileged port

sensor.reset() # Initialize the camera sensor.
sensor.set_contrast(3)
sensor.set_brightness(3)
sensor.set_saturation(1)
sensor.set_gainceiling(16)
sensor.set_framesize(sensor.B64x64) # or B40x30 or B64x64
sensor.set_pixformat(sensor.GRAYSCALE)


green_led = pyb.LED(2) # Red LED = 1, Green LED = 2, Blue LED = 3, IR LEDs = 4.
blue_led = pyb.LED(3) # Red LED = 1, Green LED = 2, Blue LED = 3, IR LEDs = 4.

# Init wlan module and connect to network
print("Trying to connect... (may take a while)...")
wlan = network.WINC()
wlan.connect(SSID, key=KEY, security=wlan.WPA_PSK)

# We should have a valid IP now via DHCP
print(wlan.ifconfig())

# Create server socket
s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)

# Bind and listen
s.bind([HOST, PORT])
s.listen(5)

# Set timeout to 1s
s.settimeout(0)

def start_streaming(s):
    green_led.on()
    print ('Waiting for connections..')
    client, addr = s.accept()
    print ('Connected to ' + addr[0] + ':' + str(addr[1]))
    green_led.off()

    # FPS clock
    clock = time.clock()

    # NOTE: The find_displacement function works by taking the 2D FFTs of the old
    # and new images and compares them using phase correlation. Your OpenMV Cam
    # only has enough memory to work on two 64x64 FFTs (or 128x32, 32x128, or etc).
    old = sensor.snapshot()

    while (True):
        clock.tick() # Track elapsed milliseconds between snapshots().
        img = sensor.snapshot() # Take a picture and return the image.

        [delta_x, delta_y, response] = old.find_displacement(img)

        old = img.copy()
        client.send("%0.1f,%0.1f,%0.2f" %(delta_x, delta_y, response))
        blue_led.toggle()

while (True):
    try:
        start_streaming(s)
    except OSError as e:
        print("socket error: ", e)
        #sys.print_exception(e)
