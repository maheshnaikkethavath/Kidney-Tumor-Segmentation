import os
import argparse
import torch
import numpy as np
from torch.utils.data import DataLoader
from dataset import Kits2dDataset, get_val_transforms
from model import HybridUNet
import cv2
from scipy.spatial import KDTree

def calculate_dice(preds, targets, class_idx=2):
    preds_class = (preds == class_idx).astype(np.float32)
    targets_class = (targets == class_idx).astype(np.float32)
    
    intersection = (preds_class * targets_class).sum()
    union = preds_class.sum() + targets_class.sum()
    
    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    return 2.0 * intersection / union

def get_boundary(mask, class_idx=2):
    """Extract boundary of a mask using morphological operations."""
    class_mask = (mask == class_idx).astype(np.uint8)
    if class_mask.sum() == 0:
        return np.zeros_like(class_mask)
    
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(class_mask, kernel, iterations=1)
    eroded = cv2.erode(class_mask, kernel, iterations=1)
    boundary = dilated - eroded
    return boundary

def calculate_hd95(preds, targets, class_idx=2):
    """Calculate 95th percentile HD between boundaries of preds and targets."""
    pred_boundary = get_boundary(preds, class_idx)
    target_boundary = get_boundary(targets, class_idx)
    
    pred_pts = np.argwhere(pred_boundary > 0)
    target_pts = np.argwhere(target_boundary > 0)
    
    if len(pred_pts) == 0 and len(target_pts) == 0:
        return 0.0
    if len(pred_pts) == 0 or len(target_pts) == 0:
        return np.inf  # Maximum penalty if one is empty
        
    tree_pred = KDTree(pred_pts)
    tree_target = KDTree(target_pts)
    
    d1, _ = tree_target.query(pred_pts)
    d2, _ = tree_pred.query(target_pts)
    
    hd95 = max(np.percentile(d1, 95), np.percentile(d2, 95))
    return hd95

def calculate_boundary_f1(preds, targets, class_idx=2, tolerance=2):
    """Calculate Boundary F1 Score with tolerance."""
    pred_boundary = get_boundary(preds, class_idx)
    target_boundary = get_boundary(targets, class_idx)
    
    pred_pts = np.argwhere(pred_boundary > 0)
    target_pts = np.argwhere(target_boundary > 0)
    
    if len(pred_pts) == 0 and len(target_pts) == 0:
        return 1.0
    if len(pred_pts) == 0 or len(target_pts) == 0:
        return 0.0
        
    tree_pred = KDTree(pred_pts)
    tree_target = KDTree(target_pts)
    
    d1, _ = tree_target.query(pred_pts)
    d2, _ = tree_pred.query(target_pts)
    
    # Precision: fraction of predicted boundary pixels within tolerance of target
    precision = np.mean(d1 <= tolerance)
    # Recall: fraction of target boundary pixels within tolerance of prediction
    recall = np.mean(d2 <= tolerance)
    
    if precision + recall == 0:
        return 0.0
        
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1

def evaluate(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    val_dataset = Kits2dDataset(args.data_dir, split="test", transform=get_val_transforms(img_size=(args.img_size, args.img_size)))
    val_loader = DataLoader(val_dataset, batch_size=1, shuffle=False)
    
    model = HybridUNet(n_channels=1, n_classes=3, use_transformer=args.use_transformer, use_baa=args.use_baa)
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model.to(device)
    model.eval()
    
    dice_scores = []
    hd95_scores = []
    bf1_scores = []
    
    with torch.no_grad():
        for i, batch in enumerate(val_loader):
            images = batch['image'].to(device)
            masks = batch['mask'].numpy()[0] # Batch size is 1
            
            logits, _ = model(images)
            preds = torch.argmax(logits, dim=1).cpu().numpy()[0]
            
            # We only calculate metrics for tumor class_idx=2
            dice = calculate_dice(preds, masks, class_idx=2)
            hd95 = calculate_hd95(preds, masks, class_idx=2)
            bf1 = calculate_boundary_f1(preds, masks, class_idx=2)
            
            dice_scores.append(dice)
            if not np.isinf(hd95): 
                hd95_scores.append(hd95)
            bf1_scores.append(bf1)
            
            if (i + 1) % 50 == 0:
                print(f"Processed {i+1}/{len(val_loader)} - Dice: {np.mean(dice_scores):.4f}, HD95: {np.mean(hd95_scores):.4f}, BF1: {np.mean(bf1_scores):.4f}")
                
    print("\n--- FINAL METRICS ---")
    print(f"Mean Dice: {np.mean(dice_scores):.4f} +/- {np.std(dice_scores):.4f}")
    print(f"Mean HD95: {np.mean(hd95_scores):.4f} +/- {np.std(hd95_scores):.4f}")
    print(f"Mean BFScore: {np.mean(bf1_scores):.4f} +/- {np.std(bf1_scores):.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="kits_2d_splitted")
    parser.add_argument("--model_path", type=str, default="checkpoints/best_model.pth")
    parser.add_argument("--img_size", type=int, default=256)
    parser.add_argument("--use_transformer", action="store_true")
    parser.add_argument("--use_baa", action="store_true")
    args = parser.parse_args()
    
    # Kaggle Path Auto-Discovery
    if not os.path.exists(args.data_dir):
        # Check standard Kaggle input locations
        potential_bases = ["/kaggle/input", "/kaggle/input/datasets"]
        found = False
        for base in potential_bases:
            if os.path.exists(base):
                for d in os.listdir(base):
                    p = os.path.join(base, d, "kits_2d_splitted")
                    if os.path.exists(p):
                        args.data_dir = p
                        print(f"Auto-detected data_dir: {args.data_dir}")
                        found = True
                        break
            if found: break

    evaluate(args)
