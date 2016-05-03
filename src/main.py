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

def transmitter_main(user, serial_number, fname):
    callsign = "KM6BHD"
    fs = 48000
    t = transmitter.Transmitter(user, serial_number)
    Qout = Queue.Queue()
    cQout = Queue.Queue()
    p = pyaudio.PyAudio()
    t_play = threading.Thread(target = aprs.play_audio, args = (Qout, cQout, p, fs, t.dusb_out, t.s))

    f = open(fname, 'rb')

    print "Putting packets in Queue"

    npp = 0

    Qout.put("KEYON")
    tmp = t.tnc.modulatePacket(callsign, "", "BEGIN", fname , preflags=20, postflags=2 )
    Qout.put(tmp)
    while(1):
	bytes = f.read(256)
	tmp = t.tnc.modulatePacket(callsign, "", str(npp), bytes, preflags=4, postflags=2 )
	Qout.put(tmp)
	npp = npp+1
        if npp > 5:
            break
	if len(bytes) < 256:
            break
    tmp = t.tnc.modulatePacket(callsign, "", "END", "This is the end of transmission", preflags=2, postflags=20)
    Qout.put(tmp)
    Qout.put("KEYOFF")
    Qout.put("EOT")

    print "Done generating packets. Generated {} packets".format(npp)
    #aprs.play_audio(Qout, cQout, p, fs, t.dusb_out, t.s, keydelay=0.5)
    print "Playing packets"
    t_play.start()
    time.sleep(75)
    cQout.put("EOT")
    time.sleep(1)
    print "Finished playing packets"
    p.terminate()
    f.close()

def receiver_main(user, serial_number, fname):
    fs = 48000
    cQin = Queue.Queue()
    Qin = Queue.Queue()
    p = pyaudio.PyAudio()
    t_rec = threading.Thread(target=aprs.record_audio, args=(Qin, cQin, p, fs, t.dusb_in))
    t_rec.start()
    time.sleep(2)
    while(1):
        tmp = Qin.get()
        packets = t.tnc.processBuffer(tmp)
        for ax in packets:
            npack = npack+1
            print ((str(npack) +")", str(ax)))
            if state == 0 and ax.destination[:5]=="BEGIN":
                f1 = open(dir + "rec_"+ax.info,"wb")
                state = 1
            elif state == 1 and ax.destination[:3] == "END":
                state = 2
                break
            elif state == 1:
                f1.write(ax.info)
                print("write")
        if state == 2 :
            break

    time.sleep(75)
    cQin.put("EOT")
    p.terminate()
    f1.close()

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
        #test.test_image(user, serial_number)
        transmitter_main(user, serial_number, file_path)
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

        r = receiver.Receiver(user, serial_number, file_path)

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
