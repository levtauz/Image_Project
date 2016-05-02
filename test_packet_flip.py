import ax25, aprs
import bitarray
import random

info = ":SMSGTE   :@6508628379 Hi Shane, this is Shane. How's your day going?"
callsign = "KK6SRY"
Digi =b'WIDE1-1,WIDE2-1'
dest = "APCAL"

packet = ax25.UI(
    destination=dest,
    source=callsign,
    info=info,
    digipeaters=Digi.split(b','),
    )

p = packet.unparse()
flag = bitarray.bitarray([0,1,1,1,1,1,1,0])
p[:8] = bitarray.bitarray([0,1,1,1,1,1,0,0]) #modify last first flag
p[-8:0] = bitarray.bitarray([0,0,1,1,1,1,1,0]) #modity first last flag
p = flag + p + flag

a = aprs.TNCaprs()
ps = a.findPackets(p)
print len(ps), "packets found."
for packet in ps:
    print a.decodeAX25(packet)