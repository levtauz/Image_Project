#!/usr/bin/env python 
import transmitter
import receiver
import time
import ax25

import Queue
import pyaudio
import threading
import aprs
import utils

DEBUG=True

def test_image(user, serial_number):
    """
    loop back mode
    """
    # setup variables for tests
    callsign = "KK6MRI"
    fname = "calBlue.tiff"
    dir = "images/"
    f = open(dir + fname,"rb")

    fs = 48000
    Abuffer = 1024
    Nchunks = 12

    # prepare transmitter and receiver
    t = transmitter.Transmitter(user, serial_number, fs=fs, Abuffer=Abuffer, Nchunks=Nchunks)
    r = receiver.Receiver(user, serial_number, fs=fs, Abuffer=Abuffer, Nchunks=Nchunks)

    # prepare i/o queues
    Qin = Queue.Queue()
    Qout = Queue.Queue()

    # create a control fifo to kill threads when done
    cQin = Queue.Queue()
    cQout = Queue.Queue()

    # create a pyaudio object
    p = pyaudio.PyAudio()

    # initialize a recording thread. 
    t_rec = threading.Thread(target = aprs.record_audio, args = (Qin, cQin, p, fs, r.dusb_in))
    t_play = threading.Thread(target = aprs.play_audio, args = (Qout, cQout, p, fs, t.dusb_out))

    # generate packets and put into output queue
    Qout = t.generate_packets(Qout, callsign)

    # start the recording and playing threads
    t_rec.start()
    time.sleep(2)
    t_play.start()

    starttime = time.time()

    # process packets and put them into input queue
    r.process_packets(Qin, file_path)

    utils.print_msg(time.time() - starttime, DEBUG)
    cQout.put("EOT")
    cQin.put("EOT")
    t.terminate()
    r.terminate()


def test_sms(user, serial_number):
    utils.print_msg("Running SMS Test", DEBUG)
    t = transmitter.Transmitter(user, serial_number, baud=1200, space_f=2200)

    callsign = "KM6BHD"
    Digi =b'WIDE1-1,WIDE2-1'
    dest = "APCAL"

    # Uncomment to Send Email
    #info = ":EMAIL    :h.wang94@berkeley.edu Hi, test email!"

    # Uncomment to Send an SMS message to a phone number
    info = ":SMSGTE   :@4089312267 Hi. This is a test message text"

    #uncomment to show yourself on mt everest
    #info = "=2759.16N/08655.30E[I'm on the top of the world"

    #uncomment to send to everyone on the APRS system near you
    #info = ":ALL      : CQCQCQ I would like to talk to you!"

    #uncomment to report position
    #info = "=3752.50N/12215.43WlIm using a laptop in Cory Hall!"

    #uncomment to send a status message
    #info = ">I like radios"
    utils.print_msg("Preparing packet...", DEBUG)
    packet = ax25.UI(
            destination=dest,
            source=callsign,
            info=info,
            digipeaters=Digi.split(b','),
            )
    utils.print_msg("Transmitting packet...", DEBUG)
    t.transmit_packet(packet)
    time.sleep(2)
    utils.print_msg("Finished transmitting packet...", DEBUG)
    t.terminate()

def test_decode_iss_packet(user, serial_number):
    fs, sig = waveread("test_files/ISSpkt.wav")
    r = receiver.Receiver(user, serial_number, fs=fs)
    packets = r.parse_data(sig)
    decode_packets(packets)
    expected = 1
    utils.print_msg("Found {} packet. Expected {}".format(found, expected), DEBUG)
    r.terminate()

def test_decode_mult_iss_packets(user, serial_number):
    fs, sig = waveread("test_files/ISS.wav")
    r = receiver.Receiver(user, serial_number, fs=fs)
    packets = r.parse_data(sig)
    decode_packets(packets)
    found = len(filter(lambda ax: ax.info != 'bad packet', map(r.tnc.decodeAX25, filter(lambda pkt: len(pkt) > 200, packets))))
    expected = 24
    utils.print_msg("Found {} packet. Expected {}".format(found, expected), DEBUG)
    r.terminate()

def run_tests(user, serial_number):
    test_sms(user, serial_number)
    test_image(user, serial_number)
    test_decode_iss_packet(user, serial_number)
    test_decode_mult_iss_packets(user, serial_number)
