
class Frame:
    PREAMBLE = [1, 0, 1, 0, 1, 0, 1, 0] * 3 + [1, 1, 1, 1, 1, 1, 1, 1]
    TAIL = [0, 0, 0, 0]

    HEADER_BYTES = 2
    PAYLOAD_BYTES = 36  # should be greater than the size of a packet header
    FRAME_BYTES = HEADER_BYTES + PAYLOAD_BYTES

    def __init__(self, seq, tot, data):
        self.seq = seq  # 1 byte
        self.end = tot  # 1 byte
        self.data = data  # PAYLOAD_BYTES

        # pad with zeros if too short
        if len(self.data) < self.PAYLOAD_BYTES:
            self.data += [0] * (self.PAYLOAD_BYTES - len(self.data))

    def __str__(self):
        return 'Frame (%d / %d): %s' % (self.seq+1, self.end, str(self.data))
