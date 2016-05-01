# import own file packages
import aprs
import JPEG
import ax25


# debugging
import pdb

class Receiver():
    def __init__(self, user, serial_number, gain=0.5):
        self.tnc = aprs.TNCaprs()
        self.s = utils.setup_serial(serial_number)
        self.dusb_in, self.dusb_out, self.din, self.dout = utils.get_dev_number(user)
        self.gain = gain

def main():
      pass

if __name__ == "__main__":
      main()

