import random

def gen_rand_vects(SEED=2026, count=10**4):
    rng = random.Random(SEED)
    return [rng.randint(-128, 127) for _ in range(count)]

def gen_edge_vects():
    cases = {
        "zeros": [0] * 32,
        "max_positive": [127] *32,
        "max_negative": [-128] * 32,
        "step_pos_100": [0] * 16 + [100] * 64,
        "step_neg_100": [0] * 16 + [-100] * 64,
        "impulse_pos": [100] + [0] * 31,
        "impulse_neg": [-100] + [0] * 31,
        "nyquist_oscilation": [127, -128] * 16,
        "small_oscillation": [2, -2] * 16,
        "ramp_up": list(range(-128, 128, 1)),
        "ramp_down": list(range(127, -129, -1)),
        "pulse": ([100] * 16 + [-100] * 16) * 4
    }
    return cases