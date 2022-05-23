import bencodepy
import hashlib  # SHA1 hashing for info hash
import requests
from constants import *
from peerConnection import *

# the purpose of this is to produce the info_hash variable, which is requisite in the
# request for the tracker server
def get_info_hash(btdata,btdata_info_backup):
    # https://docs.python.org/3/library/hashlib.html
    # get the info directory, re-encode it into bencode, then encrypt it with
    # SHA1 using the hashlib library and generate a digest.

    # XXX test print XXX
    # print("\n\n::::::btdata backup  : \n\n", btdata_backup, "\n\n")
    # print("\n\n::::::INFO btdata backup  : \n\n", btdata_info_backup, "\n\n")

    # XXX test print XXX
    # print('re-encoded : ', btdata['info'])

    # first, encode info_dictionary in bencode before encrypting using sha1
    encoded_info_dictionary = bencodepy.encode(btdata_info_backup)

    # XXX test print XXX
    # print('encoded info dictionary : ', encoded_info_dictionary)

    # encrypt the encoded_info_dictionary using sha1 & generate sha1 hash digest
    digest_builder = hashlib.sha1()
    digest_builder.update(encoded_info_dictionary)
    digest_builder = digest_builder.digest()

    # XXX test print XXX
    # print('digest builder : ', digest_builder,'\n\n')

    return digest_builder

# this function is used to make a request to the remote tracker server.
# the tracer server listens for a request of a given torrent
# if the tracker has a record for the torrent,
# then the tracker will respond with a "map" of peers that have the desired
# torrent "pieces" available
# note, if parameters are sent to the script via an HTTP GET request (a question mark appended to the URL, followed by param=value pairs; in the example, ?and=a&query=string)
# example, ?and=a&query=string
def tracker_req(btdata, info_hash, run):

    # XXX test print XXX
    # print('\n\nannounce url ::', btdata['announce'])

    # Build the params object. Read the bittorrent specs for tracker querying.
    # The parameters are then added to this URL, using standard CGI methods (i.e. a '?' after the announce URL, followed by 'param=value' sequences separated by '&').
    # https://wiki.theory.org/BitTorrentSpecification#Tracker_HTTP.2FHTTPS_Protocol

    # the uploaded request parameter is used to indicate the number of bytes that have been
    # uploaded to the server,
    uploaded = 0

    # left = total_length_bytes - run.total_bytes_gotten
    left = btdata["info"]["length"] / 8 - run.total_bytes_gotten

    # assign request parameter key:value pairs
    reqParams = {
        "info_hash": info_hash,
        "peer_id": run.peer_id,
        "port": local_port,
        "uploaded": uploaded,
        "downloaded": run.total_bytes_gotten,
        "left": left,
        "compact": 0,
        "event": "",
    }  #

    # use the requests library to send an HTTP GET request to the tracker
    response = requests.get(btdata["announce"], params=reqParams)

    # XXX test print XXX
    # print('response : ', response)
    # print('response text :', response.text)
    # print('response directory :', dir(response))
    # print('response content :', response.content)

    # decode response text with bencodepy library.

    decoded_response_content = bencodepy.decode(response.content)

    # XXX test print XXX
    # print('\nbencodepy.decoded response content', decoded_response_content)

    # decoded_dict builder for housing the decoded-data that makes up the repsonse dictionary
    decoded_dict = {}

    # for each of the key:value pairs in the OrderedDict, try to decode both the key and the value
    # finally, append the results to the builder dictionary : decoded_dict
    for x, y in decoded_response_content.items():

        # decode the key, utf-8
        x = x.decode("UTF-8")
        # try to decode the value associated with the key...
        try:
            y = y.decode("UTF-8")
        except AttributeError:
            # if we can't decode the value, just pass it for now
            pass
        decoded_dict[x] = y

    # XXX test print XXX
    # print('\ndecoded dict : ', decoded_dict)

    # decode the array elements that exist as the value for the 'url-list' key in the decoded_dict
    for x, member in enumerate(decoded_dict["peers"]):
        # peer builder
        peer_builder = {}

        # for the key:value pairs in the peer section of the decoded-dictionary
        for i, j in decoded_dict["peers"][x].items():

            # decode the key, utf-8
            i = i.decode("UTF-8")
            # try to decode the value, pass if it's an int or not containing 'peer'
            if isinstance(j, int):
                pass
            elif "peer" not in i:
                j = j.decode("UTF-8")
            else:
                pass

            # add data about the peer to the temporary peer_builder
            peer_builder[i] = j

            # XXX test print XXX
            # print(x,i,j)

        # TODO :
        # need to decode the peer_id values that are returned in the tracker's response :
        # decode_pid = bencodepy.decode(peer_builder['peer id'])
        # print('peer builder ID ::::', bencodepy.decode(peer_builder['peer id']))
        # print('peer builder ID ::::', peer_builder['peer id'].decode('UTF-8'))
        # print('peer builder ID ::::' + peer_builder['peer id'])
        # bbb = peer_builder['peer id'].decode("utf-8")
        # bbb = bencodepy.decode(peer_builder['peer id'])
        # decode_pid = peer_builder['peer id'].decode('latin-1')

        # XXX test print XXX
        # print(decode_pid)

        # append the peer_connection to the list
        run.peer_connections.append(
            PeerConnection(
                peer_builder["ip"],
                peer_builder["port"],
                peer_builder["peer id"].decode("latin-1"),
                run.torrent_data
            )
        )

    # XXX test print XXX
    # print(peer_connections)

    # The tracker responds with "text/plain" document consisting of a bencoded dictionary

    # bencodepy is a library for parsing bencoded data:
    # https://github.com/eweast/BencodePy
    # read the response in and decode it with bencodepy's decode function

    # Once you've got the dictionary parsed as "tracker_data" print out the tracker request report:
    report_tracker(run.peer_connections)

def report_torrent(torrent_data):
    # Nothing special here, just reporting the data from
    # the torrent. Note the Python 3 format syntax

    # assume that the number of files in the torrent is "one"
    no_of_files = "one"

    print("\nAnnounce URL: {0}".format(torrent_data.announce_url))
    print("Name: {0}".format(torrent_data.output_filename))
    try:
        print("Includes {0} files".format(no_of_files))
    except:
        print("Includes one file")
    print("Piece length: {0}".format(torrent_data.piece_length))
    print("Piece len (bytes): {0}".format(torrent_data.piece_length_bytes))
    print(
        "Total length: {0} ({1} bytes)".format(
            torrent_data.total_length, torrent_data.total_length_bytes
        )
    )
    print("Number of pieces: {0}".format(torrent_data.no_of_pieces))


# report_tracker() is used to report peer information
def report_tracker(peer_connections):
    for p in peer_connections:  # peer array returned by tracker
        print("Peer: {0} (ip addr: {1})".format(p.pid, p.ip))  #


