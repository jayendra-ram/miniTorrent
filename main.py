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
import argparse

from utils.constants import *
from utils.torrentData import *
from utils.decode import *
from utils.run import *


"""
todo:
-make arguments for file paths 
-add multifile
-make tests
-make it wait on socket time out
"""
def main():
    run = Run()
    parser = argparse.ArgumentParser()
    parser.add_argument("torrent", help="path to torrent file")
    args = parser.parse_args()
    if True:
        run.torrent_data, bt_data = get_data_from_torrent(args.torrent)
        info_hash = get_info_hash(bt_data)
        print("\n")
        tracker_req(bt_data, info_hash, run)
    else:
        print("incorrect number of arguments")
    for peer in run.peer_connections:
        if run.done:
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
                        run.request_piece(peer, peer.socket, i)
                        i += 1
def get_data_from_torrent(arg):
    # decodes torrent file and returns torrent data and bt_data
    try:
        file_path = arg
        btdata = bencodepy.decode_from_file(file_path)
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
        btdata_info = decoded_dict["info"]
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
        print('Failed to parse input. Usage: python btClient.py torrent_file"\ntorrent_file must be a .torrent file')
        sys.exit(2)
    return torrent_data, decoded_dict
if __name__ == "__main__":
    main()


