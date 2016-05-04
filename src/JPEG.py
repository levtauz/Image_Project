import numpy as np
import scipy as scp
from scipy import misc
import math
from quant_tables import *
from scipy.fftpack import idct, dct
from skimage.color import rgb2lab, lab2rgb
from bitarray import bitarray
import utils
import gzip

import sys
import os

#Debug
import pdb
import matplotlib.pyplot as plt

#Compression
def zero_pad_image(V):
	def roundup(x):
		return int(math.ceil(x * 1.0 / 8)) * 8
	rows, cols = roundup(V.shape[0]), roundup(V.shape[1])
	zeros = np.zeros((rows, cols, 3), dtype='uint8')
	zeros[:V.shape[0], :V.shape[1], :] = V
	return zeros

def reflect_pad_image(V):
	def roundup(x):
		return int(math.ceil(x * 1.0 / 8)) * 8
	rows, cols = roundup(V.shape[0]) - V.shape[0], roundup(V.shape[1]) - V.shape[1]
	shape = ((0,rows), (0,cols), (0,0))
	return np.pad(V,shape,mode = "reflect")

def constant_pad_image(V):
	def roundup(x):
		return int(math.ceil(x * 1.0 / 8)) * 8
	rows, cols = roundup(V.shape[0]) - V.shape[0], roundup(V.shape[1]) - V.shape[1]
	shape = ((0,rows), (0,cols), (0,0))
	return np.pad(V,shape,mode = "edge")

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
		assert q in range(1,100),"quality not in [1,100), q = {0}".format(q)
		if q in range(1, 51):
			return 50.0/q
		else:
			return 2-q*1.0/50
	alpha = a(q)

	DCT_coeffs[:,:,:,0] = np.round(DCT_coeffs[:,:,:,0]*1.0/(alpha*luminance_table))
	DCT_coeffs[:,:,:,1] = np.round(DCT_coeffs[:,:,:,1]*1.0/(alpha*chrominance_table))
	DCT_coeffs[:,:,:,2] = np.round(DCT_coeffs[:,:,:,2]*1.0/(alpha*chrominance_table))

	return DCT_coeffs

def zigzag(img):
	"""
	assumes 8x8x3 np array.
	traverse in zig-zag order.
	"""
	vector = np.empty(img.shape[0] * img.shape[1] * img.shape[2])
	indexorder = sorted(((y, x) for y in xrange(img.shape[0]) for x in xrange(img.shape[1])), \
			key = lambda (y,x): (y+x, -x if (y+x) % 2 else x) )
	#print indexorder
	for i, idx in enumerate(indexorder):
		y, x = idx
		vector[3*i:3*i+3] = img[y, x, :]
	return vector

def zigzag_blocks(img):
	"""
	shape is Mx8x8xC
	where M is number of 8x8 dft blocks
	"""
	num_blocks = img.shape[0]
	nz = img.shape[3]
	vector = np.empty(img.shape[0] * img.shape[1] * img.shape[2] * img.shape[3])
	indexorder = sorted(((y, x) for y in xrange(8) for x in xrange(8)), \
			key = lambda (y,x): (y+x, -x if (y+x) % 2 else x) )
	counter = 0
	for i, idx in enumerate(indexorder):
		y, x = idx
		for j in xrange(img.shape[0]):
			vector[3*counter:3*counter+3] = img[j, y, x, :]
			counter += 1
	return vector

def zigzag_full(img):
	"""
	assumes image is NxNx3 where N mod 8 == 0
	traverse in zig-zag order
	"""
	ny = img.shape[0] / 8
	nx = img.shape[1] / 8
	nz = img.shape[2]
	vector = np.empty(img.shape[0] * img.shape[1] * img.shape[2])
	indexorder = sorted(((y, x) for y in xrange(8) for x in xrange(8)), \
			key = lambda (y,x): (y+x, -x if (y+x) % 2 else x) )
	counter = 0
	for i, idx in enumerate(indexorder):
		y, x = idx
		for y_i in xrange(ny):
			for x_i in xrange(nx):
				new_y = 8 * y_i + y
				new_x = 8 * x_i + x
				vector[nz*counter:nz*counter+nz] = img[new_y, new_x, :]
				counter += 1
	return vector

def zigzag_decode(vec, height, width, channels=3):
	rdup = lambda x: int(math.ceil(x * 1.0 / 8)) * 8
	r_height = rdup(height)
	r_width = rdup(width)
	ny = r_height/8
	nx = r_width/8
	num_blocks = r_height * r_width / 64
	img = np.empty((num_blocks,8,8,channels))
	indexorder = sorted(((y, x) for y in xrange(8) for x in xrange(8)), \
			key = lambda (y,x): (y+x, -x if (y+x) % 2 else x) )
	counter = 0
	for i, idx in enumerate(indexorder):
		y, x = idx
		for j in xrange(img.shape[0]):
			img[j, y, x, :] = vec[3*counter:3*counter+3]
			counter += 1
	return img

#Decompression

def idct_2d(X):
	return idct(idct(X, axis=1), axis=2) * 1.0/256

def unblock_image(X,height, width):
	def roundup(x):
		return int(math.ceil(x * 1.0 / 8)) * 8
	height, width = roundup(height), roundup(width)
	result = np.zeros((height,width,3))
	n = 0
	for i in np.arange(0,height, 8):
		for j in np.arange(0, width, 8):
			result[i:i+8,j:j+8,:] = X[n]
			n += 1
	return result

def unquantize(X,q):
	X = X.copy()
	def a(q):
		assert q in range(1,101)
		if q in range(1, 51):
			return 50.0/q
		else:
			return 2-q*1.0/50
	alpha = a(q)

	X[:,:,:,0] = np.round(X[:,:,:,0]*(alpha*luminance_table))
	X[:,:,:,1] = np.round(X[:,:,:,1]*(alpha*chrominance_table))
	X[:,:,:,2] = np.round(X[:,:,:,2]*(alpha*chrominance_table))

	return X

def JPEG_compression(image, quality = 50,downsample = 1):
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

	#DownSampling
	im_d = utils.downsample(image, downsample)

	#Pading to make 8x8 blocks
	im_pad = reflect_pad_image(im_d)

	#YCbCr
	im_yc = rgb2lab(im_pad)

	#Offset
	im_yc[:,:,[1,2]] += 128

	#Blocked into 8x8 blocks and apply DCT
	im_dct = dct_all(im_yc)
	#Quantize
	im_q = quantize(im_dct,quality)
	im_vec = zigzag_blocks(im_q)
	#Add Meta Data
	im_vec = np.append(im_vec,(im_d.shape[1],im_d.shape[0],quality,image.shape[1],image.shape[0]))
	return im_vec.astype(np.int32)


def JPEG_decompression(data, channels=3):
	#Meta Data
	height = data[-1]
	width = data[-2]
	quality = data[-3]
	d_height = data[-4]
	d_width = data[-5]

	#Remove Meta Data
	data = data[:-5]
	#Unzigzag
	data_z = zigzag_decode(data, d_height, d_width, channels)
	#Unquantize
	im_q = unquantize(data_z,quality)
	#IDCT
	im_idct = idct_2d(im_q)
	#Unblock and Unpad
	im = unblock_image(im_idct,d_height,d_width)
	#Upsample

	#Undo offset and return to RGB
	im[:,:,[1,2]] -= 128
	im = lab2rgb(im) * 255 # lab2rgb converts to float64
	#Undo Padding
	im = im[:d_height,:d_width] 

	#Upsample
	im = utils.upsample(im,(height,width))

	return im.astype(np.uint8)

def main():
	assert len(sys.argv) == 4, "Need the filename of image to compress and quality amount"
	fname = sys.argv[1]
	quality = int(sys.argv[2])
	downsample = int(sys.argv[3])
	image = misc.imread(fname)
	data = JPEG_compression(image,quality,downsample) 
	utils.save_to_gzip(data,fname)
	print("Original File Size = {0} B".format(utils.get_file_size(fname)))
	print("New File Size = {0} B".format(utils.get_file_size(fname + ".gz")))

	#Load File
	data2 = utils.gzip_to_data(fname + ".gz")

	im2 = JPEG_decompression(data2)
	print("PSNR = {0}".format(utils.psnr(image,im2)))

if __name__ == "__main__":
	main()
