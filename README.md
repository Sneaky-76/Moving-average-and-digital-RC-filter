# ESL 2026/27 – Project A1: Moving Average & Digital RC Filter

Academic project for the *Electronic System Level (ESL) Design* course.  
Course Instructor: dr hab. inż. Maciej Wielgosz  
Project Instructor: Szymon Mazurek  

Target Hardware Platform: **Digilent Nexys 4 DDR** (Xilinx Artix-7 `xc7a100tcsg324-1`).

---

## 1. Project Overview & Objectives

This project implements, rigorously verifies bit-by-bit, synthesizes, and benchmarks fixed-point digital smoothing filters:
1. **Simple Moving Average (SMA)** with window size $N=16$ (power-of-two window allowing division via arithmetic right shift `>> 4`).
2. **Digital First-Order IIR RC Filter** with smoothing factor $k = 2^{-s}$ ($s=4$), eliminating dedicated multipliers.

### Key Engineering Goals
- **Bit-exact Fixed-Point Arithmetic:** Exact accumulator sizing ($W_{acc} = W_{in} + \lceil\log_2 N\rceil = 12$ bits for $W_{in}=8$) to guarantee zero overflow, and an internal $Q8.8$ fixed-point state register in the RC filter to prevent the known right-shift saturation stall (where $x=100, s=4$ would otherwise halt at 85).
- **Architecture Exploration (One change at a time):**
  - **Variant 0 (Baseline):** Direct SMA evaluation ($N$ additions per input sample).
  - **Variant 1:** Recursive SMA running sum ($\text{sum}[n] = \text{sum}[n-1] + x[n] - x[n-N]$), requiring only 2 additions per sample regardless of $N$.
  - **Variant 2:** Single-pole RC filter y[n] = y[n-1] + ((x[n] - y[n-1]) >> s), eliminating the sample history buffer and using only a single internal $Q8.8$ register.
- **Verification Proofs (Replacing "it works"):** Bit-by-bit RTL verification against a Python bit-exact golden model over $10^4$ pseudorandom test vectors (`SEED = 2026`) plus 12 targeted edge-case vectors (step response, unit impulse, signed saturation boundaries, alternating min/max).
- **Virtual Prototype (TLM Cost Model):** Analysis of computation latency vs. I/O bus transfer overhead ($T_{transfer}$ vs $T_{compute}$) to determine the system bottleneck.
- **Live Hardware Demonstration:** Hardware deployment on Nexys 4 DDR with UART streaming and real-time visualization on the host machine (`host/live_demo.py`).

---

## 2. Repository Layout

```text
├── docs/
│   └── report.md           		#7-section engineering report (L07 structure)
├── model/
│   ├── grm.py			     	#python float reference + bit-exact fixed-point model
│   ├── virtual_tlm.py      		#TLM cost model (bus transfer vs compute bottleneck)
│   └── gen_vectors.py      		#test vector generator (SEED=2026, 10^4 random + 12 edge cases)
├── hw/
│   ├── sma_direct.sv       		#variant 0 (baseline direct SMA)
│   ├── sma_recursive.sv    		#variant 1 (recursive running sum SMA)
│   ├── rc_filter.sv        		#variant 2 (digital RC filter with Q8.8 state)
│   ├── uart_receiver.sv    		#UART receiver for hardware live demo
│   ├── uart_tranciver.sv   		#UART transmitter for hardware live demo
│   ├── top.sv    			 		#top-level integration module for Nexys 4 DDR
│   └── nexys4ddr.xdc       		#vivado physical & timing constraints
│   └── verif/
│   	 ├── env.py
│   	 ├── rc_filter_tb.py 		#testbench of RC filter
│   	 ├── sma_direct_tb.py		#testbench of direct SMA
│   	 └── sma_recursive_tb.py 	#testbench of recursive SMA     
├── results/
│   ├── prase_results.py    		#vivado synthesis utilization and timing reports parsed into summary table
│   └── summary_table.csv   		#consolidated benchmarking results (LUT, FF, DSP, fmax, latency)
├── host/
│   └── live_demo.py        		#host-side live visualizer (pyserial + matplotlib animation)
├── Makefile                		#reproducible end-to-end automation target (make all)
├── tcl/
│   ├── build_bitstream.tcl    		#building full bitstream for Nexys 4 DDR
│   ├── program_board.tcl    		#programming Nexys 4 DDR with generated bitstream
│   └── synth.tcl       		#synthesis procedure
└── README.md
```

---

## 3. Quickstart & Reproducibility

The complete pipeline (vector generation, bit-exact verification, TLM evaluation, and Vivado batch synthesis) is reproducible with a single command:

```bash
make all
```

Individual workflow targets:
* `make sim` – Compile and run SystemVerilog simulation and assertions (via `iverilog`).
* `make synth` – Run batch Vivado synthesis for all variants and export utilization/timing reports.
* `make tlm` – Execute virtual prototype TLM model and generate bottleneck plots.
* `make demo` – Run live streaming host demo connected to `/dev/ttyUSB*`.
* `make bitstream` - Generate complete bitstream for Digilent Nexys 4 DDR.
* `make program` - Program Nexys 4 DDR FPGA over JTAG.
* `make demo` - Launch host-side live real-time visualizer.

---

## 4. AI Tools Usage

In accordance with course regulations (§4.4), the use of AI tools in this project is declared below:
* **Tool Used:** Antigravity (AI coding assistant in pair-programming mode) and Google Gemini.
* **Scope of Assistance:**
  - Discussions about mathematical formulation of fixed-point dynamics ($Q8.8$ fractional state sizing, accumulator dynamic range).
  - Scaffolding build automation files (`Makefile`, Vivado batch Tcl scripts).
  - Structuring testbench edge-case fixtures and TLM model templates.
* **Independent Verification:** All RTL implementations, testbenches, and synthesis reports are independently verified via automated bit-by-bit regression tests in simulation and deterministic reports generated by Xilinx Vivado.
