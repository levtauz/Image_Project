#!/usr/bin/env python 
import transmitter
import receiver
import time
import ax25

def test_sms(user, serial_number):
    print "Running SMS Test"
    t = transmitter.Transmitter(user, serial_number)

    callsign = "KM6BHD"
    Digi =b'WIDE1-1,WIDE2-1'
    dest = "APCAL"

    # Uncomment to Send Email
    #info = ":EMAIL    :h.wang94@berkeley.edu Hi, test email!"

    # Uncomment to Send an SMS message to a phone number
    info = ":SMSGTE   :@NUMBER Hi. This is a test message text"

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
