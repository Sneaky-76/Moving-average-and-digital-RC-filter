#!/usr/bin/env python3
"""Parse Vivado synthesis utilization and timing reports into summary table."""

import os
import re
import csv
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent


def parse_util(filepath):
    luts, ffs, dsps, brams = 0, 0, 0, 0
    with open(filepath) as f:
        content = f.read()

    m_lut = re.search(r'\|\s*Slice LUTs\*\s*\|\s*(\d+)', content)
    if not m_lut:
        m_lut = re.search(r'\|\s*LUT as Logic\s*\|\s*(\d+)', content)
    if m_lut:
        luts = int(m_lut.group(1))

    m_ff = re.search(r'\|\s*Register as Flip Flop\s*\|\s*(\d+)', content)
    if not m_ff:
        m_ff = re.search(r'\|\s*Slice Registers\s*\|\s*(\d+)', content)
    if m_ff:
        ffs = int(m_ff.group(1))

    m_dsp = re.search(r'\|\s*DSPs\s*\|\s*(\d+)', content)
    if m_dsp:
        dsps = int(m_dsp.group(1))

    m_bram = re.search(r'\|\s*Block RAM Tile\s*\|\s*(\d+)', content)
    if m_bram:
        brams = int(m_bram.group(1))

    return luts, ffs, dsps, brams


def parse_timing(filepath):
    wns = 0.0
    with open(filepath) as f:
        for line in f:
            if "WNS(ns)" in line:
                continue
            m = re.match(r'^\s*(-?\d+\.\d+)', line)
            if m:
                wns = float(m.group(1))
                break
    period = 10.0 - wns
    fmax = 1000.0 / period if period > 0 else 0.0
    return wns, fmax


def main():
    rows = []
    # Parse SMA variants
    for var in ["sma_direct", "sma_recursive"]:
        for n in [8, 16, 32, 64, 128]:
            u_path = RESULTS_DIR / f"{var}_N{n}_utilization.rpt"
            t_path = RESULTS_DIR / f"{var}_N{n}_timing.rpt"
            if u_path.exists() and t_path.exists():
                luts, ffs, dsps, brams = parse_util(u_path)
                wns, fmax = parse_timing(t_path)
                rows.append({
                    "variant": f"{var} (N={n})",
                    "lut": luts,
                    "ff": ffs,
                    "dsp": dsps,
                    "bram": brams,
                    "wns_ns": round(wns, 3),
                    "fmax_mhz": round(fmax, 1),
                    "throughput_msps": round(fmax, 1)  # 1 sample/cycle (II=1)
                })

    # Parse RC filter
    u_rc = RESULTS_DIR / "rc_filter_utilization.rpt"
    t_rc = RESULTS_DIR / "rc_filter_timing.rpt"
    if u_rc.exists() and t_rc.exists():
        luts, ffs, dsps, brams = parse_util(u_rc)
        wns, fmax = parse_timing(t_rc)
        rows.append({
            "variant": "rc_filter (S=4, Q8.8)",
            "lut": luts,
            "ff": ffs,
            "dsp": dsps,
            "bram": brams,
            "wns_ns": round(wns, 3),
            "fmax_mhz": round(fmax, 1),
            "throughput_msps": round(fmax, 1)
        })

    # Save to CSV
    csv_path = RESULTS_DIR / "summary_table.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["variant", "lut", "ff", "dsp", "bram", "wns_ns", "fmax_mhz", "throughput_msps"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved CSV: {csv_path}")

    # Print formatted markdown table
    print("\n| Variant | LUT | FF | DSP | BRAM | WNS [ns] | f_max [MHz] | Throughput [MS/s] |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for r in rows:
        print(f"| {r['variant']} | {r['lut']} | {r['ff']} | {r['dsp']} | {r['bram']} | {r['wns_ns']} | {r['fmax_mhz']} | {r['throughput_msps']} |")


if __name__ == "__main__":
    main()
