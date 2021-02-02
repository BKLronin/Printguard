from pyb import I2C
import adafruit_vl53l0x

i2c = I2C(2, I2C.MASTER)
i2c.init(I2C.MASTER, baudrate=400000) # init as a master
if i2c.is_ready :
    getAdress = i2c.scan()
    adress = getAdress[0]
    print(adress)
    write = i2c.mem_write('abc', adress, 2, timeout=1000)
    read = i2c.mem_read(3, adress, 2)
    data = bytearray(3)  # create a buffer
    i2c.recv(data, adress)  # receive 3 bytes, writing them into data

print(read)
print(write)
print(data)




