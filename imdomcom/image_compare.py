import cv2 as cv
import numpy as np
from pathlib import Path
from cv2.typing import MatLike
import argparse

IMAGES_FP = Path(Path.home() / "project-files/images")
OUTPUT = Path(__file__).parent.parent / "output"
GAUSSIAN_KERNEL_SIZE = 15

def setup_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("first_image", help="Image that image 2 will be compared to")
    parser.add_argument("second_image", help="Image that image 1 will be compared to")
    args = parser.parse_args()
    return args

def main(img1=IMAGES_FP / "image1.png", img2=IMAGES_FP / "image2.png"):
    im1 = cv.imread(img1)
    im2 = cv.imread(img2)
    im1 = convert_to_gray(im1)
    im2 = convert_to_gray(im2)
    im1 = crop_image_gui(im1)
    x, y, w, h = align_frame_gui(im1, im2)
    im2 = im2[y:y+h, x:x+w]
    out = diff_img(img1=im1, img2=im2)
    out = gauss_blur(out, GAUSSIAN_KERNEL_SIZE)
    write_im_output("wunk.png", out)
    return out

def gauss_blur(img, ksize:int=5):
    # TODO kernel is 5x5, scale or kernel should be this value
    # kernel = np.ones((ksize,ksize),np.float32)/(ksize**2) # scale squared
    # ret = cv.filter2D(img, cv.CV_8U, kernel)
    # Convert to CV_32F for Gaussian blur if needed
    img_32f = img.astype(np.float32) if img.dtype == np.float16 else img
    ret = cv.GaussianBlur(img_32f, (ksize, ksize), 0)
    return ret
    
def remove_thin_lines(img, kernel_size=3, dark_lines=False):
    """
    Erase thin line-like artifacts (anything no thicker than kernel_size px)
    from img via a morphological close/open pass, leaving larger features
    intact.

    dark_lines=True removes lines darker than their surroundings (closing,
    e.g. scratches/grid lines on a lighter background); set False to remove
    lines brighter than their surroundings (opening) instead.
    """
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (kernel_size, kernel_size))
    op = cv.MORPH_CLOSE if dark_lines else cv.MORPH_OPEN
    ret = cv.morphologyEx(img, op, kernel)
    return ret

def crop_hole(image, interior_frame, exterior_frame):
    """return a cropped version of the image using the exterior frame, and blanking the interior of the image"""

def blank_interior(image, interior_frame):
    """what it sounds like"""

def diff_img(img1, img2):
    # Normalize both images to [0, 255] range before subtracting
    img1_norm = cv.normalize(img1.astype(np.float32), None, alpha=0, beta=255, norm_type=cv.NORM_MINMAX)
    img2_norm = cv.normalize(img2.astype(np.float32), None, alpha=0, beta=255, norm_type=cv.NORM_MINMAX)

    diff_img = img1_norm - img2_norm
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
    # ret = median_filter(ret, GAUSSIAN_KERNEL_SIZE)
    ret = threshold_noise(ret, 20)
    # ret = bilateral_filter(ret)
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

def median_filter(img, ksize=5):
    return cv.medianBlur(img.astype(np.uint8), ksize)

def threshold_noise(img, threshold=10):
    img[img < threshold] = 0
    return img

def bilateral_filter(img, d=9, sigma_color=75, sigma_space=75):
    return cv.bilateralFilter(img.astype(np.uint8), d, sigma_color, sigma_space)

def write_im_output(fn, img):
    cv.imwrite(OUTPUT / fn, img)

def select_roi_gui(img, window_name="Select Frame"):
    """Let the user draw a rectangle on img. Returns (x, y, w, h)."""
    x, y, w, h = cv.selectROI(window_name, img, fromCenter=False, showCrosshair=True)
    cv.destroyWindow(window_name)
    return int(x), int(y), int(w), int(h)

def crop_image_gui(img):
    x, y, w, h = select_roi_gui(img)
    return img[y:y+h, x:x+w]

def align_frame_gui(patch, target_img, alpha=0.5, window_name="Align Frame"):
    """
    Overlay a translucent copy of `patch` (same size) on top of target_img and
    let the user drag it into place, so the corresponding region of
    target_img can be cropped to match.

    Controls: drag with the left mouse button, or nudge with W/A/S/D.
    Enter/Space confirms the current position, Esc cancels (keeps the
    starting position, which is centered on target_img).

    Returns (x, y, w, h) of the chosen region in target_img, where (w, h)
    matches patch's size (clamped to target_img's bounds if patch is larger).
    """
    h_patch, w_patch = patch.shape[:2]
    h_img, w_img = target_img.shape[:2]
    w_patch = min(w_patch, w_img)
    h_patch = min(h_patch, h_img)
    patch = patch[:h_patch, :w_patch]

    # top-left corner of the patch on the target image, start centered
    pos = [max(0, (w_img - w_patch) // 2), max(0, (h_img - h_patch) // 2)]
    state = {"dragging": False, "drag_offset": (0, 0)}

    def clamp(p):
        p[0] = min(max(0, p[0]), w_img - w_patch)
        p[1] = min(max(0, p[1]), h_img - h_patch)

    def on_mouse(event, mx, my, flags, userdata):
        if event == cv.EVENT_LBUTTONDOWN:
            if pos[0] <= mx <= pos[0] + w_patch and pos[1] <= my <= pos[1] + h_patch:
                state["dragging"] = True
                state["drag_offset"] = (mx - pos[0], my - pos[1])
        elif event == cv.EVENT_MOUSEMOVE and state["dragging"]:
            pos[0] = mx - state["drag_offset"][0]
            pos[1] = my - state["drag_offset"][1]
            clamp(pos)
        elif event == cv.EVENT_LBUTTONUP:
            state["dragging"] = False

    def to_bgr(im):
        return cv.cvtColor(im, cv.COLOR_GRAY2BGR) if im.ndim == 2 else im

    target_bgr = to_bgr(target_img)
    patch_bgr = to_bgr(patch)

    cv.namedWindow(window_name)
    cv.setMouseCallback(window_name, on_mouse)

    step = 1
    confirmed_pos = tuple(pos)
    while True:
        canvas = target_bgr.copy()
        x, y = pos
        roi = canvas[y:y+h_patch, x:x+w_patch]
        blended = cv.addWeighted(roi, 1 - alpha, patch_bgr, alpha, 0)
        canvas[y:y+h_patch, x:x+w_patch] = blended
        cv.rectangle(canvas, (x, y), (x + w_patch, y + h_patch), (0, 255, 0), 1)
        cv.imshow(window_name, canvas)

        key = cv.waitKey(20) & 0xFF
        if key in (13, 32):  # Enter or Space confirms
            confirmed_pos = tuple(pos)
            break
        elif key == 27:  # Esc cancels
            break
        elif key == ord('w'):
            pos[1] -= step; clamp(pos)
        elif key == ord('s'):
            pos[1] += step; clamp(pos)
        elif key == ord('a'):
            pos[0] -= step; clamp(pos)
        elif key == ord('d'):
            pos[0] += step; clamp(pos)

    cv.destroyWindow(window_name)
    x, y = confirmed_pos
    return x, y, w_patch, h_patch

def match_sizes(image1:MatLike, image2:MatLike):
    im1_dim = image1.shape
    im2_dim = image2.shape
    breakpoint()

if __name__ == "__main__":
    args = setup_args()
    main(args.first_image, args.second_image)