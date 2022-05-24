import bencodepy
from socket import *
from bitarray import bitarray
import requests  # http requests
import hashlib  # SHA1 hashing for info hash
import binascii  # use unhexlify to convert ascii hex sequences into binary
import random  # create the local peer id
import math  # you'll need to use the ceil function in a few places
import sys
import re
import urllib
from utils.constants import *
from utils.torrentData import *
from utils.peerConnection import *
from utils.decode import *
  # An array of pieces (binary sequences)
class Run:
    def __init__(self):
        self.total_bytes_gotten = 0
        self.peer_id = "M0-0-1-" + "".join(random.sample(ALPHANUM, 13))
        self.peer_connections = []
        self.torrent_data = None
        self.file_array = b""
        self.done = False

    def get_block(self, peer, data, sock):
        self.total_bytes_gotten
        recv = sock.recv(4)
        len_block = data
        len_piece = int.from_bytes(recv, byteorder="big")
        lenblock = int.from_bytes(len_block, byteorder="big")
        recv = sock.recv(1)
        messid = int.from_bytes(recv, byteorder="big")
        if messid == 7:  # tmp, the message value is correct
            index = sock.recv(4)
            offset = sock.recv(4) #buffer
            block = b""
            while (
                len(block) < lenblock
            ):  # as long as the block is smaller than the expected block size
                data = sock.recv(1)
                block = block + data
                if len(block) == len_block:
                    break
            self.file_array += block
            self.total_bytes_gotten = len(block) + self.total_bytes_gotten
            print(
                "Got a block (size: {0})\tTotal so far: {1} out of {2}".format(
                    len(block), self.total_bytes_gotten, self.torrent_data.total_length
                )
            )
            if self.done == False:  # There's still pieces to be downloaded
                index = math.floor(self.total_bytes_gotten / self.torrent_data.piece_length)
                index = int(index)
                self.request_piece(peer, sock, index)
            else:
                output_filename = self.torrent_data.output_filename
                file_contents = self.file_array
                outfile = open(output_filename, "wb+")
                outfile.write(file_contents)
                print("Download complete. Wrote file to {0}".format(output_filename))
                self.done = True
                sys.exit(1)
    
    def request_piece(self, peer, sock, index):  # You'll need access to the socket,
        if index == 0:
            offset = self.total_bytes_gotten
        else:
            offset = (
                (self.total_bytes_gotten / req_block_size_int) % 2
            ) * req_block_size_int
            offset = int(offset)
        length_last_block = self.torrent_data.total_length - self.total_bytes_gotten
        if (
            index == self.torrent_data.no_of_pieces - 1
            and length_last_block < req_block_size_int
        ):
            length = self.torrent_data.total_length - self.total_bytes_gotten
            self.done = True
        else:
            length = req_block_size_int
        offset = offset.to_bytes(4, byteorder="big")
        length = length.to_bytes(4, byteorder="big")
        index = index.to_bytes(4, byteorder="big")
        start = b"\x00\x00\x00\r\x06"
        req = start + index + offset + length
        sock.send(req)
        self.get_block(peer, length, sock)

