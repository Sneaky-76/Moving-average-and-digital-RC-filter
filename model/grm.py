def sma_float(x, N=16):
    if N <= 0:
    	raise ValueError("N must be positive!")

    buffer = [0.0] * N
    y = []
    for sample in x:
        buffer.pop(0)
        buffer.append(float(sample))
        y.append(sum(buffer) / N)
    return y

def sma_exact(x, N=16):
    if N <= 0:
    	raise ValueError("N must be positive!")

    shift = N.bit_length() - 1
    buffer = [0] * N
    y = []
    for sample in x:
        buffer.pop(0)
        buffer.append(sample)
        total = sum(buffer)
        y.append(total >> shift)
    return y

def rc_float(x, s=4):
    k = 1.0 / (2**s)
    y = []
    current_y = 0.0
    for sample in x:
        current_y = current_y + k * (sample - current_y)
        y.append(current_y)
    return y

def rc_exact(x, s=4, frac_bits=8):
    y_acc = 0
    y = []
    for sample in x:
        x_scaled = sample << frac_bits
        diff = x_scaled - y_acc
        y_acc = y_acc + (diff >> s)
        y.append(y_acc >> frac_bits)
    return y