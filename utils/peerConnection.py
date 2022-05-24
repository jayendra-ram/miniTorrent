imap kk mmap kk port bencodepy
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

from constants import *

class PeerConnection:
    """A class representing the connection to a peer"""

    def __init__(self, ip, port, pid, torrent_data):
        self.ip = ip
        self.port = port
        self.pid = pid
        self.have = bitarray()
        self.socket = None
        self.torrent_data = torrent_data

    def handshake(self, info_hash):
        pstrlen = 19

        bin_reserved = binascii.unhexlify(reserved_hex_ascii)
        byte_string = chr(pstrlen) + protocol_string  # +reserved_hex_ascii
        byte_string = str.encode(byte_string)
        byte_string = byte_string + bin_reserved + info_hash + str.encode(self.pid)
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.settimeout(10)
        print("Trying to connect to {0}:{1}".format(self.ip, self.port))
        try:
            self.socket.connect((self.ip, self.port))
            print("sending byte_string handshake...")
            self.socket.send(byte_string)



            resp_length = self.socket.recv(1)
            resp_length = int.from_bytes(resp_length, byteorder="big")
            return_protocol = self.socket.recv(resp_length)
            res_bytes = self.socket.recv(8)
            return_hash = self.socket.recv(20)
            resp_pid = self.socket.recv(20)


            return True

        except:
            print("[Errno 51]: Network is unreachable")
            print("No returned handshake from peer")
            return False

    def handle_messages(self):


        while True:
            data = self.socket.recv(4)


            size = int.from_bytes(data, byteorder="big")
            if size == 2:
                messid = self.socket.recv(1)
                messid = int.from_bytes(messid, byteorder="big")
                if messid == 5:  # tmp
                    print("Receiving bitfield")
                    bitlength = size - 1
                    self.have = bitarray(endian="big")
                    havebytes = self.socket.recv(bitlength)
                    self.have.frombytes(havebytes)
                    self.have = self.have[: self.torrent_data.no_of_pieces]
                    print("Peer have: {0}".format(self.have))
                    has_whole_file = all(self.have)
                    if has_whole_file == True:
                        print("Interested in peer {0}".format(self.ip))
                        self.socket.send(INTERESTED)
                    else:
                        pass

            elif size == 0:
                print("keep-alive")
                pass

            elif size == 1:
                messid = self.socket.recv(1)
                messid = int.from_bytes(messid, byteorder="big")
                if messid == 1:
                    print("Unchoked by peer {0}".format(self.ip))
                    return True

            elif size == 5:
                messid = self.socket.recv(1)
                messid = int.from_bytes(messid, byteorder="big")
                if messid == 4:
                    piece_index = self.socket.recv(4)
                    piece_index = int.from_bytes(piece_index, byteorder="big")

                    list_have_pieces.append(piece_index)
                    num_have_pieces = len(list_have_pieces)
                    if num_have_pieces == torrent_data.no_of_pieces:
                        print("Peer has all the pieces")
                        self.socket.send(INTERESTED)

            elif size == req_block_size_int or size == last_block_size_int + 9:
                messid = self.socket.recv(1)
                messid = int.from_bytes(messid, byteorder="big")


                pass

            if not data:
                break


