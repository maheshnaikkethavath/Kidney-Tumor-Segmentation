import os
from pathlib import Path
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
import albumentations as A
from albumentations.pytorch import ToTensorV2

class Kits2dDataset(Dataset):
    def __init__(self, root_dir, split="train", transform=None, img_size=(256, 256), max_samples=None):
        """
        Args:
            root_dir (str): Path to the kits_2d_splitted directory.
            split (str): One of "train", "val", "test".
            transform (callable, optional): Albumentations transforms to be applied on a sample.
            img_size (tuple): Target image size. Default is 256x256.
        """
        # Robust Path Discovery
        self.root_dir = Path(root_dir)
        if (self.root_dir / split).exists():
            self.working_dir = self.root_dir / split
        else:
            self.working_dir = self.root_dir
            
        self.images_dir = self.working_dir / "images"
        self.masks_dir = self.working_dir / "masks"
        
        # Fallback for kits_2d_splitted/train structure
        if not self.images_dir.exists():
            # Try once more one level deeper
            potential_images = list(self.working_dir.glob("**/images"))
            if potential_images:
                self.images_dir = potential_images[0]
                self.masks_dir = self.images_dir.parent / "masks"
        
        self.img_size = img_size
        self.max_samples = max_samples
        
        self.image_files = sorted(list(self.images_dir.glob("*.png"))) if self.images_dir.exists() else []
        self.mask_files = sorted(list(self.masks_dir.glob("*.png"))) if self.masks_dir.exists() else []
        
        print(f"[{split}] Found {len(self.image_files)} images and {len(self.mask_files)} masks in {self.images_dir}")
            
        self.transform = transform
        
        # For testing: limit dataset size
        if hasattr(self, 'max_samples') and self.max_samples is not None:
            self.image_files = self.image_files[:self.max_samples]
            if len(self.mask_files) > 0:
                self.mask_files = self.mask_files[:self.max_samples]
        
    def __len__(self):
        return len(self.image_files)
        
    def __getitem__(self, idx):
        img_path = str(self.image_files[idx])
        
        # Load image as grayscale
        # If the image was originally NIfTI with HU clip, it's now in 8-bit PNG (0-255).
        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Image not found: {img_path}")
            
        # Optional: Resize explicitly here before augmentations if not done in Albumentations
        # We will let Albumentations handle resizing
        
        if len(self.mask_files) > idx:
            mask_path = str(self.mask_files[idx])
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            
            # Map [0, 127, 255] to class indices [0, 1, 2]
            # 0: Background
            # 1: Kidney (127)
            # 2: Tumor/Cyst (255)
            mapped_mask = np.zeros_like(mask, dtype=np.int64)
            mapped_mask[mask > 64] = 1   # Kidney and Tumor
            mapped_mask[mask > 192] = 2  # Tumor only
            
            mask = mapped_mask
        else:
            mask = np.zeros(image.shape, dtype=np.int64)
            
        if self.transform is not None:
            # Albumentations expects mask to be named 'mask'
            augmented = self.transform(image=image, mask=mask)
            image = augmented['image']
            mask = augmented['mask']
        else:
            # Default fallback transformation
            image = cv2.resize(image, self.img_size, interpolation=cv2.INTER_LINEAR)
            mask = cv2.resize(mask.astype(np.uint8), self.img_size, interpolation=cv2.INTER_NEAREST)
            
            # Normalize to [0, 1]
            image = image.astype(np.float32) / 255.0
            # z-score normalize (optional, using standard ImageNet mean/std or global approx)
            image = (image - 0.5) / 0.5 
            
            image = torch.from_numpy(image).unsqueeze(0)
            mask = torch.from_numpy(mask).long()
            
        return {"image": image, "mask": mask, "id": self.image_files[idx].stem}

def get_train_transforms(img_size=(256, 256)):
    return A.Compose([
        A.Resize(height=img_size[0], width=img_size[1]),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.2, rotate_limit=30, p=0.5),
        A.OneOf([
            A.GridDistortion(p=0.5),
            # Newer versions of Albumentations might have changed these arguments
            A.OpticalDistortion(distort_limit=0.1, p=0.5),
            A.ElasticTransform(alpha=120, sigma=120 * 0.05, p=0.5),
        ], p=0.3),
        A.CLAHE(p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.RandomGamma(gamma_limit=(80, 120), p=0.5),
        A.GaussNoise(p=0.2), # Use defaults to avoid version-specific argument errors
        A.CoarseDropout(p=0.3), # Use defaults to avoid version-specific argument errors
        A.Normalize(mean=(0.5,), std=(0.5,)),
        ToTensorV2(),
    ])

def get_val_transforms(img_size=(256, 256)):
    return A.Compose([
        A.Resize(height=img_size[0], width=img_size[1]),
        A.Normalize(mean=(0.5,), std=(0.5,)),
        ToTensorV2(),
    ])

# Quick testing entry point
if __name__ == "__main__":
    root = r"kits_2d_splitted"
    dataset = Kits2dDataset(root_dir=root, split="train", transform=get_train_transforms())
    if len(dataset) > 0:
        sample = dataset[0]
        print(f"Sample Image shape: {sample['image'].shape}, dtype: {sample['image'].dtype}")
        print(f"Sample Mask shape: {sample['mask'].shape}, dtype: {sample['mask'].dtype}")
        print(f"Unique masks: {torch.unique(sample['mask'])}")
    else:
        print("Dataset is empty. Check path.")
