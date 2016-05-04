# import own file packages
import aprs
import JPEG
import threading
import pyaudio
import time

import utils

import sys
if sys.version_info.major == 2:
    import Queue
    import ax25
else:
    import queue as Queue
    import ax25_3 as ax25


# debugging
import pdb

DEBUG=True

class Receiver():
    def __init__(self, user, serial_number, gain=0.5, fs=48000.0, Abuffer=1024, Nchunks=43, baud=2400, mark_f=1200, space_f=2400):
        self.tnc = aprs.TNCaprs(fs, Abuffer, Nchunks, baud, mark_f, space_f)
        self.s = utils.setup_serial(serial_number)
        self.dusb_in, self.dusb_out, self.din, self.dout = utils.get_dev_numbers(user)
        self.gain = gain

    def process_packets(self, Q, file_path):
        npack = 0
        state = 0
        n = 0
        samples = []
        start = time.time()
        while(1):
            tmp = Q.get()
            samples.append(tmp)
            #utils.print_msg(n, DEBUG)
            packets = self.tnc.processBuffer(tmp)
            self.decode_packets(packets)
            for ax in packets:
                npack = npack+1
                utils.print_msg("Number of Packets: " + str(npack), DEBUG)
                #utils.print_msg((str(npack) +")", str(ax)), DEBUG)
                if state == 0 and ax.destination[:5]==b"BEGIN":
                    #f1 = open(dir + "rec_"+ax.info,"wb")
                    start = time.time()
                    f1 = open(file_path + ".gz", "wb")
                    state = 1
                elif state == 1 and ax.destination[:3] == b"END":
                    state = 2
                    f1.close()
                    break
                elif state == 1:
                    f1.write(ax.info)
                    #print("write")
            if state == 2 :
                break
            n+=1
            #if (time.time() - start > 75):
                #break
        print("Elapsed Time : " + str(time.time() - start))
        return samples

    def record(self, file_path, dev_num=-1):
        Q = Queue.Queue()
        cQ = Queue.Queue()
        p = pyaudio.PyAudio()
        if dev_num == -1:
            dev_num = self.dusb_in
        t_rec = threading.Thread(target=aprs.record_audio, args=(Q, cQ, p, self.tnc.fs, dev_num))
        t_rec.start()
        time.sleep(2)
        utils.print_msg("Processing packets", DEBUG)

        samples = self.process_packets(Q, file_path)

        time.sleep(3)
        cQ.put("EOT")
        time.sleep(3)
        p.terminate()
        return samples
        # get recorded audio from queue
        #sig = []
        #for n in xrange(0, Q.qsize()):
            #samples = Qin.get()
            #sig.extend(samples)
        ## clear queue
        #with Q.mutex:
            #Q.queue.clear()

        #p.terminate()
        #return sig

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
            npack += 1
            print (str(npack) + ") |DEST:" + pkt.destination[:-1].decode('ascii') + " |SRC:" + pkt.source + " |DIGI:" + pkt.digipeaters.decode('ascii') + " |", pkt.info, "|")

    def terminate(self):
        """
        terminate whatever may be still open
        """
        self.s.close()

def main():
    r = Receiver()


if __name__ == "main":
    main()
