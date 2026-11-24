#!/usr/bin/env python3
"""
ESL 2026/27 - Project A1: Live Hardware Demonstration Host Interface
Connects to Digilent Nexys 4 DDR over USB-UART and visualizes filtering in real time.
"""

import sys
import glob
import time
import math
import random
import argparse
from collections import deque

import serial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def find_serial_port():
    """Auto-detect available USB serial ports on Linux."""
    ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    if not ports:
        return None
    # On Digilent boards with FT2232, the second channel (index 1) is usually the UART
    if len(ports) >= 2:
        return ports[1]
    return ports[0]


class LiveFilterDemo:
    def __init__(self, port, baud=115200, buffer_len=200, mock=False):
        self.port_name = port
        self.baud = baud
        self.buffer_len = buffer_len
        self.mock = mock

        self.ser = None
        if not self.mock:
            try:
                self.ser = serial.Serial(self.port_name, self.baud, timeout=0.1)
                print(f"[DEMO] Connected to FPGA on {self.port_name} @ {self.baud} baud")
            except Exception as e:
                print(f"[ERROR] Could not open {self.port_name}: {e}")
                print("[INFO] Falling back to MOCK mode (simulated RC filter).")
                self.mock = True

        # Ring buffers for live plotting
        self.x_data = deque(maxlen=self.buffer_len)
        self.raw_data = deque(maxlen=self.buffer_len)
        self.filtered_data = deque(maxlen=self.buffer_len)

        for i in range(self.buffer_len):
            self.x_data.append(i)
            self.raw_data.append(0)
            self.filtered_data.append(0)

        self.sample_idx = 0
        self.mock_y_acc = 0

    def generate_next_sample(self):
        """Generates a noisy signal composed of a periodic step and Gaussian noise."""
        t = self.sample_idx

        # Square wave with period 100 samples (switches between -60 and +60)
        base = 60 if (t % 100) < 50 else -60

        # High-frequency noise
        noise = random.randint(-20, 20)

        # Clamped to signed 8-bit range [-128, 127]
        sample = max(-128, min(127, base + noise))
        self.sample_idx += 1
        return sample

    def process_sample(self, raw_sample):
        """Sends 1 sample to FPGA over UART and reads back filtered result."""
        # Convert signed int8 to unsigned byte for UART
        byte_to_send = raw_sample & 0xFF

        if self.mock or not self.ser:
            # Software mock of RC filter (S=4, Q8.8)
            x_scaled = raw_sample << 8
            diff = x_scaled - self.mock_y_acc
            self.mock_y_acc += (diff >> 4)
            return self.mock_y_acc >> 8

        # 1. Send sample to Nexys 4 DDR
        self.ser.write(bytes([byte_to_send]))

        # 2. Read filtered sample back from Nexys 4 DDR
        rx_bytes = self.ser.read(1)
        if rx_bytes:
            # Convert unsigned byte back to signed int8
            filtered = int.from_bytes(rx_bytes, byteorder="big", signed=True)
            return filtered
        return raw_sample

    def update_frame(self, frame_num, line_raw, line_filt, text_info):
        """Animation callback: processes new samples and updates matplotlib lines."""
        # Process a small burst of samples per display frame for smooth streaming
        burst_size = 4
        for _ in range(burst_size):
            raw = self.generate_next_sample()
            filt = self.process_sample(raw)

            self.raw_data.append(raw)
            self.filtered_data.append(filt)

        line_raw.set_ydata(self.raw_data)
        line_filt.set_ydata(self.filtered_data)

        status_str = f"Port: {'MOCK (No FPGA)' if self.mock else self.port_name} | Baud: {self.baud}\n" \
                     f"Nexys 4 DDR SW[1:0]: 00=Bypass | 01=SMA Direct | 10=SMA Recursive | 11=RC Filter"
        text_info.set_text(status_str)
        return line_raw, line_filt, text_info

    def run(self):
        """Starts live animated visualization."""
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.canvas.manager.set_window_title("ESL 2026/27 – FPGA Hardware Live Demo (Nexys 4 DDR)")

        ax.set_ylim(-140, 140)
        ax.set_xlim(0, self.buffer_len)
        ax.set_xlabel("Sample Index n", fontsize=11)
        ax.set_ylabel("Signal Amplitude (int8)", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)

        line_raw, = ax.plot(self.x_data, self.raw_data, color="gray", alpha=0.6, label="Raw Input (from Host)")
        line_filt, = ax.plot(self.x_data, self.filtered_data, color="dodgerblue", linewidth=2.2, label="Filtered Output (from Nexys 4 DDR)")

        ax.legend(loc="upper right", framealpha=0.9)

        text_info = ax.text(0.02, 0.95, "", transform=ax.transAxes, fontsize=10,
                            verticalalignment="top", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

        ax.set_title("Real-Time Digital Smoothing on Digilent Nexys 4 DDR", fontsize=13, fontweight="bold")

        ani = animation.FuncAnimation(
            fig,
            self.update_frame,
            fargs=(line_raw, line_filt, text_info),
            interval=30,
            blit=False
        )

        plt.tight_layout()
        plt.show()

        if self.ser:
            self.ser.close()


def main():
    parser = argparse.ArgumentParser(description="Live Demo visualizer for ESL Project A1 on Nexys 4 DDR")
    parser.add_argument("--port", type=str, default=None, help="Serial port (default: auto-detect /dev/ttyUSB*)")
    parser.add_argument("--baud", type=int, default=115200, help="UART Baudrate (default: 115200)")
    parser.add_argument("--mock", action="store_true", help="Run without FPGA board in software mock mode")
    args = parser.parse_args()

    port = args.port or find_serial_port() or "/dev/ttyUSB1"
    demo = LiveFilterDemo(port=port, baud=args.baud, mock=args.mock)
    demo.run()


if __name__ == "__main__":
    main()
