# import own file packages
import aprs
import JPEG
import ax25


# debugging
import pdb

class Receiver():
    def __init__(self, user, serial_number, fs=48000.0, gain=0.5):
        self.tnc = aprs.TNCaprs(fs)
        pdb.set_trace()
        self.s = utils.setup_serial(serial_number)
        self.dusb_in, self.dusb_out, self.din, self.dout = utils.get_dev_number(user)
        self.gain = gain

    def record(self, dev_num=-1):
        Q = Queue.queue()
        p = pyaudio.PyAudio()
        if dev_num == -1:
            dev_num = self.dusb_in
        record_audio(Q, p, self.fs, dev_num)
        # get recorded audio from queue
        sig = []
        for n in xrange(0, Q.qsize()):
            samples = Qin.get()
            sig.extend(samples)
        # clear queue
        with Q.mutex:
            Q.queue.clear()

        p.terminate()
        return sig

    def parse_data(self, data):
        NRZIa = self.tnc.demod(data)
        idx = PLL(NRZIa)
        bits_nrzi = bitarray.bitarray((NRZIa[idx] > 0).tolist())
        bits_nrz = self.tnc.NRZI2NRZ(bits_nrzi)
        packets = findPackets(bits_nrz)
        return packets

    def decode_packets(self, packets):
        npack = 0
        for pkt in packets:
            if len(pkt) > 200:
                ax = self.tnc.decodeAX25(pkt)
                # print ax.info
                if ax.info != 'bad packet':
                    npack += 1
                    print (str(npack) + ") |DEST:" + ax.destination[:-1] + " |SRC:" + ax.source + " |DIGI:" + ax.digipeaters + " |", ax.info, "|")


def main():
      pass

if __name__ == "__main__":
      main()

