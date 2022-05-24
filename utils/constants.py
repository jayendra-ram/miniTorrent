from string import ascii_letters, digits
import random

ALPHANUM = ascii_letters + digits
INTERESTED = b"\x00\x00\x00\x01\x02"
CHOKE = b"\x00\x00\x00\x01\x00"
UNCHOKE = b"\x00\x00\x00\x01\x01"
NOT_INTERESTED = b"\x00\x00\x00\x01\x03"
KEEP_ALIVE = b"\x00\x00\x00\x00"
reserved_hex_ascii = "0000000000000000"  # The reserved sequence for your handshake
protocol_string = "BitTorrent protocol"
req_block_size_int = 16384  # Recommended size for requesting blocks of data
req_block_size_hex = int(req_block_size_int).to_bytes(4, byteorder="big", signed=True)
peer_id = "M0-0-1-" + "".join(random.sample(ALPHANUM, 13))
local_port          = 62690
newline = "\n"


