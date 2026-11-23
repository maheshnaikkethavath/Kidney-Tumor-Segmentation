import torch
import torch.nn.functional as F
import numpy as np
import cv2
from typing import Optional


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping for explainability.
    Generates attention heatmaps for a specific class.

    Works with HybridUNet whose forward() returns (logits, edge_map).
    """

    def __init__(self, model: torch.nn.Module, target_layer: str = 'up4.conv.double_conv'):
        """
        Args:
            model: PyTorch model (HybridUNet)
            target_layer: Dot-separated name of the submodule to hook into.
                          Defaults to 'up4.conv.double_conv' to match the
                          training-code convention (model.up4.conv.double_conv[4]).
        """
        self.model = model
        self.target_layer_name = target_layer
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None
        self._forward_hook = None
        self._backward_hook = None

    def _get_target_module(self) -> torch.nn.Module:
        """Resolve the target layer by name."""
        module = self.model
        for part in self.target_layer_name.split('.'):
            if part.isdigit():
                module = module[int(part)]
            else:
                module = getattr(module, part)
        return module

    def _forward_hook_fn(self, module, input, output):
        self.activations = output.detach()

    def _backward_hook_fn(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, input_image: torch.Tensor, class_idx: int = 2) -> np.ndarray:
        """
        Generate GradCAM heatmap for a specific class.

        Args:
            input_image: Input tensor (1, 1, H, W)
            class_idx: Target class index (0=Background, 1=Kidney, 2=Tumor)

        Returns:
            Heatmap as numpy array (H, W), values in [0, 1]
        """
        self.gradients = None
        self.activations = None

        input_image = input_image.detach().requires_grad_(True)

        target_module = self._get_target_module()

        # Use register_full_backward_hook to avoid FutureWarning
        fwd_handle = target_module.register_forward_hook(self._forward_hook_fn)
        bwd_handle = target_module.register_full_backward_hook(self._backward_hook_fn)

        try:
            self.model.eval()

            # HybridUNet returns (logits, edge_map)
            output = self.model(input_image)
            logits = output[0] if isinstance(output, (tuple, list)) else output

            self.model.zero_grad()

            # Score: mean of target class logits across spatial dims
            score = logits[:, class_idx, :, :].mean()
            score.backward()

            if self.gradients is None or self.activations is None:
                raise RuntimeError(
                    "Failed to capture gradients or activations. "
                    f"Check that '{self.target_layer_name}' is a valid submodule."
                )

            # Global-average-pool the gradients → channel weights
            weights = self.gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)

            # Weighted sum of activation maps
            heatmap = (self.activations * weights).sum(dim=1, keepdim=True)  # (1, 1, h, w)
            heatmap = F.relu(heatmap)

            # Normalize to [0, 1]
            hmin = heatmap.min()
            hmax = heatmap.max()
            if hmax - hmin > 1e-7:
                heatmap = (heatmap - hmin) / (hmax - hmin)

            # Resize to input spatial size
            input_h, input_w = input_image.shape[-2:]
            heatmap = F.interpolate(
                heatmap,
                size=(input_h, input_w),
                mode='bilinear',
                align_corners=False
            )

            return heatmap[0, 0].cpu().detach().numpy()

        finally:
            fwd_handle.remove()
            bwd_handle.remove()

    def get_heatmap_with_colormap(
        self,
        heatmap: np.ndarray,
        colormap: int = cv2.COLORMAP_JET
    ) -> np.ndarray:
        """
        Convert a grayscale heatmap ([0,1] float) to a coloured RGB image.

        Returns:
            (H, W, 3) uint8 RGB array
        """
        heatmap_255 = (heatmap * 255).astype(np.uint8)
        colored_bgr = cv2.applyColorMap(heatmap_255, colormap)
        colored_rgb = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)
        return colored_rgb

    def overlay_heatmap(
        self,
        original_image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Overlay heatmap on original image.

        Args:
            original_image: (H, W, 3) RGB uint8
            heatmap:        (H, W) float in [0, 1]
            alpha:          heatmap blending weight

        Returns:
            (H, W, 3) uint8 blended RGB image
        """
        colored_heatmap = self.get_heatmap_with_colormap(heatmap)

        if original_image.shape[:2] != colored_heatmap.shape[:2]:
            colored_heatmap = cv2.resize(
                colored_heatmap,
                (original_image.shape[1], original_image.shape[0])
            )

        overlay = cv2.addWeighted(
            original_image.astype(np.float32), 1 - alpha,
            colored_heatmap.astype(np.float32), alpha,
            0
        )
        return np.clip(overlay, 0, 255).astype(np.uint8)
