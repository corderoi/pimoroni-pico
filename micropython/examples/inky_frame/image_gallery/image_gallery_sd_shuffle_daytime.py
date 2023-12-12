"""
An image gallery that displays a random image from your SD card and updates
on a timer, shuffling through all images before repeating.

Gets the current time from the configured WLAN and only changes the image
during the daytime hours that you specify to save energy.

Copy images to the root of your SD card by plugging it into a computer.

If you want to use your own images they must be the screen dimensions
(or smaller) and saved as *non-progressive* jpgs.

Make sure to uncomment the correct size for your display!
"""

# from picographics import PicoGraphics, DISPLAY_INKY_FRAME as DISPLAY    # 5.7"
# from picographics import PicoGraphics, DISPLAY_INKY_FRAME_4 as DISPLAY  # 4.0"
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"
from machine import Pin, SPI
import inky_helper as ih
import gc
import time
import jpegdec
import sdcard
import os
import inky_frame
import random
import math

# how often to change image (in minutes)
UPDATE_INTERVAL = 60
WAKE_TIME_HR = 15
SLEEP_TIME_HR = 7

# A short delay to give USB chance to initialise
time.sleep(0.5)

# Turn any LEDs off that may still be on from last run.
ih.clear_button_leds()
ih.led_warn.off()

# Sync the Inky (always on) RTC to the Pico W so that "time.localtime()" works.
inky_frame.pcf_to_pico_rtc()

# set up the display
graphics = PicoGraphics(DISPLAY)

# set up the SD card
sd_spi = SPI(0, sck=Pin(18, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(16, Pin.OUT))
sd = sdcard.SDCard(sd_spi, Pin(22))
os.mount(sd, "/sd")

# Get some memory back, we really need it!
gc.collect()

# Create a new JPEG decoder for our PicoGraphics
j = jpegdec.JPEG(graphics)

def display_image(filename):

    # Open the JPEG file
    j.open_file(filename)

    # Decode the JPEG
    j.decode(0, 0, jpegdec.JPEG_SCALE_FULL)

    # Display the result
    graphics.update()


ih.led_warn.on()

# Get initial time
year, month, day, hour, minute, second, dow, _ = time.localtime()

# Get a list of files that are in the directory
files = os.listdir("/sd")
# remove files from the list that aren't .jpgs or .jpegs and are not hidden files
files = [f for f in files if (f.endswith(".jpg") or f.endswith(".jpeg")) and not f.startswith(".")]
# track last file opened
last_file = None

while True:
    # Get some memory back, we really need it!
    gc.collect()

    ih.led_warn.on()

    # pick a random file
    num_files = len(files)
    file_idx = random.randrange(num_files)
    file = files[file_idx]
    del files[file_idx]
    print(f"Picking {file_idx} of {num_files}")

    # Shuffle files if we've cycled through all of them
    if not files:
        # Get a list of files that are in the directory
        files = os.listdir("/sd")
        # remove files from the list that aren't .jpgs or .jpegs and are not hidden files
        files = [f for f in files if (f.endswith(".jpg") or f.endswith(".jpeg")) and not f.startswith(".")]

    # Open the file
    print(f"Displaying /sd/{file}")
    print(f"Last file {last_file}")
    # don't redraw if last_file = file
    if last_file != file:
        print("Display image " + "/sd/" + file)
        display_image("/sd/" + file)

    # Get current time
    print("Reading current time...")
    # Avoid running code unless we've been triggered by an event
    # Keeps this example from locking up Thonny when we want to tweak the code
    if inky_frame.woken_by_rtc() or inky_frame.woken_by_button():
        # Connect to the network and get the time if it's not set
        if year < 2023:
            connected = False

            print("Setting time from network...")
            t_start = time.time()
            try:
                from secrets import WIFI_SSID, WIFI_PASSWORD
                ih.network_connect(WIFI_SSID, WIFI_PASSWORD)
                connected = True
            except ImportError:
                print("Create secrets.py with your WiFi credentials")
            except RuntimeError:
                pass
            t_end = time.time()

            if connected:
                inky_frame.set_time()

                print(f"Connection took: {t_end-t_start}s")
                ih.stop_network_led()
            else:
                print("Failed to connect!")

        # Display the date and time
        year, month, day, hour, minute, second, dow, _ = time.localtime()

        print(year)
        print(month)
        print(day)
        print(hour)
        print(minute)
        print(second)
        print(dow)

    last_file = file
    ih.led_warn.off()

    # Sleep or wait for a bit
    sleep_time_min = UPDATE_INTERVAL - minute
    if SLEEP_TIME_HR <= hour < WAKE_TIME_HR - 1:
        deep_sleep_offset = int(math.fabs(WAKE_TIME_HR - hour)) - 1
        sleep_time_min += deep_sleep_offset * 60
    print(f"Sleeping for {sleep_time_min} minutes")
    inky_frame.sleep_for(sleep_time_min)


