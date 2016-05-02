import ax25
import bitarray

b = bitarray.bitarray([random.random() > .5 for _ in range(256*8)])
callsign = "KK6SRY"
Digi =b'WIDE1-1,WIDE2-1'
dest = "APCAL"
