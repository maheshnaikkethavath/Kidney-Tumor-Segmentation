import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
import matplotlib.pyplot as plt

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.hook_layers()

    def hook_layers(self):
        def forward_hook(module, input, output):
            self.activations = output
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        # Use register_forward_hook and register_backward_hook
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_cam(self, input_image, target_class=2):
        """
        input_image: (1, 1, H, W) tensor
        target_class: index of the class to visualize (tumor=2)
        """
        self.model.eval()
        logits, _ = self.model(input_image)
        
        # We want to explain the segmentation of the target class
        # We take the mean of the logits for the target class across the spatial dimensions
        score = logits[:, target_class, :, :].mean()
        
        self.model.zero_grad()
        score.backward()
        
        gradients = self.gradients.cpu().data.numpy()[0]
        activations = self.activations.cpu().data.numpy()[0]
        
        # Global Average Pooling of gradients
        weights = np.mean(gradients, axis=(1, 2))
        
        cam = np.zeros(activations.shape[1:], dtype=np.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i]
            
        cam = np.maximum(cam, 0) # ReLU
        cam = cv2.resize(cam, (input_image.shape[3], input_image.shape[2]))
        cam = cam - np.min(cam)
        cam = cam / (np.max(cam) + 1e-7)
        return cam

def visualize_gradcam(model, image_tensor, mask, target_layer=None, save_path="gradcam.png"):
    """
    image_tensor: (1, 1, H, W) normalized tensor
    mask: (H, W) numpy array
    target_layer: layer to visualize. If None, tries to find the last conv layer in model.up4
    """
    if target_layer is None:
        # Default target layer for HybridUNet is the second DoubleConv in Up4
        target_layer = model.up4.conv.double_conv[4]
        
    gcam = GradCAM(model, target_layer)
    cam = gcam.generate_cam(image_tensor, target_class=2)
    
    img = image_tensor[0, 0].cpu().numpy()
    img = (img - img.min()) / (img.max() - img.min() + 1e-7)
    
    # Prediction
    logits, _ = model(image_tensor)
    pred = torch.argmax(logits, dim=1)[0].cpu().numpy()
    
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    
    axes[0].set_title("Input Image")
    axes[0].imshow(img, cmap='gray')
    axes[0].axis('off')
    
    axes[1].set_title("Ground Truth (Tumor=2)")
    axes[1].imshow(mask, cmap='jet', vmin=0, vmax=2)
    axes[1].axis('off')
    
    axes[2].set_title("GradCAM Attention (Tumor)")
    axes[2].imshow(img, cmap='gray')
    axes[2].imshow(cam, cmap='jet', alpha=0.5)
    axes[2].axis('off')
    
    axes[3].set_title("Model Prediction")
    axes[3].imshow(pred, cmap='jet', vmin=0, vmax=2)
    axes[3].axis('off')
    
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    print(f"GradCAM visualization saved to {save_path}")
