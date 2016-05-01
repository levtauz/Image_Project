# import own file packages
import aprs
import ax25
import utils

# debugging
import pdb

class Transmitter():
    def __init__(self, user, serial_number, gain=0.5):
        self.tnc = aprs.TNCaprs()
        self.s = utils.setup_serial(serial_number)
        self.dusb_in, self.dusb_out, self.din, self.dout = utils.get_dev_number(user)
        self.gain = gain

    def transmit_packet(self, packet):
        """
        sends message to radio to transmit
        """
        prefix = bitarray.bitarray(tile([0,1,1,1,1,1,1,0],(20,)).tolist())
        msg = tnc.modulate(self.tnc.NRZ2NRZI( prefix + packet.unparse() + prefix))
        p = pyaudio.PyAudio()

        Qout = Queue.Queue()
        ctrlQ = Queue.Queue()

        Qout.put("KEYON")
        Qout.put(msg*self.gain)
        Qout.put("KEYOFF")
        Qout.put("EOT")

        aprs.play_audio( Qout ,ctrlQ ,p, 48000 , dusb_out, s, keydelay=0.5)

        time.sleep(1)
        p.terminate()





def main():
      pass

if __name__ == "__main__":
      main()

