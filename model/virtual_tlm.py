from grm import sma_exact, rc_exact

class FilterTLM:
    def __init__(self, filter_func, words_per_cycle=1.0, cycles_per_sample=1.0, c0=0, overlap=False):
        self.filter_func = filter_func
        self.w = words_per_cycle
        self.c = cycles_per_sample
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
