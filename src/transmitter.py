# import own file packages
import aprs
import utils

import bitarray
import pyaudio

import sys
if sys.version_info.major == 2:
    import Queue
    import ax25
else:
    import queue as Queue
    import ax25_3 as ax25

import time
import numpy as np

import threading
# debugging
import pdb

DEBUG=True

class Transmitter():
    def __init__(self, user, serial_number, gain=0.5, fs=48000.0, Abuffer=1024, Nchunks=43, baud=2400, mark_f=1200, space_f=2400):
        self.tnc = aprs.TNCaprs(fs, Abuffer, Nchunks, baud, mark_f, space_f)
        self.s = utils.setup_serial(serial_number)
        self.dusb_in, self.dusb_out, self.din, self.dout = utils.get_dev_numbers(user)
        self.gain = gain

    def packets_to_queue(self, file_path, callsign, Qout, bytes_read=256):
        f = open(file_path, 'rb')
        npp = 0
        while(1):
            bytes = f.read(bytes_read)
            tmp = self.tnc.modulatePacket(callsign, "", str(npp), bytes, preflags=10, postflags=10 )
            Qout.put(tmp)
            npp = npp+1
            if len(bytes) < bytes_read:
                break
        f.close()
        return Qout

    def generate_packets(self, Qout, callsign, file_path):
        utils.print_msg("Putting packets in Queue", DEBUG)

        Qout.put("KEYON")
        tmp = self.tnc.modulatePacket(callsign, "", "BEGIN", file_path , preflags=40, postflags=2 )
        Qout.put(tmp)

        Qout = self.packets_to_queue(file_path, callsign, Qout, 256)

        tmp = self.tnc.modulatePacket(callsign, "", "END", "This is the end of transmission", preflags=2, postflags=20)
        Qout.put(tmp)
        Qout.put("KEYOFF")
        Qout.put("EOT")

        utils.print_msg("Done generating packets. Generated {} packets".format(Qout.qsize()-3), DEBUG)
        return Qout

    def transmit_file(self, file_path, callsign="KM6BHD"):
        Qout = Queue.Queue()
        cQout = Queue.Queue()
        p = pyaudio.PyAudio()
        t_play = threading.Thread(target = aprs.play_audio , args=(Qout, cQout, p, self.tnc.fs, self.dusb_out, self.s))

        Qout = self.generate_packets(Qout, callsign, file_path)

        utils.print_msg("Playing packets", DEBUG)
        t_play.start()
        time.sleep(75)
        cQout.put("EOT")
        time.sleep(3)
        p.terminate()

        utils.print_msg("Terminating", DEBUG)

    def transmit_packet(self, packet):
        """
        sends message to radio to transmit
        """
        prefix = bitarray.bitarray(np.tile([0,1,1,1,1,1,1,0],(20,)).tolist())
        msg = self.tnc.modulate(self.tnc.NRZ2NRZI( prefix + packet.unparse() + prefix))
        p = pyaudio.PyAudio()

        Qout = Queue.Queue()
        ctrlQ = Queue.Queue()

        Qout.put("KEYON")
        Qout.put(msg*self.gain)
        Qout.put("KEYOFF")
        Qout.put("EOT")

        aprs.play_audio( Qout ,ctrlQ ,p, 48000 , self.dusb_out, self.s, keydelay=0.5)

        time.sleep(1)
        p.terminate()

    def terminate(self):
        """
        terminate whatever may still be open
        """
        self.s.close()
