import numpy as np
import scipy as scp
from scipy import misc
import math
import numpy as np
from matplotlib import *
import matplotlib.pyplot as plt
from matplotlib.pyplot import *

from numpy import *

import pyaudio
import serial
import sys
import time

import gzip

import sys
import os

from bitarray import bitarray

import pdb

DEBUG=True

def psnr(im_truth, im_test, maxval=255.):
    """
    Staff PSNR function
    """
    mse = np.linalg.norm(im_truth.astype(np.float64) - im_test.astype(np.float64))**2 / np.prod(np.shape(im_truth))
    return 10 * np.log10(maxval ** 2 / mse)

def downsample(im, factor):
    return misc.imresize(im, (im.shape[0]/factor, im.shape[1]/factor))

def upsample(im, orig_size):
    return misc.imresize(im, orig_size)

def text2Morse(text, fc, fs, dt):
    CODE = {'A': '.-',     'B': '-...',   'C': '-.-.',
        'D': '-..',    'E': '.',      'F': '..-.',
        'G': '--.',    'H': '....',   'I': '..',
        'J': '.---',   'K': '-.-',    'L': '.-..',
        'M': '--',     'N': '-.',     'O': '---',
        'P': '.--.',   'Q': '--.-',   'R': '.-.',
        'S': '...',    'T': '-',      'U': '..-',
        'V': '...-',   'W': '.--',    'X': '-..-',
        'Y': '-.--',   'Z': '--..',
        '0': '-----',  '1': '.----',  '2': '..---',
        '3': '...--',  '4': '....-',  '5': '.....',
        '6': '-....',  '7': '--...',  '8': '---..',
        '9': '----.',

        ' ': ' ', "'": '.----.', '(': '-.--.-',  ')': '-.--.-',
        ',': '--..--', '-': '-....-', '.': '.-.-.-',
        '/': '-..-.',   ':': '---...', ';': '-.-.-.',
        '?': '..--..', '_': '..--.-'
        }

    Ndot= 1.0*fs*dt
    Ndah = 3*Ndot

    sdot = sin(2*pi*fc*r_[0.0:Ndot]/fs)
    sdah = sin(2*pi*fc*r_[0.0:Ndah]/fs)

    # convert to dit dah
    mrs = ""
    for char in text:
        mrs = mrs + CODE[char.upper()] + "*"

    sig = zeros(1)
    for char in mrs:
        if char == " ":
            sig = concatenate((sig,zeros(Ndot*7)))
        if char == "*":
            sig = concatenate((sig,zeros(Ndot*3)))
        if char == ".":
            sig = concatenate((sig,sdot,zeros(Ndot)))
        if char == "-":
            sig = concatenate((sig,sdah,zeros(Ndot)))
    return sig

def printDevNumbers(output):
    if output:
        p = pyaudio.PyAudio()
        N = p.get_device_count()
        for n in range(0,N):
            name = p.get_device_info_by_index(n).get('name')
            print_msg( "{} {}".format(n, name), DEBUG)
        p.terminate()

def get_dev_numbers(person, output=False):
    printDevNumbers(True)
    if person == "h": # personal setup for harrison
        dusb_in = 1
        dusb_out = 5
        din = 2
        dout = 4
    elif person == "l": # personal setup for lev. CHANGE
        dusb_in = 3
        dusb_out = 3
        din = 7
        dout = 4
    elif person == "s": # personal setup for shane. CHANGE
        dusb_in = 1
        dusb_out = 5
        din = 2
        dout = 4
    elif person == "lab": # for lab computers
        dusb_in = 1
        dusb_out = 3
        din = 0
        dout = 2
    return (dusb_in, dusb_out, din, dout)

def setup_serial(com_num):
    if com_num == -1:
        if sys.platform == 'darwin':  # Mac
            s = serial.Serial(port='/dev/tty.SLAB_USBtoUART')
        elif sys.platform == 'linux2':
            s = serial.Serial(port='/dev/ttyUSB0')
        else: # for windows
            s = serial.Serial(port='COM4')
    else:
        if sys.platform == 'linux2':
            s = serial.Serial(port='/dev/ttyUSB{0}').format(com_num)
        else:
            s = serial.Serial(port='COM{}'.format(com_num))
    s.setDTR(0)
    return s

############################
# helpful debugging tools
############################
# function to compute average power spectrum
def avgPS( x, N=256, fs=1):
    M = floor(len(x)/N)
    x_ = reshape(x[:M*N],(M,N)) * np.hamming(N)[None,:]
    X = np.fft.fftshift(np.fft.fft(x_,axis=1),axes=1)
    return r_[-N/2.0:N/2.0]/N*fs, mean(abs(X)**2,axis=0)


# Plot an image of the spectrogram y, with the axis labeled with time tl,
# and frequency fl
#
# t_range -- time axis label, nt samples
# f_range -- frequency axis label, nf samples
# y -- spectrogram, nf by nt array
# dbf -- Dynamic range of the spect

def sg_plot( t_range, f_range, y, dbf = 60, fig = None) :
    eps = 10.0**(-dbf/20.0)  # minimum signal

    # find maximum
    y_max = abs(y).max()

    # compute 20*log magnitude, scaled to the max
    y_log = 20.0 * np.log10( (abs( y ) / y_max)*(1-eps) + eps )

    # rescale image intensity to 256
    img = 256*(y_log + dbf)/dbf - 1

    fig=figure(figsize=(16,6))

    plt.imshow( np.flipud( 64.0*(y_log + dbf)/dbf ), extent= t_range  + f_range ,cmap=plt.cm.gray, aspect='auto')
    plt.xlabel('Time, s')
    plt.ylabel('Frequency, Hz')
    plt.tight_layout()

    return fig

def myspectrogram_hann_ovlp(x, m, fs, fc,dbf = 60):
    # Plot the spectrogram of x.
    # First take the original signal x and split it into blocks of length m
    # This corresponds to using a rectangular window %


    isreal_bool = isreal(x).all()

    # pad x up to a multiple of m 
    lx = len(x);
    nt = (lx + m - 1) // m
    x = append(x,zeros(-lx+nt*m))
    x = x.reshape((m/2,nt*2), order='F')
    x = concatenate((x,x),axis=0)
    x = x.reshape((m*nt*2,1),order='F')
    x = x[r_[m//2:len(x),ones(m//2)*(len(x)-1)].astype(int)].reshape((m,nt*2),order='F')


    xmw = x * hanning(m)[:,None];


    # frequency index
    t_range = [0.0, lx / fs]

    if isreal_bool:
        f_range = [ fc, fs / 2.0 + fc]
        xmf = np.fft.fft(xmw,len(xmw),axis=0)
        sg_plot(t_range, f_range, xmf[0:m/2,:],dbf=dbf)
        print_msg(1, DEBUG)
    else:
        f_range = [-fs / 2.0 + fc, fs / 2.0 + fc]
        xmf = np.fft.fftshift( np.fft.fft( xmw ,len(xmw),axis=0), axes=0 )
        sg_plot(t_range, f_range, xmf,dbf = dbf)

    return t_range, f_range, xmf

def print_msg(msg, debug=True):
    if debug:
        print(msg)

def decode_packets(packets):
    npack = 0
    for pkt in packets:
        npack += 1
        print (str(npack) + ") |DEST:" + pkt.destination[:-1].decode('ascii') + " |SRC:" + pkt.source + " |DIGI:" + pkt.digipeaters.decode('ascii') + " |", pkt.info, "|")


#####
#GZIP
#####

def file_to_bitarray(fname):
    """
    assume file is path to a file
    """
    ba = bitarray()
    with open(fname, 'rb') as f:
        ba.fromfile(f)
    return ba

def gzip_to_data(fname):
	"""
	assume file is int16 data
	"""
	with gzip.open(fname, 'rb') as f:
		data = f.read()
	return np.fromstring(data,dtype = np.int32)


def data_to_bitarray(data):
    """
    assume data is a string
    """
    ba = bitarray()
    ba.frombytes(data)
    return ba

def bitarray_to_data(bits):
    """
    assume bits contain int16 data
    """
    return np.fromstring(bits,dtype = np.int32)

def save_to_gzip(data,fname):
    """
    Saves data to a gzip file
    fname: name of gzip file, do not at gz to the end
    """
    with gzip.open(fname  + '.gz', 'wb',compresslevel = 9) as f:
        f.write(data.tobytes())

def get_file_size(fname):
    """
    Returns the file size in Bytes
    """
    return os.path.getsize(fname)
