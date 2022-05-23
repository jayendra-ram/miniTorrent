"""
todo: 
-add multifile
-make tests
-make it wait on socket time out

"""
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

peer_id = "M0-0-1-" + "".join(random.sample(ALPHANUM, 13))
peer_connections = []  # An array of PeerConnection objects
total_length = 0  # Total length of the file being downlaoded
no_of_pieces = 0  # Number of pieces the file's divided into
piece_length = 0  # Size of each piece
piece_length_bytes = 0
i_have = None  # A bitarray representing which pieces we have
file_array = b""  # An array of pieces (binary sequences)
last_block_size_int = 0  # The size of the last block of the file
output_filename = None  # The name of the file we'll write to the filesystem
total_bytes_gotten = 0  # Total number of bytes received towards the full file so far
total_length_bytes = 0
done = False  # Are we done yet?
torrent_url = ""
announce_url = ""
list_have_pieces = []  # list of numbers from "have" messages from a peer
btdata_backup = None
btdata_info_backup = None
newline = "\n"
blocks_per_piece = 0  # number of blocks per piece (piece_length/req_block_size_int)
r = 0
class Run():
    def __init__(self):
        self.total_bytes_gotten = 0
        self.peer_id = "M0-0-1-" + "".join(random.sample(ALPHANUM, 13))
        self.peer_connections = []
        self.torrent_data = None
def main():
    global done
    global r
    run  = Run()
    if len(sys.argv) == 2:
        run.torrent_data, bt_data = get_data_from_torrent(sys.argv[1])
        info_hash = get_info_hash(bt_data,btdata_info_backup)
        print(newline)
        tracker_req(bt_data, info_hash,run)
    else:
        print("incorrect number of arguments")

    for peer in run.peer_connections:
        if done:
            sys.exit(1)
        else:
            print("Try to handshake " + peer.ip + " " + str(peer.port))
            print("Trying to connect to {0}:{1}".format(peer.ip, str(peer.port)))
            handle = peer.handshake(info_hash)
            if handle:
                request = peer.handle_messages()
                if request:
                    print("requesting peer " + str(peer.ip))
                    i = 0
                    while i < run.torrent_data.no_of_pieces:
                        print("requesting piece " + str(i))
                        request_piece(peer, peer.socket, i, run)
                        i += 1

def get_block(peer, data, sock,run):

    global total_bytes_gotten
    global done
    global file_array
    recv = sock.recv(4)
    len_block = data
    len_piece = int.from_bytes(recv, byteorder="big")
    lenblock = int.from_bytes(len_block, byteorder="big")
    recv = sock.recv(1)
    messid = int.from_bytes(recv, byteorder="big")
    if messid == 7:  # tmp, the message value is correct
        index = sock.recv(4)
        offset = sock.recv(4)
        block = b""
        while (
            len(block) < lenblock
        ):  # as long as the block is smaller than the expected block size
            data = sock.recv(1)
            block = block + data
            if len(block) == len_block:
                break
        file_array = file_array + block
        total_bytes_gotten = len(block) + total_bytes_gotten
        print(
            "Got a block (size: {0})\tTotal so far: {1} out of {2}".format(
                len(block), total_bytes_gotten, run.torrent_data.total_length
            )
        )


        if done == False:  # There's still pieces to be downloaded
            index = math.floor(total_bytes_gotten / run.torrent_data.piece_length)
            index = int(index)
            request_piece(peer, sock, index, run)
        else:
            output_filename = run.torrent_data.output_filename
            file_contents = file_array
            outfile = open(output_filename, "wb+")
            outfile.write(file_contents)
            print("Download complete. Wrote file to {0}".format(output_filename))
            done = True
            sys.exit(1)


def request_piece(peer, sock, index,run):  # You'll need access to the socket,
    global total_bytes_gotten
    global done
    if index == 0:
        offset = total_bytes_gotten
    else:
        offset = ((total_bytes_gotten / req_block_size_int) % 2) * req_block_size_int
        offset = int(offset)
    length_last_block = run.torrent_data.total_length - total_bytes_gotten
    if (
        index == run.torrent_data.no_of_pieces - 1
        and length_last_block < req_block_size_int
    ):
        length = run.torrent_data.total_length - total_bytes_gotten
        done = True

    else:
        length = req_block_size_int

    offset = offset.to_bytes(4, byteorder="big")
    length = length.to_bytes(4, byteorder="big")
    index = index.to_bytes(4, byteorder="big")
    start = b"\x00\x00\x00\r\x06"
    req = start + index + offset + length

    sock.send(req)
    get_block(peer, length, sock,run)




def get_data_from_torrent(arg):
    try:

        file_path = arg

        btdata = bencodepy.decode_from_file(file_path)

        global btdata_backup
        btdata_backup = btdata


        decoded_dict = {}

        for x, y in btdata.items():

            x = x.decode("UTF-8")
            try:
                y = y.decode("UTF-8")
            except AttributeError:
                pass
            decoded_dict[x] = y

        for x, member in enumerate(decoded_dict["url-list"]):
            decoded_dict["url-list"][x] = decoded_dict["url-list"][x].decode("UTF-8")

        for x, member in enumerate(decoded_dict["announce-list"]):
            for y, member in enumerate(decoded_dict["announce-list"][x]):
                decoded_dict["announce-list"][x][y] = decoded_dict["announce-list"][x][
                    y
                ].decode("UTF-8")

        global btdata_info_backup
        btdata_info_backup = decoded_dict["info"]

        appendage_dict = {}
        for x, y in decoded_dict["info"].items():

            x = x.decode("UTF-8")
            try:
                if x != "pieces":
                    y = y.decode("UTF-8")

            except AttributeError:
                pass

            appendage_dict[x] = y

        decoded_dict["info"] = appendage_dict



        torrent_data = TorrentData(
            decoded_dict["info"]["name"],
            decoded_dict["info"]["length"],
            decoded_dict["info"]["length"] / 8,
            decoded_dict["info"]["piece length"],
            decoded_dict["info"]["piece length"] / 8,
            math.ceil(
                decoded_dict["info"]["length"] / decoded_dict["info"]["piece length"]
            ),
            decoded_dict["announce"],
        )


        report_torrent(torrent_data)

    except:
        print(
            'Failed to parse input. Usage: python btClient.py torrent_file"\ntorrent_file must be a .torrent file'
        )
        sys.exit(2)

    return torrent_data, decoded_dict


if __name__ == "__main__":
    main()
