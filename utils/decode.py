import bencodepy
import hashlib  # SHA1 hashing for info hash
import requests
from constants import *
from peerConnection import *

def get_info_hash(btdata,btdata_info_backup):
    encoded_info_dictionary = bencodepy.encode(btdata_info_backup)


    digest_builder = hashlib.sha1()
    digest_builder.update(encoded_info_dictionary)
    digest_builder = digest_builder.digest()


    return digest_builder

def tracker_req(btdata, info_hash, run):
    uploaded = 0

    left = btdata["info"]["length"] / 8 - run.total_bytes_gotten

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

    response = requests.get(btdata["announce"], params=reqParams)



    decoded_response_content = bencodepy.decode(response.content)


    decoded_dict = {}

    for x, y in decoded_response_content.items():

        x = x.decode("UTF-8")
        try:
            y = y.decode("UTF-8")
        except AttributeError:
            pass
        decoded_dict[x] = y


    for x, member in enumerate(decoded_dict["peers"]):
        peer_builder = {}

        for i, j in decoded_dict["peers"][x].items():

            i = i.decode("UTF-8")
            if isinstance(j, int):
                pass
            elif "peer" not in i:
                j = j.decode("UTF-8")
            else:
                pass

            peer_builder[i] = j




        run.peer_connections.append(
            PeerConnection(
                peer_builder["ip"],
                peer_builder["port"],
                peer_builder["peer id"].decode("latin-1"),
                run.torrent_data
            )
        )




    report_tracker(run.peer_connections)

def report_torrent(torrent_data):
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


def report_tracker(peer_connections):
    for p in peer_connections:  # peer array returned by tracker
        print("Peer: {0} (ip addr: {1})".format(p.pid, p.ip))  #


