import torch
import torch.nn as nn
import torch.nn.functional as F

class DoubleConv(nn.Module):
    """(convolution => [BN] => ReLU) * 2"""
    def __init__(self, in_channels, out_channels, mid_channels=None):
        super().__init__()
        if not mid_channels:
            mid_channels = out_channels
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)

class Down(nn.Module):
    """Downscaling with maxpool then double conv"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels)
        )

    def forward(self, x):
        return self.maxpool_conv(x)

class BAAModule(nn.Module):
    """Boundary-Aware Attention Module"""
    def __init__(self, enc_channels):
        super().__init__()
        # Small head to compute edge logits from encoder features
        self.edge_head = nn.Sequential(
            nn.Conv2d(enc_channels, enc_channels // 2, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(enc_channels // 2, 1, kernel_size=1)
        )

    def forward(self, enc_feat):
        # enc_feat: Skip connection feature from encoder
        # E: Edge logits
        edge_logits = self.edge_head(enc_feat)
        # Soft edge attention map A_edge in [0, 1]
        A_edge = torch.sigmoid(edge_logits)
        
        # Multiply A_edge elementwise with skip feature to emphasize boundary regions
        weighted_skip = enc_feat * A_edge
        
        return weighted_skip, edge_logits

class Up(nn.Module):
    """Upscaling then double conv with BAA"""
    def __init__(self, in_channels, out_channels, enc_channels, use_baa=True):
        super().__init__()
        self.use_baa = use_baa
        
        # bilinear upsampling
        self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        
        self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
        
        if self.use_baa:
            self.baa = BAAModule(enc_channels)

    def forward(self, x1, x2):
        # x1: features from decoder (to upsample)
        # x2: skip connection from encoder
        x1 = self.up(x1)
        
        # input is CHW
        diffY = x2.size()[2] - x1.size()[2]
        diffX = x2.size()[3] - x1.size()[3]

        x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2,
                        diffY // 2, diffY - diffY // 2])
        
        edge_logits = None
        if self.use_baa:
            # Weight the skip connection using Boundary-Aware Attention
            x2, edge_logits = self.baa(x2)
            
        # Concatenate weighted skip and decoder features
        x = torch.cat([x2, x1], dim=1)
        x = self.conv(x)
        return x, edge_logits

class TransformerBlock(nn.Module):
    """Local or Global Transformer Block in Bottleneck"""
    def __init__(self, dim, num_heads=4, mlp_ratio=4.):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        # Standard Multi-head self-attention
        self.attn = nn.MultiheadAttention(embed_dim=dim, num_heads=num_heads, batch_first=True)
        self.norm2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, int(dim * mlp_ratio)),
            nn.GELU(),
            nn.Linear(int(dim * mlp_ratio), dim)
        )

    def forward(self, x):
        # x: (B, C, H, W)
        B, C, H, W = x.shape
        # Flatten spatial dims: (B, H*W, C)
        x_flat = x.flatten(2).transpose(1, 2)
        
        # Self-attention
        attn_out, _ = self.attn(self.norm1(x_flat), self.norm1(x_flat), self.norm1(x_flat))
        x_flat = x_flat + attn_out
        
        # FFN
        mlp_out = self.mlp(self.norm2(x_flat))
        x_flat = x_flat + mlp_out
        
        # Reshape back to (B, C, H, W)
        x_out = x_flat.transpose(1, 2).view(B, C, H, W)
        return x_out

class OutConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(OutConv, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, x):
        return self.conv(x)

class HybridUNet(nn.Module):
    def __init__(self, n_channels=1, n_classes=3, use_transformer=True, use_baa=True):
        super(HybridUNet, self).__init__()
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.use_baa = use_baa

        factor = 2 # factor to reduce channels to fit in colab without hitting OOM immediately

        self.inc = DoubleConv(n_channels, 64 // factor)
        self.down1 = Down(64 // factor, 128 // factor)
        self.down2 = Down(128 // factor, 256 // factor)
        self.down3 = Down(256 // factor, 512 // factor)
        self.down4 = Down(512 // factor, 1024 // factor)

        self.use_transformer = use_transformer
        if self.use_transformer:
            # Transformer in bottleneck
            self.transformer = TransformerBlock(dim=1024 // factor, num_heads=4)

        # Decoder
        self.up1 = Up((1024 + 512) // factor, 512 // factor, 512 // factor, use_baa=use_baa)
        self.up2 = Up((512 + 256) // factor, 256 // factor, 256 // factor, use_baa=use_baa)
        self.up3 = Up((256 + 128) // factor, 128 // factor, 128 // factor, use_baa=use_baa)
        self.up4 = Up((128 + 64) // factor, 64 // factor, 64 // factor, use_baa=use_baa)
        
        self.outc = OutConv(64 // factor, n_classes)

    def forward(self, x):
        # Encoder
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        # Bottleneck (Transformer)
        if self.use_transformer:
            x5 = self.transformer(x5)

        # Decoder path with Edge logits collection
        edge_logits_list = []
        
        x, e1 = self.up1(x5, x4)
        if e1 is not None: edge_logits_list.append(e1)
            
        x, e2 = self.up2(x, x3)
        if e2 is not None: edge_logits_list.append(e2)
            
        x, e3 = self.up3(x, x2)
        if e3 is not None: edge_logits_list.append(e3)
            
        x, e4 = self.up4(x, x1)
        if e4 is not None: edge_logits_list.append(e4)

        logits = self.outc(x)
        
        # Upsample all edge logits to input size and sum or average them for auxiliary loss
        edge_map = None
        if self.use_baa and len(edge_logits_list) > 0:
            upsampled_edges = [F.interpolate(e, size=logits.shape[2:], mode='bilinear', align_corners=True) 
                               for e in edge_logits_list]
            edge_map = torch.mean(torch.stack(upsampled_edges), dim=0)

        return logits, edge_map

    def load_from_checkpoint(self, checkpoint_path: str, device: str = 'cpu'):
        """Load model weights from checkpoint file."""
        try:
            state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
        except Exception as e:
            print(f"Warning: Failed to load with weights_only=True: {e}")
            print("Retrying with weights_only=False...")
            state_dict = torch.load(checkpoint_path, map_location=device, weights_only=False)
        
        self.load_state_dict(state_dict)
        self.to(device)
        self.eval()

# Quick testing entry point
if __name__ == "__main__":
    model = HybridUNet(n_channels=1, n_classes=3, use_transformer=True, use_baa=True)
    x = torch.randn((2, 1, 256, 256))
    logits, edge_map = model(x)
    print(f"Logits shape: {logits.shape}")

