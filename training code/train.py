import os
import argparse
import torch
import numpy as np
from torch.utils.data import DataLoader, Subset
from dataset import Kits2dDataset, get_train_transforms, get_val_transforms
from model import HybridUNet
from losses import CompoundLoss, AuxiliaryEdgeLoss
import time
from sklearn.model_selection import KFold

def calculate_dice(preds, targets, class_idx=2):
    """Calculate Dice coefficient for a specific class (default Tumor=2)"""
    preds_class = (preds == class_idx).float()
    targets_class = (targets == class_idx).float()
    
    intersection = (preds_class * targets_class).sum()
    union = preds_class.sum() + targets_class.sum()
    
    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    return (2.0 * intersection / union).item()

def train_one_epoch(model, loader, optimizer, criterion_main, criterion_edge, device, scaler, args):
    model.train()
    train_loss = 0.0
    optimizer.zero_grad()
    
    for batch_idx, batch in enumerate(loader):
        images = batch['image'].to(device)
        masks = batch['mask'].to(device).long()
        
        with torch.amp.autocast('cuda') if scaler is not None else torch.autocast('cpu'):
            logits, edge_logits = model(images)
            loss_main = criterion_main(logits, masks)
            loss = loss_main
            
            if args.use_baa and edge_logits is not None:
                loss_edge = criterion_edge(edge_logits, masks)
                loss += loss_edge
            
            loss = loss / args.accum_steps
            
        if scaler is not None:
            scaler.scale(loss).backward()
            if ((batch_idx + 1) % args.accum_steps == 0) or (batch_idx + 1 == len(loader)):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
        else:
            loss.backward()
            if ((batch_idx + 1) % args.accum_steps == 0) or (batch_idx + 1 == len(loader)):
                optimizer.step()
                optimizer.zero_grad()
                
        train_loss += loss.item() * args.accum_steps
    return train_loss / len(loader)

def validate(model, loader, device):
    model.eval()
    val_dice_tumor = 0.0
    with torch.no_grad():
        for batch in loader:
            images = batch['image'].to(device)
            masks = batch['mask'].to(device)
            logits, _ = model(images)
            preds = torch.argmax(logits, dim=1)
            val_dice_tumor += calculate_dice(preds, masks, class_idx=2)
    return val_dice_tumor / len(loader)

def train(args):
    # Kaggle Path Setup (Only set if default or not found)
    if args.kaggle:
        if not os.path.exists(args.data_dir):
            # Attempt to find common Kaggle data paths
            potential_paths = [
                "/kaggle/input/kits2d-multiclass-dataset/kits_2d_splitted",
                "/kaggle/input/3d-ct-kidney-tumor-segmentation-splitted/kits_2d_splitted"
            ]
            for p in potential_paths:
                if os.path.exists(p):
                    args.data_dir = p
                    break
        
        if args.save_dir == "checkpoints":
            args.save_dir = "/kaggle/working/checkpoints"
            
        os.makedirs(args.save_dir, exist_ok=True)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}", flush=True)
    
    # Dataset
    full_dataset = Kits2dDataset(args.data_dir, split="train", transform=get_train_transforms(img_size=(args.img_size, args.img_size)), max_samples=args.max_samples)
    
    # K-Fold Setup
    kf = KFold(n_splits=args.n_folds, shuffle=True, random_state=42)
    fold_results = []

    summary_file = os.path.join(args.save_dir, "training_summary.txt")
    with open(summary_file, "w") as f:
        f.write(f"Research Grade Training Summary - {time.ctime()}\n")
        f.write(f"Model: HybridUNet | Transformer: {args.use_transformer} | BAA: {args.use_baa}\n")
        f.write("-" * 50 + "\n")

    for fold, (train_idx, val_idx) in enumerate(kf.split(np.arange(len(full_dataset)))):
        print(f"\n--- FOLD {fold+1}/{args.n_folds} ---")
        
        train_sub = Subset(full_dataset, train_idx)
        val_sub = Subset(full_dataset, val_idx)
        # Apply validation transforms to val_sub
        val_sub.dataset.transform = get_val_transforms(img_size=(args.img_size, args.img_size))
        
        train_loader = DataLoader(train_sub, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, pin_memory=True)
        val_loader = DataLoader(val_sub, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, pin_memory=True)
        
        model = HybridUNet(n_channels=1, n_classes=3, use_transformer=args.use_transformer, use_baa=args.use_baa).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
        criterion_main = CompoundLoss().to(device)
        criterion_edge = AuxiliaryEdgeLoss().to(device)
        scaler = torch.amp.GradScaler('cuda') if torch.cuda.is_available() else None
        
        best_fold_dice = 0.0
        
        for epoch in range(args.epochs):
            t_loss = train_one_epoch(model, train_loader, optimizer, criterion_main, criterion_edge, device, scaler, args)
            v_dice = validate(model, val_loader, device)
            scheduler.step()
            
            print(f"Epoch {epoch+1} | Loss: {t_loss:.4f} | Val Dice: {v_dice:.4f}")
            
            if v_dice > best_fold_dice:
                best_fold_dice = v_dice
                torch.save(model.state_dict(), os.path.join(args.save_dir, f"best_model_fold{fold+1}.pth"))
        
        fold_results.append(best_fold_dice)
        print(f"Fold {fold+1} Best Tumor Dice: {best_fold_dice:.4f}")
        with open(summary_file, "a") as f:
            f.write(f"Fold {fold+1}: Best Tumor Dice = {best_fold_dice:.4f}\n")

    mean_dice = np.mean(fold_results)
    std_dice = np.std(fold_results)
    print(f"\nFINAL K-FOLD RESULTS: {mean_dice:.4f} +/- {std_dice:.4f}")
    with open(summary_file, "a") as f:
        f.write("-" * 50 + "\n")
        f.write(f"Final Cross-Validation Score: {mean_dice:.4f} +/- {std_dice:.4f}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="kits_2d_splitted")
    parser.add_argument("--save_dir", type=str, default="checkpoints")
    parser.add_argument("--kaggle", action="store_true", help="Running on Kaggle")
    parser.add_argument("--n_folds", type=int, default=3)
    parser.add_argument("--img_size", type=int, default=256)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--accum_steps", type=int, default=4)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--use_transformer", action="store_true")
    parser.add_argument("--use_baa", action="store_true")
    args = parser.parse_args()
    
    train(args)

