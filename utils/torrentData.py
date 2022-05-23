req_block_size_int = 16384 
class TorrentData:
    def __init__(
        self,
        output_filename,
        total_length,
        total_length_bytes,
        piece_length,
        piece_length_bytes,
        no_of_pieces,
        announce_url,
    ):
        self.output_filename = output_filename
        self.total_length = total_length
        self.total_length_bytes = total_length_bytes
        self.piece_length = piece_length
        self.piece_length_bytes = piece_length_bytes
        self.no_of_pieces = no_of_pieces
        self.announce_url = announce_url
        blocks_per_piece = self.piece_length / req_block_size_int


