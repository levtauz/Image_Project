# import own file packages
import aprs
import ax25
import utils

import bitarray
import pyaudio
import Queue
import time
import numpy as np

# debugging
import pdb

class Transmitter():
    def __init__(self, user, serial_number, gain=0.5, fs=48000.0, Abuffer=1024, Nchunks=43, baud=1200):
        self.tnc = aprs.TNCaprs(fs, Abuffer, Nchunks, baud)
        self.s = utils.setup_serial(serial_number)
        self.dusb_in, self.dusb_out, self.din, self.dout = utils.get_dev_numbers(user)
        self.gain = gain

    def transmit_file(self, file_path):
        Qout = Queue.Queue()
        cQout = Queue.Queue()
        p = pyaudio.PyAudio()
        t_play = threading.Thread(target = aprs.play_audio , args=(Qout, cQout, p, self.tnc.fs, self.dusb_out, self.s))

        f = open(fname, 'rb')

        print "Putting packets in Queue"
        npp = 0
        Qout.put("KEYON")
        tmp = self.tnc.modulatePacket(callsign, "", "BEGIN", fname , preflags=20, postflags=2 )
        Qout.put(tmp)
        while(1):
            bytes = f.read(256)
            tmp = self.tnc.modulatePacket(callsign, "", str(npp), bytes, preflags=4, postflags=2 )
            Qout.put(tmp)
            npp = npp+1
            if npp > 5:
                break
            if len(bytes) < 256:
                break
        tmp = self.tnc.modulatePacket(callsign, "", "END", "This is the end of transmission", preflags=2, postflags=20)
        Qout.put(tmp)
        Qout.put("KEYOFF")
        Qout.put("EOT")

        print "Done generating packets. Generated {} packets".format(npp)
        print "Playing packets"
        t_play.start()
        time.sleep(75)
        cQout.put("EOT")
        time.sleep(1)
        p.terminate()
        f.close()

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


def main():
      pass

if __name__ == "__main__":
      main()

