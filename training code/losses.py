import torch
import torch.nn as nn
import torch.nn.functional as F

class DiceLoss(nn.Module):
    def __init__(self, smooth=1e-5):
        super(DiceLoss, self).__init__()
        self.smooth = smooth

    def forward(self, inputs, targets):
        # inputs: (B, C, H, W) logits
        # targets: (B, C, H, W) one-hot encoded or (B, H, W) class indices
        
        # apply softmax to inputs
        inputs = F.softmax(inputs, dim=1)
        
        # If targets is not one-hot, make it one-hot
        if targets.dim() == 3:
            targets = F.one_hot(targets, num_classes=inputs.shape[1]).permute(0, 3, 1, 2).float()
            
        intersection = (inputs * targets).sum(dim=(2, 3))
        union = inputs.sum(dim=(2, 3)) + targets.sum(dim=(2, 3))
        
        dice = (2. * intersection + self.smooth) / (union + self.smooth)
        
        # return inverse dice (1 - dice)
        return 1.0 - dice.mean()

class CompoundLoss(nn.Module):
    def __init__(self, ce_weight=1.0, dice_weight=1.0):
        super(CompoundLoss, self).__init__()
        self.ce_weight = ce_weight
        self.dice_weight = dice_weight
        self.ce = nn.CrossEntropyLoss()
        self.dice = DiceLoss()

    def forward(self, inputs, targets):
        # inputs: (B, C, H, W)
        # targets: (B, H, W)
        ce_loss = self.ce(inputs, targets)
        dice_loss = self.dice(inputs, targets)
        return self.ce_weight * ce_loss + self.dice_weight * dice_loss

def get_morphological_gradient(mask):
    """
    Computes boundaries of a binary mask using morphological gradient.
    mask: (B, 1, H, W) float tensor [0, 1]
    """
    # Dilation
    dilated = F.max_pool2d(mask, kernel_size=3, stride=1, padding=1)
    # Erosion: -max_pool(-x)
    eroded = -F.max_pool2d(-mask, kernel_size=3, stride=1, padding=1)
    # Morphological gradient
    grad = dilated - eroded
    return grad

class AuxiliaryEdgeLoss(nn.Module):
    def __init__(self, edge_weight=0.1):
        super(AuxiliaryEdgeLoss, self).__init__()
        self.edge_weight = edge_weight
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, edge_logits, targets):
        """
        edge_logits: (B, 1, H, W) raw logits from the BAA module
        targets: (B, H, W) multiclass labels
        """
        # Create a binary mask for foreground (kidney + tumor = >0)
        binary_mask = (targets > 0).float().unsqueeze(1)
        
        # Get morphological gradient acting as the ground truth boundary
        gt_edges = get_morphological_gradient(binary_mask)
        
        # Edge loss
        loss = self.bce(edge_logits, gt_edges)
        return self.edge_weight * loss
