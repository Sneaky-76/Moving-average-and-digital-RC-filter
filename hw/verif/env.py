from cocotb.triggers import RisingEdge, ReadOnly
from cocotb.queue import Queue 

class FilterDriver:
    def __init__(self, dut, queue: Queue):
        self.dut = dut
        self.queue = queue

    async def run(self):
        while True:
            sample = await self.queue.get()
            self.dut.data_in.value = sample
            self.dut.valid_in.value = 1
            await RisingEdge(self.dut.clk)

            if self.queue.empty():
                self.dut.valid_in.value = 0

class FilterMonitor:
    def __init__(self, dut, queue: Queue):
        self.dut = dut
        self.queue = queue

    async def run(self):
        while True:
            await RisingEdge(self.dut.clk)

            if self.dut.rst_n.value == 1 and self.dut.valid_out.value == 1:
                await self.queue.put(self.dut.data_out.value.to_signed())


import cocotb
from cocotb.clock import Clock

class FilterEnv:
    def __init__(self, dut):
        self.dut = dut
        self.drv_q = Queue()
        self.mon_q = Queue()
        self.driver = FilterDriver(dut, self.drv_q)
        self.monitor = FilterMonitor(dut, self.mon_q)

    async def start(self):
        cocotb.start_soon(Clock(self.dut.clk, 10, unit="ns").start())
        cocotb.start_soon(self.driver.run())
        cocotb.start_soon(self.monitor.run())

    async def reset(self):
        self.dut.valid_in.value = 0
        self.dut.data_in.value = 0
        self.dut.rst_n.value = 0
        for _ in range(5):
            await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)
    
    async def verify(self, input_vector, expected_vector):
        for sample in input_vector:
            await self.drv_q.put(sample)

        actual_output = []
        for _ in range(len(expected_vector)):
            val = await self.mon_q.get()
            actual_output.append(val)

        assert actual_output == expected_vector, (
            f"Mismatch! First failure at: "
            f"{[(i, a, e) for i, (a, e) in enumerate(zip(actual_output, expected_vector)) if a != e][:3]}"
        )