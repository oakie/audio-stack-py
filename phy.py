from scipy.signal import chirp, butter, lfilter

from frame import Frame
from util import arr_to_str

import numpy as np


def goertzel(x, freq, rate):
    coeff = 2 * np.cos(2.0 * np.pi * freq / rate)
    prev1 = prev2 = 0.0
    for n in range(0, len(x)):
        s = x[n] + (coeff * prev1) - prev2
        prev2 = prev1
        prev1 = s
    power = prev2*prev2 + prev1*prev1 - coeff*prev1*prev2
    return np.sqrt(power)


def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


class PhyLayer:
    def __init__(self, freq_sample=2*2*3*3*5*5*7*7, freq_carrier=2*2*3*5*5*7, baud_rate=3*3*7*7):
        assert(freq_sample % baud_rate == 0)

        self.freq_sample = freq_sample
        self.freq_carrier = freq_carrier
        self.bits_per_frame = Frame.FRAME_BYTES * 8

        # TODO: find some other means of matching phase of the 0/1-bit samples to enable higher frequencies
        # f1 = 2 * f0 -> harmony so that phases match if baud_rate divides f0
        self.freq_dev = freq_carrier / 3.0
        self.freq_bit_0 = self.freq_carrier - self.freq_dev
        self.freq_bit_1 = self.freq_carrier + self.freq_dev
        self.baud_rate = baud_rate
        self.samples_per_bit = int(self.freq_sample / self.baud_rate)

        print('phy: sample frequency: %d Hz' % self.freq_sample)
        print('phy: carrier frequency: %d Hz' % self.freq_carrier)
        print('phy: symbol frequencies: 0: %d Hz  1: %d Hz' % (self.freq_bit_0, self.freq_bit_1))
        print('phy: data rate: %d Bd' % self.baud_rate)
        print('phy: samples per bit: %d' % self.samples_per_bit)
        print('phy: cycles per bit: %f/%f' % (self.freq_bit_0 / self.baud_rate, self.freq_bit_1 / self.baud_rate))

        rads_per_bit_0 = 2 * np.pi * self.freq_bit_0 / self.baud_rate
        rads_per_bit_1 = 2 * np.pi * self.freq_bit_1 / self.baud_rate
        self.samples_bit_0 = np.sin(np.linspace(0, rads_per_bit_0, self.samples_per_bit + 1))[:-1]
        self.samples_bit_1 = np.sin(np.linspace(0, rads_per_bit_1, self.samples_per_bit + 1))[:-1]

        dev = 500
        self.filter_freq_0 = butter_bandpass(self.freq_bit_0 - dev, self.freq_bit_0 + dev, self.freq_sample)
        self.filter_freq_1 = butter_bandpass(self.freq_bit_1 - dev, self.freq_bit_1 + dev, self.freq_sample)

        self.preamble = np.array([])
        for bit in Frame.PREAMBLE:
            self.preamble = np.append(self.preamble, self.samples_bit_1 if bit == 1 else self.samples_bit_0)
        self.preamble_str = ''.join(map(str, Frame.PREAMBLE))

        self.sample_buffer = np.array(())
        self.frame_bits_remaining = 0

    def rx(self, signal_samples):
        self.sample_buffer = np.append(self.sample_buffer, signal_samples)

        # skip ahead until start of frame is detected
        while self.frame_bits_remaining == 0:
            if len(self.sample_buffer) < 2 * len(self.preamble):
                return []
            self.sync()

        # check if in sync with start of frame
        if self.frame_bits_remaining > 0:
            bit_array = self.demodulate()
            if any(bit_array):
                print('phy.rx: ' + str(arr_to_str(bit_array, 1)))
            return bit_array
        else:
            return []

    def tx(self, bit_array):
        if len(bit_array) < self.bits_per_frame:
            return np.array([])

        print('phy.tx: ' + arr_to_str(bit_array, 1))
        signal_samples = np.array([])
        offset = 0
        while offset < len(bit_array):
            frame_bits = bit_array[offset:offset+self.bits_per_frame]
            # Insert the frame between a preamble and a tail of silence
            signal_samples = np.append(signal_samples, self.preamble)
            signal_samples = np.append(signal_samples, self.modulate(frame_bits))
            signal_samples = np.append(signal_samples, np.linspace(0, 0, len(self.preamble)))
            offset += self.bits_per_frame
        return signal_samples

    def sync(self):
        samples = self.sample_buffer[:2 * len(self.preamble)]

        d = 6
        offset = int(self.samples_per_bit / d)
        bit_array = []
        best_score = -1
        sample_offset = 0
        for i in range(d):
            bits, score = self.__demodulate_bits(samples[i * offset:])
            # Try to align with bit boundary by testing different sample offsets
            if score > best_score:
                best_score = score
                sample_offset = i * offset
                bit_array = bits

        # Try to align with frame boundaries by searching for the preamble bits
        bit_str = ''.join(map(str, bit_array))
        bit_offset = bit_str.find(self.preamble_str)

        if bit_offset > -1:
            # Preamble was found with start at bit_offset, skip to the end of the preamble
            print('phy.sync: found preamble! ' + str(bit_offset) + '  ' + bit_str)
            sample_offset += bit_offset * self.samples_per_bit + len(self.preamble)
            self.sample_buffer = self.sample_buffer[sample_offset:]
            self.frame_bits_remaining = self.bits_per_frame  # assume frame starts immediately
        else:
            # Preamble was not found, skip ahead
            self.sample_buffer = self.sample_buffer[len(self.preamble):]

    def modulate(self, bit_array):
        samples = np.array(())
        for bit in bit_array:
            samples = np.append(samples, self.samples_bit_1 if bit == 1 else self.samples_bit_0)
        return samples

    def demodulate(self):
        available_bits = int(len(self.sample_buffer) / self.samples_per_bit)
        if available_bits > self.frame_bits_remaining:
            available_bits = self.frame_bits_remaining

        sample_count = available_bits * self.samples_per_bit
        bit_array, _ = self.__demodulate_bits(self.sample_buffer[:sample_count])
        self.sample_buffer = self.sample_buffer[sample_count:]
        self.frame_bits_remaining -= len(bit_array)
        return bit_array

    def __demodulate_bits(self, samples):
        count = int(len(samples) / self.samples_per_bit)
        bit_array = []
        score = 0
        for i in range(count):
            bit, separation = self.__match_bit(samples[:self.samples_per_bit])
            bit_array.append(bit)
            score += separation * separation
            samples = samples[self.samples_per_bit:]
        return bit_array, score

    def __match_bit(self, samples):
        filtered_0 = lfilter(self.filter_freq_0[0], self.filter_freq_0[1], samples)
        filtered_1 = lfilter(self.filter_freq_1[0], self.filter_freq_1[1], samples)

        power_0 = goertzel(filtered_0, self.freq_bit_0, self.freq_sample)
        power_1 = goertzel(filtered_1, self.freq_bit_1, self.freq_sample)
        bit = 1 if power_1 > power_0 else 0
        separation = abs(power_0 - power_1)
        return bit, separation
