import uuid


class Packet:
    HEADER_ID_BYTES = 16
    HEADER_SIZE_BYTES = 2
    HEADER_RECEIVER_BYTES = 6
    HEADER_SENDER_BYTES = 6
    HEADER_BYTES = HEADER_ID_BYTES + HEADER_SIZE_BYTES + HEADER_RECEIVER_BYTES + HEADER_SENDER_BYTES

    def __init__(self, pid=uuid.uuid4().bytes, data=[], receiver=0, sender=uuid.getnode()):
        self.id = pid
        self.data = data
        self.size = len(self.data)
        self.receiver = receiver
        self.sender = sender
