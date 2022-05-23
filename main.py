# XXX SOURCES :
# http://www.kristenwidman.com/blog/33/how-to-write-a-bittorrent-client-part-1/
# https://wiki.theory.org/BitTorrentSpecification#Tracker_HTTP.2FHTTPS_Protocol
# https://github.com/eweast/BencodePy

"""
todo: 
-add multifile
-make tests
-make it wait on socket time out

"""
#package imports
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
from utils.constants import *
from utils.torrentData import *
from utils.peerConnection import *
from utils.decode import *

# Here are some global variables for your use throughout the program.
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
# variable used to store the global bencodepy decoded ordered dict & info
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
        # call tracker request
        tracker_req(bt_data, info_hash,run)
    else:
        print("incorrect number of arguments")

    for peer in run.peer_connections:
        if done:
            sys.exit(1)
        else:
            # XXX test print XXX
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
        # full featured implementation would require multiple concurrent
        # requests for different pieces of the file to different peers.
        # multiple threads or other ways to handle concurrency, and would also
        # involve a bit more bookkeeping
        # This implementation: whole file from a single peer, cycling through the
        # list of peers until we find one that provides with the full file


def get_block(peer, data, sock,run):
    # This is where we consume a block of data and use it to
    # build our pieces

    # Include any necessary globals
    global total_bytes_gotten
    global done
    global file_array
    # We need to know how big the block is going to be (we can get that
    # from 'data'. We then want to double check that the message type is
    # the appropriate value (check the specs for the "piece" message value,
    # which is what we're reading right now))
    # piece message: <len=0009+X><id=7><index><begin><block>
    recv = sock.recv(4)
    len_block = data
    len_piece = int.from_bytes(recv, byteorder="big")
    lenblock = int.from_bytes(len_block, byteorder="big")
    recv = sock.recv(1)
    messid = int.from_bytes(recv, byteorder="big")
    if messid == 7:  # tmp, the message value is correct
        # get the index and offset. Read the description of the "piece" message
        # to see how to do this.
        index = sock.recv(4)
        offset = sock.recv(4)
        block = b""
        while (
            len(block) < lenblock
        ):  # as long as the block is smaller than the expected block size
            data = sock.recv(1)
            block = block + data
            # continue to receive data from your socket and
            # append it to the block. When the block is the size
            # you're expecting, break out of the loop.
            # You can use len() to check the size of the block.
            if len(block) == len_block:
                break
        # You've got a block. Now add it to the piece it belongs to. I suggest
        # Making an array of pieces which can be accessed by index.
        # temp_array = []
        # temp_array.append(block)
        file_array = file_array + block
        # temp = b''
        # temp_array = temp.join(temp_array)
        # temp_array = temp_array
        # print(temp_array)
        # file_array.extend(temp_array)
        # It may also be helpful to keep a record of how many bytes you've gotten
        # in total towards the full file.
        total_bytes_gotten = len(block) + total_bytes_gotten
        # He's a little report
        print(
            "Got a block (size: {0})\tTotal so far: {1} out of {2}".format(
                len(block), total_bytes_gotten, run.torrent_data.total_length
            )
        )

        # If you haven't fully downloaded a piece, you need to get the next block
        # within the piece. The piece index stays the same, but the offset must
        # be shifted to get a later block. This is done by adding the requested
        # block size to the previous offset
        # if the new offset is greater than the length of the piece, you
        # must be done with that piece. Since we're just getting pieces in
        # order, you can just go ahead and request the next piece, beginning
        # with an offset of 0. (Of course, if the next index is greater than
        # or equal to the total number of pieces, you are finished downloading
        # and should write your downloaded data to a file).

        if done == False:  # There's still pieces to be downloaded
            # Request the first block of the next piece.
            index = math.floor(total_bytes_gotten / run.torrent_data.piece_length)
            index = int(index)
            request_piece(peer, sock, index, run)
        else:
            # Join all the elements of the downloaded pieces array using
            # .join()
            # print(file_array)
            output_filename = run.torrent_data.output_filename
            # file_array_str = map(str, file_array)
            # file_contents = b''.join(file_array)
            file_contents = file_array
            # print(file_contents)
            outfile = open(output_filename, "wb+")
            # outfile = open(file_contents, 'wb')
            # Write the full content to the outfile file
            outfile.write(file_contents)
            print("Download complete. Wrote file to {0}".format(output_filename))
            done = True
            sys.exit(1)


def request_piece(peer, sock, index,run):  # You'll need access to the socket,
    # the index of the piece you're requesting, and the offset of the block
    # within the piece.
    # Declare any necessary globals here
    global total_bytes_gotten
    global done
    # The piece index and offset will need to be converted to bytes
    # Read the specs for request structure:
    # <len=0013><id=6><index (4 bytes)><begin (4 bytes)><length (4 bytes)>
    if index == 0:
        offset = total_bytes_gotten
    else:
        offset = ((total_bytes_gotten / req_block_size_int) % 2) * req_block_size_int
        offset = int(offset)
    # if it's the last section of the last piece:
    length_last_block = run.torrent_data.total_length - total_bytes_gotten
    if (
        index == run.torrent_data.no_of_pieces - 1
        and length_last_block < req_block_size_int
    ):
        # adjust the length accordingly
        length = run.torrent_data.total_length - total_bytes_gotten
        done = True

    else:
        length = req_block_size_int

    offset = offset.to_bytes(4, byteorder="big")
    length = length.to_bytes(4, byteorder="big")
    index = index.to_bytes(4, byteorder="big")
    # Build the request here before sending it into the socket.
    # Length is set as a global at the recommended 16384 bytes. However, the
    # request will be disregarded if there is less data to send than that
    # amount, which is likely to be the case for the final block in the file.
    # For this reason, will probably want to build the request slighly
    # differently for the final block case. Keeping track of the total number
    # of bytes you've collected can be helpful for this.
    # request: <len=0013><id=6><index><offset><length>
    start = b"\x00\x00\x00\r\x06"
    req = start + index + offset + length
    ################ TEST PRINTS #################
    # print("***REQUEST MESSAGE***")
    # print(req)
    # print("index " + str(index))
    # print("length: " + str(length))
    # print("no_of_pieces: ", torrent_data.no_of_pieces)
    # print("last: ", length_last_block)
    # print("offset " + str(offset))

    # Send the request:
    sock.send(req)
    get_block(peer, length, sock,run)




def get_data_from_torrent(arg):
    # https://github.com/eweast/BencodePy
    # try to parse and decode the torrent file...
    try:

        # assign file_path based on the command line arg/param
        file_path = arg

        # call the decode_from_file() function that's a member of the bencodepy class`
        btdata = bencodepy.decode_from_file(file_path)

        # store the fresh, bencodepy decoded data in the global scope
        global btdata_backup
        btdata_backup = btdata

        # XXX test print XXX
        # print("\n\n::::::btdata backup  : \n\n", btdata_backup, "\n\n")

        # next, build the decoded dictionary through a series of iterative statements within the btdata OrderedDict object
        # the "builder" variable used for this we'll call decoded_dict
        decoded_dict = {}

        # for each of the key:value pairs in the OrderedDict, try to decode both the key and the value
        # finally, append the results to the builder dictionary : decoded_dict
        for x, y in btdata.items():

            # decode the key
            x = x.decode("UTF-8")
            # try to decode the value associated with the key...
            try:
                y = y.decode("UTF-8")
            except AttributeError:
                # if we can't decode the value, just pass it for now
                pass
            decoded_dict[x] = y

        # decode the array elements that exist as the value for the 'url-list' key in the decoded_dict
        for x, member in enumerate(decoded_dict["url-list"]):
            decoded_dict["url-list"][x] = decoded_dict["url-list"][x].decode("UTF-8")

        # decode the array elements that exist as the value for the 'announce-list' key in the decoded_dict
        # this has another layer of complexity compared to decoding the elements in the 'url-list', this is
        # because some of the elements of the decoded_dict['announce-list'] are arrays themselves, need a nested loop :
        for x, member in enumerate(decoded_dict["announce-list"]):
            for y, member in enumerate(decoded_dict["announce-list"][x]):
                decoded_dict["announce-list"][x][y] = decoded_dict["announce-list"][x][
                    y
                ].decode("UTF-8")

        # store freshly bencodepy decoded info-ordered-dictionary
        global btdata_info_backup
        btdata_info_backup = decoded_dict["info"]

        # decode the (sub)ordered-dictionary that exists as a value corresponding to the 'info' key inside the decoded_dict dictionary
        # access this (sub)ordered-dictionary with : decoded_dict['info']
        # use the appendage_dict={} in order to temporarily store the sub-ordered-dictionary, this will be appended to the decoded_dict at the correct 'info' key after traversal
        appendage_dict = {}
        for x, y in decoded_dict["info"].items():

            # decode the key
            x = x.decode("UTF-8")
            # try to decode the value associated with the key...
            try:
                # we don't want to decode the value at the pieces key... this is a byte string
                if x != "pieces":
                    y = y.decode("UTF-8")

            except AttributeError:
                # if we can't decode the value, just pass it for now
                pass

            # append the key:value pair to the dictionary
            appendage_dict[x] = y

        # append the appendage_dict to the 'info' key of the decoded_dict dictionary, the same place where it came encoded from
        decoded_dict["info"] = appendage_dict

        # XXX test print XXX
        # print(decoded_dict)
        # XXX test print XXX

        # Do what you need to do with the torrent data.
        # You'll probably want to set some globals, such as
        # total_length, piece_length, number of pieces (you'll)
        # need to calculate that) etc. You might want to give
        # file_array its initial value here as an array of
        # empty binary sequences (b'') that can later be appended
        # to. There may be other values you want to initialize here.

        # instantiate an object to have the TorrentData class type
        # assign all of the key:value pairs to correspond to the relevant bit_torrent data
        # note : the number of pieces is thus determined by 'ceil( total length / piece size )'
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

        #  XXX test print XXX
        # print('total length : ', total_length)
        # print('piece length : ', piece_length)
        # print('piece length bytes : ', piece_length_bytes)
        # print('number of pieces :', no_of_pieces)
        # print('announce url :', announce_url)
        # print('output file name : ', output_filename)
        # print(decoded_dict['info']['pieces'])
        # print('type :', type(decoded_dict['info']['pieces'])) # type of
        #  XXX test print XXX

        # reporting torrent :
        report_torrent(torrent_data)

    except:
        print(
            'Failed to parse input. Usage: python btClient.py torrent_file"\ntorrent_file must be a .torrent file'
        )
        sys.exit(2)

    return torrent_data, decoded_dict


# main
if __name__ == "__main__":
    main()
