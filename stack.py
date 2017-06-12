from threading import Thread, Lock
import uuid
import time
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
import sounddevice as sd
from scipy.signal import lfilter

from phy import PhyLayer
from lnk import LnkLayer
from net import NetLayer
from frame import Frame
from packet import Packet
from util import bytes_to_str


class Stack:
    def __init__(self):
        # Layer setup
        self.phy = PhyLayer()
        self.lnk = LnkLayer()
        self.net = NetLayer()

        # Data packet buffers, for communication with application
        self.rx_packets_mutex = Lock()
        self.tx_packets_mutex = Lock()
        self.rx_packets = []
        self.tx_packets = []

        # Audio sample buffers, for communication with audio device
        self.rx_samples_mutex = Lock()
        self.tx_samples_mutex = Lock()
        self.rx_samples = np.array([])
        self.tx_samples = np.array([])

        # Worker threads, one per buffer
        self.rx_thread = Thread(target=self.__rx)
        self.tx_thread = Thread(target=self.__tx)
        self.play_thread = Thread(target=self.__play)
        self.rec_thread = Thread(target=self.__rec)

        self.history = np.array([])

    def __rec(self):
        def callback(indata, frames, time, status):
            if any(indata):
                self.rx_samples_mutex.acquire()
                self.rx_samples = np.append(self.rx_samples, indata)
                self.rx_samples_mutex.release()

        fs = self.phy.freq_sample
        with sd.InputStream(channels=1, callback=callback, blocksize=int(fs/10), samplerate=fs, dtype='float32'):
            while True:
                pass

    def __play(self):
        while True:
            self.tx_samples_mutex.acquire()
            samples = np.asarray(np.asarray(self.tx_samples, dtype='float32'))
            self.tx_samples = np.array(())
            self.tx_samples_mutex.release()

            if len(samples) > 0:
                sd.play(samples, self.phy.freq_sample, blocking=True)
            else:
                time.sleep(0.1)

    def __rx(self):
        while True:
            window_size = int(self.phy.freq_sample / 10)

            self.rx_samples_mutex.acquire()
            if window_size > len(self.rx_samples):
                window_size = len(self.rx_samples)
            samples = self.rx_samples[:window_size]
            self.rx_samples = self.rx_samples[window_size:]
            self.rx_samples_mutex.release()

            if any(samples):
                self.history = np.append(self.history, samples)

            bits = self.phy.rx(samples)
            frames = self.lnk.rx(bits)
            packets = self.net.rx(frames)

            for pkt in packets:
                string = bytes_to_str(pkt.data)
                print('* received: ' + string)

            self.rx_packets_mutex.acquire()
            self.rx_packets += packets
            self.rx_packets_mutex.release()

            time.sleep(0.01)

    def __tx(self):
        while True:
            pkt = None

            self.tx_packets_mutex.acquire()
            if len(self.tx_packets) > 0:
                pkt = self.tx_packets[0]
                self.tx_packets = self.tx_packets[1:]
            self.tx_packets_mutex.release()

            frames = self.net.tx(pkt)
            bits = self.lnk.tx(frames)
            samples = self.phy.tx(bits)

            if len(samples) > 0:
                self.tx_samples_mutex.acquire()
                self.tx_samples = np.append(self.tx_samples, samples)
                self.tx_samples_mutex.release()

            time.sleep(0.01)

    def start(self):
        self.rx_thread.start()
        self.tx_thread.start()
        self.rec_thread.start()
        self.play_thread.start()

    def send(self, string, receiver):
        data = [ord(char) for char in string]
        pkt = Packet(data=data, receiver=receiver)

        self.tx_packets_mutex.acquire()
        self.tx_packets.append(pkt)
        self.tx_packets_mutex.release()

    def recv(self):
        while True:
            packet = None
            self.rx_packets_mutex.acquire()
            if len(self.rx_packets) > 0:
                packet = self.rx_packets[0]
                self.rx_packets = self.rx_packets[1:]
            self.rx_packets_mutex.release()

            if packet is not None:
                return packet
            time.sleep(0.1)


if __name__ == '__main__':
    me = uuid.getnode()
    stack = Stack()

    stack.start()
    stack.send('Hello, world!', me)

    time.sleep(10)

    f0 = stack.phy.filter_freq_0
    y0 = lfilter(f0[0], f0[1], stack.history)
    f1 = stack.phy.filter_freq_1
    y1 = lfilter(f1[0], f1[1], stack.history)

    plt.figure()
    plt.plot(stack.history)
    plt.plot(y0)
    plt.plot(y1)
    plt.draw()
    plt.show()
