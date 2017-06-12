from frame import Frame
from util import arr_to_str


def bytes_to_bits(byte_array):
    bit_array = []
    for byte in byte_array:
        bit_array += [(byte & (1 << shift)) >> shift for shift in reversed(range(8))]
    return bit_array


def bits_to_bytes(bit_array):
    byte_array = []
    for i in range(0, len(bit_array), 8):
        if i + 8 > len(bit_array):
            break
        byte = 0
        for b in range(8):
            byte |= (bit_array[i+b] << (7-b))
        byte_array.append(byte)
    return byte_array


def bytes_to_frame(byte_array):
    frame_seq = int(byte_array[0])
    frame_end = int(byte_array[1])
    frame_data = byte_array[2:]
    return Frame(frame_seq, frame_end, frame_data)


def frame_to_bytes(frame):
    byte_array = [frame.seq & 0xff, frame.end & 0xff]
    byte_array += frame.data
    return byte_array


class LnkLayer:
    def __init__(self):
        self.bit_buffer = []
        self.bits_per_frame = Frame.FRAME_BYTES * 8

    def rx(self, bit_array):
        self.bit_buffer += bit_array

        frames = []
        while True:
            if len(self.bit_buffer) < self.bits_per_frame:
                return frames

            byte_array = bits_to_bytes(self.bit_buffer[0:self.bits_per_frame])
            print('lnk.rx: ' + arr_to_str(byte_array, 3))
            self.bit_buffer = self.bit_buffer[self.bits_per_frame:]

            frame = bytes_to_frame(byte_array)
            frames.append(frame)
            print('lnk.rx: ' + str(frame))

    def tx(self, frames):
        bit_array = []
        for f in frames:
            # TODO: apply error correction here
            byte_array = frame_to_bytes(f)
            print('lnk.tx: ' + arr_to_str(byte_array, 3))
            bit_array += bytes_to_bits(byte_array)
        if any(bit_array):
            print('lnk.tx: ' + arr_to_str(bit_array, 1))
        return bit_array
