# own file packages
import aprs
import JPEG
import ax25

from scipy import misc
import matplotlib.pyplot as plt
import pyaudio
import sys
import threading, time
import Queue
import numpy as np
import serial
import bitarray

from numpy import pi
from numpy import sin
from numpy import cos
from numpy import zeros
from numpy import r_
from scipy import signal
from scipy import integrate

from numpy import ones
from numpy import floor
from numpy import round
from numpy import zeros
from numpy import sin
from numpy import log
from numpy import exp
from numpy import sign
from numpy import nonzero
from numpy import angle
from numpy import conj
from numpy import concatenate

from numpy import mean
from numpy import power
from numpy.fft import fft
from numpy.fft import fftshift
from numpy.fft import ifft
from numpy.fft import ifftshift
from  scipy.io.wavfile import read as wavread
from numpy import tile

# debugging
import pdb

def setup_device_numbers():
    p = pyaudio.PyAudio()
    N = p.get_device_count()
    for n in range(0,N):
        name = p.get_device_info_by_index(n).get('name')
        print n, name
    #printDevNumbers(p)
    p.terminate()

    dusb_in = 1
    dusb_out = 5
    din = 2
    dout = 4
    return (dusb_in, dusb_out, din, dout)
    
def setup_serial(com_num=5):
    if sys.platform == 'darwin':  # Mac
        s = serial.Serial(port='/dev/tty.SLAB_USBtoUART')
    else: # for windows
        s = serial.Serial(port='COM{}'.format(com_num))

#    s.setDTR(1)
    #time.sleep(1)
    s.setDTR(0)
    return s

def test_sms():
    callsign = "KM6BHD"
    Digi =b'WIDE1-1,WIDE2-1'
    dest = "APCAL"

    # Uncomment to Send Email
    #info = ":EMAIL    :h.wang94@berkeley.edu Hi, its YOURNAME, what a great lab!"

    # Uncomment to Send an SMS message to a phone number (update the number!)
    info = ":SMSGTE   :@4089312267 This is a new message! 2"
    #uncomment to show yourself on mt everest
    #info = "=2759.16N/08655.30E[I'm on the top of the world"

    #uncomment to send to everyone on the APRS system near you
    #info = ":ALL      : CQCQCQ I would like to talk to you!"


    #uncomment to report position
    #info = "=3752.50N/12215.43WlIm using a laptop in Cory Hall!"

    #uncomment to send a status message
    #info = ">I like radios"


    packet = ax25.UI(
            destination=dest,
            source=callsign, 
            info=info,
            digipeaters=Digi.split(b','),
            )
    #print(packet.unparse())
    return packet


def main():
    #image = misc.imread('images/createrLake.tiff')
    #quality = 90
    #data = JPEG.JPEG_compression(image, quality)

    dusb_in, dusb_out, din, dout = setup_device_numbers()
    com_num = 5
    s = setup_serial(com_num)

    tnc = aprs.TNCaprs() # inititiate a terminal-node-controller

    packet = test_sms()
    prefix = bitarray.bitarray(tile([0,1,1,1,1,1,1,0],(20,)).tolist())
    msg = tnc.modulate(tnc.NRZ2NRZI( prefix + packet.unparse() + prefix))
    p = pyaudio.PyAudio()

    Qout = Queue.Queue()
    ctrlQ = Queue.Queue()

    Qout.put("KEYON")
    Qout.put(msg*0.5)  # pick the gain that you calibrated in lab 5 part I
    Qout.put("KEYOFF")
    Qout.put("EOT")

    aprs.play_audio( Qout ,ctrlQ ,p, 48000 , dusb_out, s, keydelay=0.5)

    time.sleep(1)
    p.terminate()


    #im = JPEG.JPEG_decompression(data, quality, image.shape[0], image.shape[1])


main()
