from PIL import Image
import pytesseract as tess
from functools import reduce
import math

class CaptchaSolver():
	def __init__(self, tesseract_path):
		tess.pytesseract.tesseract_cmd = tesseract_path
	def rgb_to_hsv(self, r, g, b):
		r, g, b = r/255.0, g/255.0, b/255.0
		mx = max(r, g, b)
		mn = min(r, g, b)
		df = mx-mn
		if mx == mn:
			h = 0
		elif mx == r:
			h = (60 * ((g-b)/df) + 360) % 360
		elif mx == g:
			h = (60 * ((b-r)/df) + 120) % 360
		elif mx == b:
			h = (60 * ((r-g)/df) + 240) % 360
		if mx == 0:
			s = 0
		else:
			s = (df/mx)*100
		v = mx*100
		return h, s, v

	def getRGB(self, img, i, j):
		try:
			return img[i, j]
		except:
			return (0, 0, 0)

	def isYellow(self, color):
		hsv = self.rgb_to_hsv(color[0], color[1], color[2])
		if hsv[0] > 31 and hsv[0] < 80:
			return True
		else:
			return False

	def getNeighborPixels(self, img, i, j):
		arr = []
		arr.append(self.getRGB(img, i, j + 1))
		arr.append(self.getRGB(img, i + 1, j))
		arr.append(self.getRGB(img, i - 1, j))
		arr.append(self.getRGB(img, i, j - 1))
		return arr

	def removeYellowLine(self, origImage, img):
		ok = True
		for i in range(origImage.size[0]):
			for j in range(origImage.size[1]):
				if self.isYellow(img[i, j]):
					ok = False

					neighborPixels = self.getNeighborPixels(img, i, j)
					notYellowPixels = list(filter((lambda x: not self.isYellow(x)), neighborPixels))

					if len(notYellowPixels) > 1:
						avgPixel = reduce((lambda  x, y: (x[0] + y[0], x[1] + y[1], x[2] + y[2])), notYellowPixels)
						avgPixel = list(map(lambda x: x // len(notYellowPixels), avgPixel))
						if self.isYellow(avgPixel):
							img[i, j] = (255, 255, 255)
							continue
						else:
							img[i, j] = (avgPixel[0], avgPixel[1], avgPixel[2])

		if not ok:
			self.removeYellowLine(origImage, img)

	def resolve(self, orig_img):
		img = orig_img.load()
		self.removeYellowLine(orig_img, img)
		return tess.image_to_string(orig_img, lang="eng", config="-c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ").lower()
