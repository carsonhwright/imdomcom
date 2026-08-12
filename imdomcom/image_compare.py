import cv2 as cv
import numpy as np
from pathlib import Path
from cv2.typing import MatLike

IMAGES_FP = Path(Path.home() / "project-files/images")
OUTPUT = Path(__file__).parent.parent / "output"
GAUSSIAN_KERNEL_SIZE = 7

def main():
    im1 = cv.imread(IMAGES_FP / "image1.png")
    im2 = cv.imread(IMAGES_FP / "image2.png")
    im1 = convert_to_gray(im1)
    im2 = convert_to_gray(im2)
    im1 = crop_image_gui(im1)
    im1, im2 = match_sizes(im1, im2)
    out = diff_img(img1=im1, img2=im2)
    out = gauss_blur(out, GAUSSIAN_KERNEL_SIZE)
    write_im_output("wunk.png", out)
    return out

def gauss_blur(img, ksize:int=5):
    # TODO kernel is 5x5, scale or kernel should be this value
    # kernel = np.ones((ksize,ksize),np.float32)/(ksize**2) # scale squared
    # ret = cv.filter2D(img, cv.CV_8U, kernel)
    ret = cv.GaussianBlur(img, (ksize, ksize), 0)
    return ret
    
def crop_hole(image, interior_frame, exterior_frame):
    """return a cropped version of the image using the exterior frame, and blanking the interior of the image"""

def blank_interior(image, interior_frame):
    """what it sounds like"""

def diff_img(img1, img2):
    diff_img = img1 - img2
    min, max, mean, std_dev = image_stats(diff_img)
    divisor = max - min
    if not divisor:
        norm_diff = np.zeros(diff_img.shape)
    else:
        # NOTE this is the min max method, BUT I'm worried that the autograder is busted
        # it keeps sending zeroes as the input
        norm_diff = ((diff_img-min)/(divisor))*255
    # diff_img = (((diff_img - mean) / std_dev) * 0.05) + mean
    # ret = cv.normalize(diff_img, None, beta=0, alpha=1, norm_type=cv.NORM_MINMAX, dtype=cv.CV_16F)*std_dev + mean
    # ret = np.clip(norm_diff, 0, 255)
    ret = abs(diff_img)
    return ret

def image_stats(image):
    im_min = float(np.min(image))
    im_max = float(np.max(image))
    im_mean = float(np.mean(image))
    # NOTE read docs: https://numpy.org/doc/2.1/reference/generated/numpy.std.html
    im_std = float(np.std(image))
    return im_min, im_max, im_mean, im_std

def convert_to_gray(img):
    ret = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    return ret

def write_im_output(fn, img):
    cv.imwrite(OUTPUT / fn, img)

def crop_image_gui(img):
    x, y, w, h = cv.selectROI("Select Frame", img, fromCenter=False, showCrosshair=True)
    ret = img[int(y):int(y+h), int(x):int(x+w)]
    return ret

def match_sizes(image1:MatLike, image2:MatLike):
    im1_dim = image1.shape
    im2_dim = image2.shape
    breakpoint()

if __name__ == "__main__":
    main()