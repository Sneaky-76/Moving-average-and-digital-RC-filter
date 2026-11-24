from grm import sma_exact, rc_exact

class FilterTLM:
    def __init__(self, filter_func, cycles_per_word=1.0, cycles_per_sample=1.0, c0=0, overlap=False):
        self.filter_func = filter_func
        self.w = cycles_per_word            #modeling data transfer over the bus
        self.c = cycles_per_sample          #modeling filter computation per output sample
        self.c0 = c0
        self.overlap = overlap

    def run_transaction(self, x):
        y = self.filter_func(x)

        t_transfer = (len(x) + len(y)) * self.w
        t_compute = len(y) * self.c + self.c0

        if self.overlap:
            t_total = max(t_transfer, t_compute)
        else:
            t_total = t_transfer + t_compute

        return {
            "result": y,
            "t_transfer": t_transfer,
            "t_compute": t_compute,
            "t_total": t_total,
            "transfer_share_pct": (t_transfer / t_total) * 100.0
        }


if __name__ == "__main__":
    xb = [42] * 1024

    baud = 115200
    clk = 100_000_000
    frame_size = 10
    uart_cpw = frame_size / baud * clk

    print(f"UART CPW: {uart_cpw} clock cycles (cc) per word")

    tlm_rc_uart = FilterTLM(rc_exact, cycles_per_word=uart_cpw, cycles_per_sample=1)
    res_rc_uart = tlm_rc_uart.run_transaction(xb)
    print(f"Transfer: {res_rc_uart.get("t_transfer")} cc; Compute: {res_rc_uart.get("t_compute")} cc; Total: {res_rc_uart.get("t_total")} cc")

    tlm_sma_uart = FilterTLM(sma_exact, cycles_per_word=uart_cpw, cycles_per_sample=1)
    res_sma_uart = tlm_sma_uart.run_transaction(xb)
    print(f"Transfer: {res_sma_uart.get("t_transfer")} cc; Compute: {res_sma_uart.get("t_compute")} cc; Total: {res_sma_uart.get("t_total")} cc")

    tlm_rc_axi = FilterTLM(rc_exact, cycles_per_word=1.0, cycles_per_sample=1)
    res_rc_axi = tlm_rc_axi.run_transaction(xb)
    print(f"Transfer: {res_rc_axi.get("t_transfer")} cc; Compute: {res_rc_axi.get("t_compute")} cc; Total: {res_rc_axi.get("t_total")} cc")

    tlm_sma_axi = FilterTLM(sma_exact, cycles_per_word=1.0, cycles_per_sample=1)
    res_sma_axi = tlm_sma_axi.run_transaction(xb)
    print(f"Transfer: {res_sma_axi.get("t_transfer")} cc; Compute: {res_sma_axi.get("t_compute")} cc; Total: {res_sma_axi.get("t_total")} cc")

    tlm_rc_pipe = FilterTLM(rc_exact, cycles_per_word=1.0, cycles_per_sample=1, overlap=True)
    res_rc_pipe = tlm_rc_pipe.run_transaction(xb)
    print(f"Transfer: {res_rc_pipe.get("t_transfer")} cc; Compute: {res_rc_pipe.get("t_compute")} cc; Total: {res_rc_pipe.get("t_total")} cc")

    tlm_sma_pipe = FilterTLM(sma_exact, cycles_per_word=1.0, cycles_per_sample=1, overlap=True)
    res_sma_pipe = tlm_sma_pipe.run_transaction(xb)
    print(f"Transfer: {res_sma_pipe.get("t_transfer")} cc; Compute: {res_sma_pipe.get("t_compute")} cc; Total: {res_sma_pipe.get("t_total")} cc")