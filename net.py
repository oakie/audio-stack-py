import math
from frame import Frame
from packet import Packet


class NetLayer:
    def __init__(self):
        self.frame_buffer = []

    def rx(self, frames):
        self.frame_buffer += frames
        self.sync()
        packets = self.frames_to_packet()
        return packets

    def tx(self, packet):
        frames = []
        if packet is not None:
            frames = self.packet_to_frames(packet)
        return frames

    def packet_to_frames(self, packet):
        frames = []

        byte_array = []
        byte_array += packet.id  # Packet.HEADER_ID_BYTES
        byte_array += packet.size.to_bytes(Packet.HEADER_SIZE_BYTES, byteorder='big')
        byte_array += packet.receiver.to_bytes(Packet.HEADER_RECEIVER_BYTES, byteorder='big')
        byte_array += packet.sender.to_bytes(Packet.HEADER_SENDER_BYTES, byteorder='big')
        byte_array += packet.data

        count = int(math.ceil(len(byte_array) / Frame.PAYLOAD_BYTES))
        for i in range(count):
            start_byte = i * Frame.PAYLOAD_BYTES
            frame = Frame(i, count, byte_array[start_byte:start_byte + Frame.PAYLOAD_BYTES])
            frames.append(frame)

        return frames

    def frames_to_packet(self):
        packets = []
        while True:
            count = len(self.frame_buffer)

            if count == 0:
                return packets

            packet_frames = self.frame_buffer[0].end
            if packet_frames > count:
                return packets

            # we have enough frames to make a packet
            byte_array = []
            for i in range(packet_frames):
                byte_array += self.frame_buffer[i].data
            self.frame_buffer = self.frame_buffer[packet_frames:]

            packet_id = int.from_bytes(byte_array[0:16], 'big')
            packet_size = int.from_bytes(byte_array[16:18], 'big')
            packet_receiver = int.from_bytes(byte_array[18:24], 'big')
            packet_sender = int.from_bytes(byte_array[24:30], 'big')
            packet_data = byte_array[30:30+packet_size]

            packet = Packet(packet_id, packet_data, packet_receiver, packet_sender)
            packets.append(packet)
            return packets

    def sync(self):
        # Make sure we are in sync with packet bounds
        while len(self.frame_buffer) > 0:
            if self.frame_buffer[0].seq != 0:
                self.frame_buffer = self.frame_buffer[1:]
            else:
                return
