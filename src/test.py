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

def test_image(user, serial_number):
    """
    loop back mode
    """
    cQout = Queue.Queue()
    Qout = Queue.Queue()

    callsign = "KK6MRI"
    fname = "calBlue.tiff"
    dir = "images/"
    f = open(dir + fname,"rb")

    fs = 48000
    Abuffer = 1024
    Nchunks = 12
    modem = transmitter.Transmitter(user, serial_number)

    Qin = Queue.Queue()
    Qout = Queue.Queue()

# create a control fifo to kill threads when done
    cQin = Queue.Queue()
    cQout = Queue.Queue()

    # create a pyaudio object
    p = pyaudio.PyAudio()

    # initialize a recording thread. 
    t_rec = threading.Thread(target = aprs.record_audio,   args = (Qin, cQin, p, fs, modem.dusb_in))
    t_play = threading.Thread(target = aprs.play_audio,   args = (Qout, cQout, p, fs, modem.dusb_out))

    print("Putting packets in Queue")

    npp = 0
    tmp = modem.tnc.modulatePacket(callsign, "", "BEGIN", fname , preflags=2, postflags=2 )
    Qout.put(tmp)
    while(1):
	bytes = f.read(256)
	tmp = modem.tnc.modulatePacket(callsign, "", str(npp), bytes, preflags=4, postflags=2 )
	Qout.put(tmp)
	npp = npp+1
	if len(bytes) < 256:
            break
    tmp = modem.tnc.modulatePacket(callsign, "", "END", "This is the end of transmission", preflags=2, postflags=2 )
    Qout.put(tmp)
    Qout.put("EOT")

    print("Done generating packets")


    # start the recording and playing threads
    t_rec.start()
    time.sleep(2)
    t_play.start()

    starttime = time.time()
    npack = 0
    state = 0
    while(1):
	tmp = Qin.get()
	Qout.put(tmp)
	packets  = modem.tnc.processBuffer(tmp)
	#print len(packets)
	for ax in packets:
            npack = npack + 1
            print((str(npack)+")",str(ax)))
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

    print(time.time() - starttime)
    cQout.put("EOT")
    cQin.put("EOT")
    f1.close()
    f.close()

def test_sms(user, serial_number):
    print "Running SMS Test"
    t = transmitter.Transmitter(user, serial_number)

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
    print "Preparing packet..."
    packet = ax25.UI(
            destination=dest,
            source=callsign,
            info=info,
            digipeaters=Digi.split(b','),
            )
    print "Transmitting packet..."
    t.transmit_packet(packet)
    time.sleep(2)
    print "Finished transmitting packet..."
    t.s.close()

def test_decode_iss_packet(user, serial_number):
    fs, sig = waveread("test_files/ISSpkt.wav")
    r = receiver.Receiver(user, serial_number, fs)
    packets = r.parse_data(sig)
    decode_packets(packets)
    expected = 1
    print "Found {} packet. Expected {}".format(found, expected)
    r.s.close()

def test_decode_mult_iss_packets(user, serial_number):
    fs, sig = waveread("test_files/ISS.wav")
    r = receiver.Receiver(user, serial_number, fs)
    packets = r.parse_data(sig)
    decode_packets(packets)
    found = len(filter(lambda ax: ax.info != 'bad packet', map(r.tnc.decodeAX25, filter(lambda pkt: len(pkt) > 200, packets))))
    expected = 24
    print "Found {} packet. Expected {}".format(found, expected)
    r.s.close()

def run_tests(user, serial_number):
    test_sms(user, serial_number)
