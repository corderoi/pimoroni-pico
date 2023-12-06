"""
An offline image gallery that displays a random image from your SD card
and updates on a timer.

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

# how often to change image (in minutes)
UPDATE_INTERVAL = 60

# A short delay to give USB chance to initialise
time.sleep(0.5)

# Turn any LEDs off that may still be on from last run.
ih.clear_button_leds()
ih.led_warn.off()

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


def get_files():
    # Get a list of files that are in the directory
    filenames = os.listdir("/sd")
    # remove files from the list that aren't .jpgs or .jpegs and are not hidden files
    return [f for f in filenames if (f.endswith(".jpg") or f.endswith(".jpeg")) and not f.startswith(".")]

ih.led_warn.on()

files = get_files()
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
        files = get_files()

    # Open the file
    print(f"Displaying /sd/{file}")
    print(f"Last file {last_file}")
    # don't redraw if last_file = file
    if last_file != file:
        print("Display image " + "/sd/" + file)
        display_image("/sd/" + file)

    last_file = file
    ih.led_warn.off()

    # Sleep or wait for a bit
    print(f"Sleeping for {UPDATE_INTERVAL} minutes")
    inky_frame.sleep_for(UPDATE_INTERVAL)


