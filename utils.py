import numpy as np
import scipy as scp
import math
import numpy as np

import pyaudio
import serial
import sys

def psnr(im_truth, im_test, maxval=255.):
    """
    Staff PSNR function
    """
    mse = np.linalg.norm(im_truth.astype(np.float64) - im_test.astype(np.float64))**2 / np.prod(np.shape(im_truth))
    return 10 * np.log10(maxval ** 2 / mse)

def printDevNumbers(output):
    if output:
        p = pyaudio.PyAudio()
        N = p.get_device_count()
        for n in range(0,N):
            name = p.get_device_info_by_index(n).get('name')
            print n, name
        p.terminate()

def get_dev_numbers(person, output=False):
    printDevNumbers(output)
    if person == "h": # personal setup for harrison
        dusb_in = 1
        dusb_out = 5
        din = 2
        dout = 4
    elif person == "l": # personal setup for lev. CHANGE
        dusb_in = 1
        dusb_out = 5
        din = 2
        dout = 4
    elif person == "s": # personal setup for shane. CHANGE
        dusb_in = 1
        dusb_out = 5
        din = 2
        dout = 4
    return (dusb_in, dusb_out, din, dout)

def setup_serial(com_num):
    if com_num == -1:
        if sys.platform == 'darwin':  # Mac
            s = serial.Serial(port='/dev/tty.SLAB_USBtoUART')
        else: # for windows
            s = serial.Serial(port='COM4')
    else:
        s = serial.Serial(port='COM{}'.format(com_num))

    s.setDTR(0)
    return s


