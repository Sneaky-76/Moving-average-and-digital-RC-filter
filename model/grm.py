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
