# own file packages
import aprs
import JPEG
import utils
import test

import transmitter
import receiver

from scipy import misc
import matplotlib.pyplot as plt
import pyaudio
import threading, time
import numpy as np
import serial
import bitarray
import scipy

import sys
if sys.version_info.major == 2:
    import Queue
    import ax25
else:
    import queue as Queue
    import ax25_3 as ax25


import sys
if sys.version_info.major == 2:
    import Queue
    import ax25
else:
    import queue as Queue
    import ax25_3 as ax25


# debugging
import pdb

# command line parsing
import argparse

# Global variables
VIEW=False # toggle comparing old and new images
DEBUG=True

fs = 48000
callsign = "KM6BHD"

def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default=str) # for user setup configuration
    parser.add_argument("--type", default=str) # receiver or transmitter
    parser.add_argument("-f", default="images/createrLake.tiff") # image file
    parser.add_argument("-q", default=90, type=int) # image quality
    parser.add_argument("-d", type=int) # downsample
    parser.add_argument("-s", default=-1, type=int) # serial number. default is -1 for MAC or COM4. can change if needed
    parser.add_argument("--test", default=-1, type=int) # test suites
    args = parser.parse_args()
    return args

def transmitter_main(user, serial_number, file_path, jpeg_quality, downsample):
    jpeg_quality = int(jpeg_quality)
    downsample = int(downsample)
    image = misc.imread(file_path)
    data = JPEG.JPEG_compression(image, jpeg_quality, downsample)
    utils.save_to_gzip(data, file_path)
    t = transmitter.Transmitter(user, serial_number, baud=1200, space_f=2200)
    t.transmit_file(file_path + ".gz", callsign)

def receiver_main(user, serial_number, file_path):
    r = receiver.Receiver(user, serial_number, baud=1200, mark_f=1200, space_f=2200)
    r.record(file_path)
    data = utils.gzip_to_data(file_path + ".gz")
    im = JPEG.JPEG_decompression(data)
    misc.imsave(file_path + "_dc.tiff", im)

def main():
    args = init_args()

    # unpack variables from args. allow flexible changes without using args
    user = args.user
    serial_number = args.s

    file_path = args.f
    jpeg_quality = args.q
    downsample = args.d

    test_number = args.test

    type = args.type

    if test_number != -1:
        test.run_tests(user, serial_number)
    else:
        if args.type == "r": # receiver
            utils.print_msg("Receiver!", DEBUG)
            receiver_main(user, serial_number, file_path)
        if args.type == "t": # transmitter
            utils.print_msg("Transmitter!", DEBUG)
            transmitter_main(user, serial_number, file_path, jpeg_quality, downsample)


        #test.test_image(user, serial_number)
        #transmitter_main(user, serial_number, file_path)
        #receiver_main(user, serial_number, file_path)

        # read in image
        #image = misc.imread(file_path)
        # compress image and prepare for transmission
        #data = JPEG.JPEG_compression(image, jpeg_quality)

        # Initiate a transmitter
        #t = transmitter.Transmitter(user, serial_number)

        # prepare data -> packets?
        #packet = test_sms()

        # transmit packets
        #t.transmit_packet(packet)

        #r = receiver.Receiver(user, serial_number,)

        #im = JPEG.JPEG_decompression(data, jpeg_quality, image.shape[0], image.shape[1])
    #    if VIEW:
            #plt.figure()
            #plt.subplot(1,2,1)
            #plt.imshow(image)
            #plt.subplot(1,2,2)
            #plt.imshow(im)
            #plt.show()


if __name__ == "__main__":
    main()
