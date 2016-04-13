import numpy as np
import scipy as scp
import math
from quant_tables import *
from scipy.fftpack import idct
from skimage.color import rgb2lab, lab2rgb   

def zeropad_image(V):
    def roundup(x):
        return int(math.ceil(x * 1.0 / 8)) * 8
    rows, cols = roundup(V.shape[0]), roundup(V.shape[1])
    zeros = np.zeros((rows, cols, 3), dtype='uint8')
    zeros[:V.shape[0], :V.shape[1], :] = V
    return zeros

def block_image(V):
    l = []
    for i in np.arange(0,V.shape[0], 8):
        for j in np.arange(0, V.shape[1], 8):
            l.append(V[i:i+8, j:j+8, :])
    return np.array(l)

def dct_2d(X):
    return dct(dct(X, axis=1), axis=2)

def dct_all(X):
    blocks = block_image(X)
    return dct_2d(blocks)

def quantize(DCT_coeffs, q):
    DCT_coeffs = DCT_coeffs.copy()
    def a(q):
        assert q in range(1,101)
        if q in range(1, 51):
            return 50.0/q
        else:
            return 2-q*1.0/50
    alpha = a(q)
    
    DCT_coeffs[:,:,:,0] = np.round(DCT_coeffs[:,:,:,0]*1.0/(alpha*luminance_table))
    DCT_coeffs[:,:,:,1] = np.round(DCT_coeffs[:,:,:,1]*1.0/(alpha*chrominance_table))
    DCT_coeffs[:,:,:,2] = np.round(DCT_coeffs[:,:,:,2]*1.0/(alpha*chrominance_table))
    
    return DCT_coeffs

def JPEG_compression(image, quality = 50):
    """
    Takes in an RGB image and applys the JPEG compression algorithm
    Steps:
    -Preprocessing
    -DCT
    -Quantinization
    
    Input:
    quality- determines the amount of lossy compression 
    
    Output:
    Numpy array of 8x8 blocks for each channel
    [number of blocks, 8,8,3]
    """
    #Prepocessing
    im = zeropad_image(image)
    im = rgb2lab(O)
    im[:,:,[1,2]] += 128
    #Blocked into 8x8 blocks and apply DCT
    im_dct = dct_all(O)
    #Quantize
    im_q = quantize(im_dct,quality)
    return im_q
