import numpy as np
import scipy as scp
import math
import numpy as np

def psnr(original, transmitted):
    max_pixel = np.max(original) * 1.0
    mse = (np.sum(np.square(np.asarray(original, dtype=np.float) - np.asarray(transmitted, dtype=np.float)))) / (original.size * 1.0)
    if mse == 0:
        return float('inf')
    psnr_value = 20 * np.log10(float(max_pixel)) - 10 * np.log10(mse)
    return psnr_value
