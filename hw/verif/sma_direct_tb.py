import os
import sys
from pathlib import Path
import logging

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cocotb
from cocotb.triggers import Timer, RisingEdge, ReadOnly
from cocotb.clock import Clock
from cocotb_tools.runner import get_runner

from model.gen_vect import gen_rand_vects, gen_edge_vects
from model.grm import sma_exact

from hw.verif.env import FilterEnv

@cocotb.test()
async def sma_direct_test(dut):
    log = logging.getLogger("cocotb.test")
    log.info("Starting simulation...")

    env = FilterEnv(dut)
    await env.start()

    for name, vector in gen_edge_vects().items():
        log.info(f"Running: {name} (len={len(vector)})")
        await env.reset()
        expected = sma_exact(vector)
        await env.verify(vector, expected)

    await env.reset()
    rand_vec = gen_rand_vects(SEED=2026)
    expected_rand = sma_exact(rand_vec)
    await env.verify(rand_vec, expected_rand)





def test_run():
    sim = os.getenv("SIM", "icarus")

    proj_path = Path(__file__).resolve().parent
    sources = [ROOT / "hw" / "sma_direct.sv"]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="sma_direct",
        build_args=["-g2012"],
        timescale=("1ns", "1ps"),
        always=True,
        build_dir=proj_path / "sim_build",
    )

    runner.test(
        hdl_toplevel="sma_direct",
        test_module="sma_direct_tb",
        test_dir=proj_path,
        build_dir=proj_path / "sim_build",
        results_xml=str(proj_path / "sim_build" / "results.xml"),
        timescale=("1ns", "1ps"),
    )



if __name__ == "__main__":
    test_run()
