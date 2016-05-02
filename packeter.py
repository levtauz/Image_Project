import ax25
import random
import bitarray

def bits_to_packets(bits):
    N = len(bits)
    n = N // 256
    for i in range(n):
        x = bits[i*256:(i+1)*256]

b = bitarray.bitarray([random.random() > .5 for _ in range(4096)])
print b.tobytes()
bits_to_packets(b)