# Updated code at 11/27  10:27PM - Eli
# Got rid of comments, small formatting and spelling errors

import time
import os
import adafruit_mma8451  # Accelerometer
import adafruit_gps  # GPS
import adafruit_mprls  # Air pressure
import serial
import board
import busio
import csv
from picamera import PiCamera

i2c = busio.I2C(board, board.SCL, board.SDA)

# UART initialization for GPS sensor
# Change device address accordingly!
gps_uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(gps_uart, debug=False)

# UART initialization for Geiger counter to read the serial data
# Change device address accordingly!
geiger_uart = serial.Serial("/dev/ttyUSB1", baudrate=9600, timeout=10)

# Get bytes of data queued up
# since 'readline()' will wait for EOL (end of line) symbol "\n"
try:
    geiger_bytes = gps_uart.inWaiting()
except:
    print('Geiger counter bytes fail')

# Turn on the basic GGA and RMC info (what you typically want)
# - From Code example
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")

# Set update rate to once a second (1hz) which is what you typically want.
gps.send_command(b"PMTK220,1000")

# Optionally change the data rate from its default of 800hz:
# accelerometer.data_rate = adafruit_mma8451.DATARATE_800HZ  #  800Hz (default)
try:
    accelerometer = adafruit_mma8451.MMA8451(i2c)
except:
    accelerometer = None
    print("No connection with the accelerometer.")

try:
    pressure_sensor = adafruit_mprls.MPRLS(i2c, psi_min=0, psi_max=25)
except:
    pressure_sensor = None
    print("No connection with the pressure sensor.")

current_time = time.strftime("%H:%M:%S:%MS", time.localtime())

# Make sure this list matches the indexes of the data_list
# defined below
headers = [
    'Time',
    'Acceleration x',
    'Acceleration y',
    'Acceleration z',
    'Orientation',
    'Air Pressure (psi)',
    'Geiger counter stuff',
    'Longitude',
    'Latitude',
    'Altitude'
]

file = open(current_time + '.csv', 'a', newline='')
writer = csv.DictWriter(file, fieldnames=headers)
writer.writeheader()


# Yep!
# Now, the file will stay "open" until we close it.
# We can do that when we exit the while loop
# or when we try to switch files.
# If we want to switch files, we could just
# Rerun this program (start it over)

def take_picture(cur_time):
    camera = PiCamera()
    camera.capture(f'/home/pi/Desktop/image{cur_time}.jpg')


# for the camera
# iterates through 60 while loops (which take 1 second),
# then goes back to 0 and captures a pic.
second_count = 0
while True:

    # Try / except used so if any data is unavailable, program will still continue
    try:
        x, y, z = accelerometer.acceleration
    except:
        x, y, z = None, None, None
        print("Accelerometer is not giving acceleration.")

    try:
        orientation = accelerometer.acceleration
    except:
        orientation = None
        print("Accelerometer is not giving orientation.")

    try:
        pressure = pressure_sensor.pressure
    except:
        pressure = None
        print("Pressure sensor is not giving pressure.")

    # Depending on if this takes too long, find a way to run asynchronously
    gps.update()

    if not gps.has_fix:
        # Try again if we don't have a fix yet.
        print("Waiting for fix...")
        continue
        # We have a fix! (gps.has_fix is true)

    try:
        longitude = gps.longitude
    except:
        longitude = None
        print("Not getting longitude.")
    try:
        latitude = gps.latitude
    except:
        latitude = None
        print("Not getting latitude.")
    try:
        altitude = gps.altitude_m
    except:
        altitude = None
        print("Not getting altitude.")

    # If we need to add more data later,
    # we'll have to remember to make sure the
    # indexes of headers and the data variables list match up
    data_list = [
        current_time,
        x,
        y,
        z,
        orientation,
        pressure,
        geiger_bytes,
        longitude,
        latitude,
        altitude
    ]

    # Will need to see how well the geiger counter data gets represented in the file!

    sensor_data = dict(zip(headers, data_list))

    writer.writerow(sensor_data)

    # Flushing the file will put the values in the file 'real time' won't have any non-negligible time delays
    # with our data. "Note flush() does not necessarily write the file’s data to disk. Use flush() followed
    # by os.fsync() to ensure this behavior. " - Python Docs

    file.flush()
    os.fsync(file.fileno)
    file_size = os.path.getsize(file.name)
    time.sleep(1)  # collect data every second
    second_count += 1

    # Take photo every minute with Pi Camera
    if second_count == 60:
        take_picture(current_time)
        second_count = 0

