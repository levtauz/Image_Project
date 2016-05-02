# own file packages
import aprs
import JPEG
import ax25
import utils
import test

import transmitter
import receiver

from scipy import misc
import matplotlib.pyplot as plt
import pyaudio
import sys
import threading, time
import Queue
import numpy as np
import serial
import bitarray

# debugging
import pdb

# command line parsing
import argparse

# Global variables
VIEW=False # toggle comparing old and new images

def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default=str) # for user setup configuration
    parser.add_argument("-f", default="images/createrLake.tiff") # image file
    parser.add_argument("-q", default=90, type=int) # image quality
    parser.add_argument("-s", default=-1, type=int) # serial number. default is -1 for MAC or COM4. can change if needed
    parser.add_argument("--test", default=-1, type=int) # test suites
    args = parser.parse_args()
    return args

def main():
    args = init_args()

    # unpack variables from args. allow flexible changes without using args
    user = args.user
    serial_number = args.s

    file_path = args.f
    jpeg_quality = args.q

    test_number = args.test
    if test_number != -1:
        test.run_tests(user, serial_number)
    else:
        # read in image
        image = misc.imread(file_path)
        # compress image and prepare for transmission
        data = JPEG.JPEG_compression(image, jpeg_quality)

        # Initiate a transmitter
        #t = transmitter.Transmitter(user, serial_number)

        # prepare data -> packets?
        #packet = test_sms()

        # transmit packets
        #t.transmit_packet(packet)

        #r = receiver.Receiver(user, serial_number)

        im = JPEG.JPEG_decompression(data, jpeg_quality, image.shape[0], image.shape[1])
        if VIEW:
            plt.figure()
            plt.subplot(1,2,1)
            plt.imshow(image)
            plt.subplot(1,2,2)
            plt.imshow(im)
            plt.show()


if __name__ == "__main__":
    main()
