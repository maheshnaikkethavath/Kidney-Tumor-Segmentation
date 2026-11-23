# Backend - FastAPI Medical Imaging Server

FastAPI backend for kidney and tumor segmentation with HybridUNet model.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Server will be available at: `http://localhost:8000`

## API Documentation

Interactive API docs available at: `http://localhost:8000/docs`

## Files

### model.py
Implements the HybridUNet architecture:
- **HybridUNet**: Main model class
  - U-Net encoder-decoder with skip connections
  - Transformer bottleneck for global context
  - Boundary-Aware Attention for enhanced feature extraction
  
- **TransformerBlock**: Transformer component for bottleneck
  - Multi-head self-attention (Lucene)
  - Feed-forward MLP
  - Layer normalization
  
- **BoundaryAwareAttention**: Custom attention mechanism
  - Query, Key, Value projections
  - Softmax attention computation
  - Learnable residual weighting
  
- **ConvBlock**: Standard double convolution
  - 3×3 convolutions
  - Batch normalization
  - ReLU activation

#### Key Methods:
- `forward(x)`: Forward pass
- `load_from_checkpoint(path, device)`: Load trained weights
- `get_activation_maps(x)`: Extract intermediate activations

### gradcam.py
Gradient-weighted Class Activation Mapping for model explainability:
- **GradCAM**: Main class for generating attention heatmaps
  
#### Methods:
- `generate(input_image, class_idx)`: Generate heatmap for specific class
- `get_heatmap_with_colormap(heatmap, colormap)`: Apply color map
- `overlay_heatmap(original, heatmap, alpha)`: Blend with original image

#### Features:
- Class-specific attention visualization
- Batch processing support
- Interpolation to input size
- Multiple color map options

### generate_report.py
Medical report generation in multiple formats:
- **ReportGenerator**: Report creation class

#### Methods:
- `generate_markdown_report()`: Markdown format with metrics
- `generate_html_report()`: Rich HTML format with embedded images

#### Report Includes:
- Patient information
- Timing and modality
- Tumor detection status
- Quantitative measurements
- Class distribution
- Clinical interpretation
- Recommendations
- Technical details

### main.py
FastAPI application with endpoints:

#### Startup Events
- Model loading from checkpoint
- GradCAM initialization
- Device selection (CUDA/CPU)

#### Endpoints

**GET /health**
- Health check
- Returns model status and device

**GET /**
- Root endpoint
- Lists available endpoints

**POST /predict**
- Segmentation prediction
- Accepts: PNG/JPG image
- Returns: Segmentation mask, tumor detection, metrics

**POST /gradcam**
- Attention heatmap generation
- Accepts: Image, target class
- Returns: Heatmap, overlay, class name

**POST /report**
- Medical report generation
- Accepts: Image, patient info, format
- Returns: HTML or Markdown report

## Configuration

Edit `main.py` to adjust:
```python
MODEL_PATH = "best_model.pth"           # Model file path
DEVICE = "cuda" or "cpu"               # Compute device
NORMALIZE_MEAN = 0.5                   # Image normalization mean
NORMALIZE_STD = 0.5                    # Image normalization std
INPUT_SIZE = 256                       # Input image size
```

## Environment Variables

None required by default. Backend uses:
- Port: 8000
- Host: 0.0.0.0

## Requirements

Python 3.8+

Main packages:
- fastapi: Web framework
- uvicorn: ASGI server
- torch: Deep learning
- opencv-python: Image processing
- pillow: Image handling

See `requirements.txt` for all dependencies.

## Image Preprocessing

Input images are automatically:
1. Converted to grayscale (if RGB)
2. Resized to 256×256 pixels
3. Normalized with mean=0.5, std=0.5
4. Converted to PyTorch tensors

## Output Format

Segmentation masks use color coding:
- **Black (0, 0, 0)**: Background
- **Cyan (0, 188, 212)**: Kidney
- **Red (255, 0, 0)**: Tumor

All images returned as Base64-encoded PNG for easy frontend integration.

## Error Handling

Backend returns proper HTTP status codes:
- 200: Success
- 400: Bad request (invalid image, missing file)
- 503: Service unavailable (model not loaded)

Error messages included in response detail field.

## Performance

- GPU (CUDA): ~100-200ms per image
- CPU: ~1-2 seconds per image
- Batch processing: Not currently implemented
- Memory: ~2GB (GPU) / ~8GB (CPU)

## Logging

Server logs:
- Model loading status
- Request processing
- Error details

Check console output for debug information.

## Development

### Running in Debug Mode
```python
# In main.py or when starting:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

### Testing
```bash
# Check health endpoint
curl http://localhost:8000/health

# View API docs
# Open: http://localhost:8000/docs
```

## Troubleshooting

**ImportError: No module named 'torch'**
```bash
pip install -r requirements.txt
```

**Model file not found**
- Ensure `best_model.pth` is in backend directory
- Check MODEL_PATH in main.py

**CUDA not available**
- Install CUDA version matching your torch installation
- Or run on CPU: edit DEVICE = "cpu"

**Port already in use**
```bash
# Change port in main.py:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

## CORS Configuration

Frontend requests are allowed from all origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, restrict to specific origins:
```python
allow_origins=["http://localhost:5173", "https://yourdomain.com"]
```

## Future Improvements

- [ ] Batch API endpoint
- [ ] Streaming responses
- [ ] Model quantization
- [ ] Multi-GPU support
- [ ] Request rate limiting
- [ ] Caching mechanism
- [ ] Database integration
- [ ] Authentication/Authorization
