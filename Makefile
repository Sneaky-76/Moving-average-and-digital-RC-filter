# ESL 2026/27 – Project A1 Makefile
# Automated end-to-end flow: from golden model to Vivado batch synthesis and live demo

PYTHON ?= /opt/miniconda3/bin/python3.13
PYTEST ?= $(PYTHON) -m pytest
VIVADO ?= /opt/Xilinx/2025.2/Vivado/bin/vivado

.PHONY: all clean sim synth bitstream program tlm demo help

all: sim tlm synth
	@echo "=========================================================="
	@echo "=== Full end-to-end pipeline completed successfully!  ==="
	@echo "=========================================================="

help:
	@echo "ESL 2026/27 Project A1 Build Targets:"
	@echo "  make sim       : Run Cocotb UVM-style verification for all 3 variants"
	@echo "  make tlm       : Run virtual prototype TLM analysis (transfer vs compute)"
	@echo "  make synth     : Run headless batch synthesis across variants & window sizes"
	@echo "  make bitstream : Generate complete bitstream for Digilent Nexys 4 DDR"
	@echo "  make program   : Program Nexys 4 DDR FPGA over JTAG"
	@echo "  make demo      : Launch host-side live real-time visualizer"
	@echo "  make clean     : Remove simulation and synthesis build artifacts"

sim:
	$(PYTEST) hw/verif/ -v

tlm:
	$(PYTHON) model/virtual_tlm.py

synth:
	@if [ -x "$(VIVADO)" ]; then \
		$(VIVADO) -mode batch -nojournal -nolog -source tcl/synth.tcl; \
		$(PYTHON) results/parse_results.py; \
	else \
		echo "Warning: Vivado not found at $(VIVADO). Skipping synthesis."; \
	fi

bitstream:
	@if [ -x "$(VIVADO)" ]; then \
		$(VIVADO) -mode batch -nojournal -nolog -source tcl/build_bitstream.tcl; \
	else \
		echo "Warning: Vivado not found at $(VIVADO). Skipping bitstream generation."; \
	fi

demo:
	$(PYTHON) host/live_demo.py

clean:
	rm -rf hw/verif/sim_build/ hw/build/
	rm -rf results/*.rpt results/*.log results/*.jou results/*.png results/*.csv
	find . -type d -name "__pycache__" -exec rm -rf {} +
