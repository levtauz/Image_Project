import numpy as np
import scipy as scp
import math
import numpy as np

def psnr(im_truth, im_test, maxval=255.):
    """
    Staff PSNR function
    """
    mse = np.linalg.norm(im_truth.astype(np.float64) - im_test.astype(np.float64))**2 / np.prod(np.shape(im_truth))
    return 10 * np.log10(maxval ** 2 / mse)
    #max_pixel = np.max(original) * 1.0
    #mse = (np.sum(np.square(np.asarray(original, dtype=np.float) - np.asarray(transmitted, dtype=np.float)))) / (original.size * 1.0)
    #if mse == 0:
    #    return float('inf')
    #psnr_value = 20 * np.log10(float(max_pixel)) - 10 * np.log10(mse)
    #return psnr_value
