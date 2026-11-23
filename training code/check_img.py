import cv2
import numpy as np

img_path = r"C:\Users\pagil\OneDrive\Documents\College\Minor project\small dataset try\kits_2d_splitted\train\images\case_00000_axial_291.png"
mask_path = r"C:\Users\pagil\OneDrive\Documents\College\Minor project\small dataset try\kits_2d_splitted\train\masks\case_00000_axial_291.png"

img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
mask = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)

print(f"Image shape: {img.shape}, dtype: {img.dtype}, min: {img.min()}, max: {img.max()}")
print(f"Mask shape: {mask.shape}, dtype: {mask.dtype}, min: {mask.min()}, max: {mask.max()}, unique: {np.unique(mask)}")
