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


