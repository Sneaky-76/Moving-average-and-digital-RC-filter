# ESL 2026/27 – Project Report: Topic A1
## Moving Average & Digital RC Filter

**Authors:** Łukasz Kmiecik, Paweł Ścibek, Wiktor Rogowski 
**Repository:** https://github.com/Sneaky-76/Moving-average-and-digital-RC-filter.git
**Evaluation Tag:** `git tag final`  
**Target Device:** Xilinx Artix-7 `xc7a100tcsg324-1` (Digilent Nexys 4 DDR)

---

### 1. Specification and Criteria
*Question: What was to be built and by what criteria should it be evaluated?*

* **Functionality:** 
  * Simple Moving Average (SMA) filter with window $N = 16$.
  * First-order digital recursive RC/IIR filter: $y[n] = y[n-1] + k(x[n] - y[n-1])$ with $k = 2^{-s}$ ($s = 4$).
* **Interfaces & Formats:**
  * Input data: 8-bit signed integer (`int8` $\in [-128, 127]$).
  * Output data: 8-bit signed integer.
  * Internal accumulator / registers: sized to guarantee zero mathematical overflow under all possible inputs.
* **Performance Requirements:**
  * Throughput: $\ge 50$ MSamples/s @ $100\text{ MHz}$ clock.
  * Latency: Minimal pipeline latency ($\le 2$ cycles per sample).
* **Evaluation Criteria Ranking (in order of importance):**
  1. Functional correctness: bit-exact match against bit-level model.
  2. Hardware efficiency: minimal resource consumption (LUTs, FFs, DSPs, BRAM).
  3. Maximum achievable clock frequency ($f_{max}$) and throughput.
  4. Architectural scalability (cost of increasing $N$ vs increasing $s$).

---

### 2. Reference Model and Tests
*Question: What does "correct" mean?*

* **Comparison Definition & Tolerance:**
  * Bit-exact model vs. float reference: tolerance $\epsilon = \Delta_{out}/2 = 0.5$ LSB for truncation/rounding analysis.
  * RTL vs. Bit-exact model: strictly **bit-by-bit identical** ($\text{assert } y_{hw} === y_{ref}$).
* **Test Vectors:**
  * Deterministic seed: `SEED = 2026`.
  * Pseudorandom vector: $10^4$ samples drawn uniformly from $[-128, 127]$.
  * 12 Edge-case vectors:
    1. Zero input stream ($x=0$)
    2. Maximum positive step ($0 \to 100$) – verifies RC settling without truncation stall
    3. Negative step ($0 \to -100$)
    4. Full-scale positive saturation ($x = +127$)
    5. Full-scale negative saturation ($x = -128$)
    6. Unit positive impulse ($x = [100, 0, 0, \dots]$)
    7. Unit negative impulse ($x = [-100, 0, 0, \dots]$)
    8. Alternating extreme oscillation ($+127, -128, +127, -128, \dots$)
    9. Small alternating oscillation ($2, -2, 2, -2, \dots$)
    10. Ramp up ($-128 \to +127$)
    11. Ramp down ($+127 \to -128$)
    12. Pulse burst (short high-frequency packet)

---

### 3. Architecture
*Question: What was built?*

* **Host-to-Accelerator Interface:** Streaming interface (`sample_in`, `valid_in`, `ready_out`, `sample_out`, `valid_out`).
* **Accumulator Dynamic Range Proof:**
  * For SMA with $N=16$ and 8-bit signed input $[-128, 127]$:
    $$\text{Worst-case sum} = 16 \times (-128) = -2048$$
    $$\text{Worst-case sum} = 16 \times 127 = 2032$$
    Required bits: $W_{acc} = W_{in} + \lceil\log_2 N\rceil = 8 + 4 = 12$ bits (signed).
* **RC Filter State Register ($Q8.8$ format):**
  * To eliminate the right-shift truncation error where $(x - y) \gg 4 = 0$ prematurely (e.g. at $x=100, y=85 \implies 100-85 = 15 \implies 15 \gg 4 = 0$), the internal state register $y_{acc}$ is represented in $Q8.8$ fixed-point format (16 bits signed: 8 integer bits, 8 fractional bits).
  * State update:
    $$y_{acc}[n] = y_{acc}[n-1] + \left( (x[n] \ll 8) - y_{acc}[n-1] \right) \gg s$$
  * Final output is extracted as $y[n] = y_{acc}[n][15:8]$.

---

### 4. Explored Variants
*Question: What alternatives were evaluated, and why was the final choice made?*

* **Variant 0 (Baseline): Direct SMA**
  * Architecture: $N$-element shift register buffer; all $N$ tap values are summed using an adder tree/chain every clock cycle.
  * Computational cost: $N$ additions per sample.
* **Variant 1: Recursive Running Sum SMA**
  * Architecture: Circular buffer / shift register of length $N$; maintains running accumulator:
    $$\text{sum}[n] = \text{sum}[n-1] + x[n] - x[n-N]$$
  * Single design decision changed: transformed tapped-delay adder tree into a constant 2-addition recursive update.
  * Computational cost: 2 additions per sample, completely independent of $N$.
* **Variant 2: Digital RC / IIR Filter**
  * Architecture: Eliminates the entire sample history buffer; maintains a single 16-bit $Q8.8$ state register.
  * Single design decision changed: replaced moving window memory with recursive exponential decay state.
  * Computational cost: 1 subtraction, 1 arithmetic shift, 1 addition per sample.

---

### 5. Verification Proofs
*Question: How do we know each variant actually works?*

* **Proof Sentence for Variant 0:**
  > *`tb_sma_direct` passes in RTL simulation, bit-by-bit identical to the bit-exact Python model, for $10^4$ random vectors (`SEED = 2026`) and 12 targeted edge-case scenarios.*
* **Proof Sentence for Variant 1:**
  > *`tb_sma_recursive` passes in RTL simulation, bit-by-bit identical to the bit-exact Python model, for $10^4$ random vectors (`SEED = 2026`) and 12 targeted edge-case scenarios.*
* **Proof Sentence for Variant 2:**
  > *`tb_rc_filter` passes in RTL simulation, bit-by-bit identical to the bit-exact Python model, for $10^4$ random vectors (`SEED = 2026`) and 12 targeted edge-case scenarios, confirming full settling on step responses with zero truncation stall.*

---

### 6. Results against Baseline
*Question: How much better is it, and against what?*

#### Synthesis Benchmarking Table (Artix-7 `xc7a100tcsg324-1`)

| Variant | Architecture Change | Test Status | Cycles / Sample | LUT | FF | DSP | BRAM | $f_{max}$ [MHz] | Throughput [MS/s] | Error vs Float (MSE) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0 (Baseline)** | Direct SMA ($N=16$) | PASS (bit-exact) | 1 | 94 | 129 | 0 | 0 | 127.6 | 127.6 | 0.3052 |
| **1** | Recursive SMA ($N=16$) | PASS (bit-exact) | 1 | 25 | 44 | 0 | 0 | 296.6 | 296.6 | 0.3052 |
| **2** | RC Filter ($s=4, Q8.8$) | PASS (bit-exact) | 1 | 49 | 25 | 0 | 0 | 242.6 | 242.6 | 0.3589 |

#### Architectural Scaling across Window Sizes $N$

| Module | Window $N$ | LUT | FF | WNS [ns] | $f_{max}$ [MHz] | Throughput [MS/s] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `sma_direct` | 8 | 49 | 65 | +4.055 | 168.2 | 168.2 |
| `sma_direct` | 16 | 94 | 129 | +2.164 | 127.6 | 127.6 |
| `sma_direct` | 32 | 185 | 257 | +1.386 | 116.1 | 116.1 |
| `sma_direct` | 64 | 376 | 513 | -0.731 | 93.2 | 93.2 |
| `sma_direct` | 128 | 757 | 1025 | -2.555 | 79.6 | 79.6 |
| `sma_recursive` | 8 | 24 | 35 | +6.628 | 296.6 | 296.6 |
| `sma_recursive` | 16 | 25 | 44 | +6.628 | 296.6 | 296.6 |
| `sma_recursive` | 32 | 26 | 61 | +6.616 | 295.5 | 295.5 |
| `sma_recursive` | 64 | 35 | 94 | +6.511 | 286.6 | 286.6 |
| `sma_recursive` | 128 | 52 | 159 | +6.511 | 286.6 | 286.6 |
| `rc_filter` | $s=4$ | 49 | 25 | +5.878 | 242.6 | 242.6 |

*(Extracted automatically via `cl/synth.tcl` and `results/parse_results.py` from Vivado synthesis reports)*

#### Virtual Prototype TLM Analysis (Transfer vs Computation)
* *Key finding:* At an arithmetic intensity of $\le 2$ operations per sample, computation completes in 1 clock cycle (10 ns @ 100 MHz). Transferring samples over UART (115200 baud) requires $\approx 87\,\mu\text{s}$ per byte, accounting for $>99.9\%$ of end-to-end execution time. Denser compute architectures beyond Variant 1 provide zero system-level speedup without upgrading to high-throughput DMA / PCIe streaming.

---

### 7. Limitations and Next Steps
*Question: Under what conditions do these conclusions hold, and what is the next iteration?*

* **Operating Assumptions & Limits:**
  * Power-of-two window size ($N = 2^k$) is assumed; non-power-of-two windows require integer division or multipliers.
  * Input is constrained to 8-bit signed (`int8`). For 16-bit or 24-bit audio signals, accumulator and internal state widths must scale accordingly.
* **Next Iteration Roadmap:**
  * Multi-channel time-division multiplexing (TDM) processing through a single RC filter engine.
  * Cascaded second-order IIR sections (biquads) for steeper cutoff slopes.
  * AXI4-Stream interface with Scatter-Gather DMA for high-bandwidth host streaming.
