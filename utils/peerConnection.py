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

#local imports
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
        # Declare any necessary globals here
        # Your handshake message will be a bytes sequence
        # <pstrlen><pstr><reserved><info_hash><peer_id>
        # https://wiki.theory.org/BitTorrentSpecification#Handshake
        # http://bittorrent.org/beps/bep_0003.html#peer-protocol
        # In version 1.0 of the BitTorrent protocol, pstrlen = 19, and pstr = "BitTorrent protocol".
        pstrlen = 19

        # send byte string handshake to peer
        bin_reserved = binascii.unhexlify(reserved_hex_ascii)
        byte_string = chr(pstrlen) + protocol_string  # +reserved_hex_ascii
        # byte_string = str.encode(byte_string)
        byte_string = str.encode(byte_string)
        byte_string = byte_string + bin_reserved + info_hash + str.encode(self.pid)
        #### TEST PRINTS ####
        # print('pid : ', self.pid)
        # print('info_hash : ', info_hash)
        # print('byte string : ', byte_string)
        # print('byte string post pid : ', byte_string)
        # binstr = reserved_hex_ascii.encode()
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.settimeout(10)
        print("Trying to connect to {0}:{1}".format(self.ip, self.port))
        try:
            self.socket.connect((self.ip, self.port))
            print("sending byte_string handshake...")
            self.socket.send(byte_string)

            # The global reserved_hex_ascii stores the reserved value, but you'll
            # need to convert it from ascii-written hex to binary data.

            # You'll need to set up a TCP socket here to the peer (the self value
            # for this object represents the peer connection, remember)

            # Here you'll need to consume the response. Use recv on this socket to
            # get the message. First you need to discover how big the message is
            # going to be, and then you need to consume the full handshake.
            # handshake is (49+len(pstr)) bytes long.
            resp_length = self.socket.recv(1)
            resp_length = int.from_bytes(resp_length, byteorder="big")
            return_protocol = self.socket.recv(resp_length)
            res_bytes = self.socket.recv(8)
            return_hash = self.socket.recv(20)
            resp_pid = self.socket.recv(20)

            #### TEST PRINTS ####
            # print("Response protocol")
            # print(return_protocol)
            # print("reserved bytes")
            # print(res_bytes)
            # print("Response hash")
            # print(return_hash)
            # print("Response pid")
            # print(resp_pid)

            return True
            # If you got a handshake, it's time to handle incoming messages.

        except:
            print("[Errno 51]: Network is unreachable")
            print("No returned handshake from peer")
            return False

    def handle_messages(self):
        # This method will handle messages from the peer coming
        # in on the socket. Read the section of the BT specification
        # closely! Read until the "Algorithms" section.
        # https://wiki.theory.org/BitTorrentSpecification#Peer_wire_protocol_.28TCP.29

        # Declare any necessary global variables
        # here using the 'global' keyword
        # <length_prefix><message ID><payload> form of these messages
        # length is 4 bytes, length is 1 byte, payload is length-dependent (length-5bytes)

        while True:
            # Grab first four bytes of the message to see how
            # long the message is going to be. You can tell a lot (most of
            # what you need to know) just by the length of the message.
            data = self.socket.recv(4)

            # Remember, the argument to recv() tells the socket how many bytes
            # to read. Use this to control the incoming message flow.

            # Remember, the data coming in is in bytes. You'll need to get an
            # int value to determine the size of the message. Use
            #
            # int.from_bytes(data, byteorder='big')
            #
            # for this, where data is the 4 byte sequence you just read in. FYI,
            # the second argument here indicates that the bytes should be
            # read in the "big-endian" way, meaning most significant on the left.
            size = int.from_bytes(data, byteorder="big")
            ####### TEST PRINTS #########
            # Now to handle the different size cases:
            #
            # if #SIZE IS BITFIELD SIZE (in bytes, of course)
            if size == 2:
                # get the id of the message
                messid = self.socket.recv(1)
                messid = int.from_bytes(messid, byteorder="big")
                # In this case, the peer is sending us a message composed of a series
                # of *bits* corresponding to which *pieces* of the file it has. So, the
                # length of this will be... bits, bytes, pieces, oh dear! Remember there's
                # always an extra byte corresponding to the message type, which comes
                # right after the length sequence and in this case should be 5.
                # Just to be sure, you should receive another byte and make sure it is
                # in fact equal to 5, before consuming the whole bitfield.
                # if # Check the message type is 5, indicating bitfield
                if messid == 5:  # tmp
                    print("Receiving bitfield")
                    # The peer's 'have' attribute is a bitarray. You can assign
                    # that here based on what you've just consumed, using
                    # bitarray's frombytes method.
                    #
                    # https://pypi.python.org/pypi/bitarray
                    bitlength = size - 1
                    self.have = bitarray(endian="big")
                    havebytes = self.socket.recv(bitlength)
                    self.have.frombytes(havebytes)
                    self.have = self.have[: self.torrent_data.no_of_pieces]
                    print("Peer have: {0}".format(self.have))
                    # you can use the bitarray all() method to determine
                    # if the peer has all the pieces. For this exercise,
                    # we'll keep it simple and only request pieces from
                    # peers that can provide us with the whole file. Of course
                    # in a real BT client this would defeat the purpose.
                    has_whole_file = all(self.have)
                    # If the peer does have all the pieces, now would be a good time
                    # to let them know we're interested.
                    if has_whole_file == True:
                        ###### TEST PRINTS ######
                        print("Interested in peer {0}".format(self.ip))
                        self.socket.send(INTERESTED)
                    else:
                        pass

            elif size == 0:
                # SIZE IS ZERO
                print("keep-alive")
                # It's a keep alive message. The least interesting message in the
                # world. You can handle this however you think works best for your
                # program, but you should probably handle it somehow.
                pass

            elif size == 1:
                # get the id of the message
                messid = self.socket.recv(1)
                messid = int.from_bytes(messid, byteorder="big")
                # SIZE IS ONE
                # If the message size is one, it could be one of several simple
                # messages. The only one we definitely need to care about is unchoke,
                # so that we know whether it's okay to request pieces. The message
                # code for unchoke is 1, so make sure you consume a byte and deal with
                # that message.
                # If you do get an unchoke, then you're doing great! You've found
                # a peer out there who will give you some data. Now would be the time
                # to go pluck up your courage and make that request!
                if messid == 1:
                    print("Unchoked by peer {0}".format(self.ip))
                    return True
            # When making a request here, we'll go ahead and simply start with
            # the first piece at the zero index (block) and progress through in
            # order requesting from the same peer. Note: In a real implementation,
            # you would probably take a different approach. A common way to do
            # it is to look at all peers' bitfields and find the rarest piece
            # among them, then request that one first.
            # i = 0
            # while i < torrent_data.no_of_pieces:
            #   print("requesting piece " + str(i))
            #  self.request_piece(s, i)
            # i = i + 1

            elif size == 5:
                # get the id of the message
                messid = self.socket.recv(1)
                messid = int.from_bytes(messid, byteorder="big")
                # SIZE IS FIVE
                if messid == 4:
                    piece_index = self.socket.recv(4)
                    piece_index = int.from_bytes(piece_index, byteorder="big")

                    list_have_pieces.append(piece_index)
                    # It's a have. Some clients don't want so send just a bitfield, or
                    # maybe not send one at all. Instead, they want to tell you index
                    # by index which pieces they have. This message would include a
                    # single byte for the message type (have is 4) followed by 4 bytes
                    # representing an integer index corresponding to the piece the have.
                    num_have_pieces = len(list_have_pieces)
                    # If you get have messages for all the pieces, that also tells you
                    # that the peer has the pieces you need, so now is also a good time
                    # to check their have array, and if they've got all the pieces send
                    # them an interested message.
                    ######## TEST PRINTS ########
                    # print("have piece " + str(piece_index))
                    # print("num_have_pieces = " + str(num_have_pieces))
                    # print("no_of_pieces = " + str(torrent_data.no_of_pieces))
                    if num_have_pieces == torrent_data.no_of_pieces:
                        print("Peer has all the pieces")
                        self.socket.send(INTERESTED)

            elif size == req_block_size_int or size == last_block_size_int + 9:
                # get the id of the message
                messid = self.socket.recv(1)
                messid = int.from_bytes(messid, byteorder="big")
                # SIZE IS REQUESTED BLOCK SIZE OR LAST BLOCK SIZE (PLUS 9)
                # This must be a block of data. You'll have to do the bookkeeping
                # to know whether you're consuming a standard sized block (defined
                # in global variable req_block_size_int) or a smaller one for the
                # last block, because you'll need to consume the appropriate
                # number of bytes. Check the wireshark traces for why this size
                # should be "plus 9".

                # Remember, a block isn't a full piece. Here is where I'd suggest you
                # call the function that consumes the block.

                # get_block(self, data, sock)
                pass

            if not data:
                # There's also the case that there's no data for the socket. You probably
                # want to handle this in some way, particularly while you're developing
                # and haven't got all the message handling fully implemented.
                break


