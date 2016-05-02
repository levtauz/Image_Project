import ax25
import random
import bitarray

callsign = "KK6SRY"
Digi =b'WIDE1-1,WIDE2-1'
dest = "APCAL"

def bitarray_to_packets(bits, dest, callsign, Digi):
    len_payload = 256*8
    N = len(bits)
    n = N // (len_payload)
    extra = N-n*len_payload

    packets = []

    for i in range(n):
        x = bits[i*len_payload:(i+1)*len_payload]
        packet = ax25.UI(
            destination=dest,
            source=callsign,
            info=x.tobytes(),
            digipeaters=Digi.split(b','),
            )
        packets.append(packet)

    if extra != 0:
        x = bits[n*len_payload:]
        x.extend([0]*(len_payload-len(x))) #zero-append last extra packet
        packet = ax25.UI(
            destination=dest,
            source=callsign,
            info=x.tobytes(),
            digipeaters=Digi.split(b','),
            )
        packets.append(packet)

    return packets

L = 256*8*3+256*4
b = bitarray.bitarray([random.random() > .5 for _ in range(L)])
packs = bitarray_to_packets(b, dest, callsign, Digi)

print L
print "no. of packets:", len(packs)
for p in packs:
    print len(p.unparse())
    print "unstuffed length:", len(ax25.bit_unstuff(p.unparse()))

