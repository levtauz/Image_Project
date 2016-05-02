import ax25
import random
import bitarray

callsign = "KK6SRY"
Digi =b'WIDE1-1,WIDE2-1'
dest = "APCAL"

def bitarray_to_packets(bits, dest, callsign, Digi):
    N = len(bits)
    n = N // 256
    extra = N-n*256

    packets = []

    for i in range(n):
        x = bits[i*256:(i+1)*256]
        packet = ax25.UI(
            destination=dest,
            source=callsign,
            info=x.tobytes(),
            digipeaters=Digi.split(b','),
            )
        packets.append(packet)

    if extra != 0:
        x = bits[n*256:]
        x.extend([0]*(256-len(x))) #zero-append last extra packet
        packet = ax25.UI(
            destination=dest,
            source=callsign,
            info=x.tobytes(),
            digipeaters=Digi.split(b','),
            )
        packets.append(packet)

    return packets

b = bitarray.bitarray([random.random() > .5 for _ in range(4100)])
packs = bitarray_to_packets(b, dest, callsign, Digi)

for p in packs:
    print p.unparse()