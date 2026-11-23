# Configuration Guide

## Backend Configuration

### File: `backend/main.py`

All configuration constants are defined at the top of the file:

```python
MODEL_PATH = "best_model.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NORMALIZE_MEAN = 0.5
NORMALIZE_STD = 0.5
INPUT_SIZE = 256
```

### Configuration Parameters

#### `MODEL_PATH`
- **Type**: String
- **Default**: `"best_model.pth"`
- **Description**: Path to trained HybridUNet model checkpoint
- **Usage**: 
  - Place your trained model in the backend directory with this name
  - Or update path to point to your model location
  - Must be a PyTorch state dict file

```python
# Example: Other location
MODEL_PATH = "../models/best_model.pth"
# Or absolute path
MODEL_PATH = "/path/to/trained/model.pth"
```

#### `DEVICE`
- **Type**: String ("cuda" or "cpu")
- **Default**: Auto-detects CUDA availability
- **Description**: Device for model inference
- **Usage**:
  - `"cuda"`: GPU inference (fast, requires NVIDIA GPU + CUDA)
  - `"cpu"`: CPU inference (slow, but works everywhere)

```python
# Force CPU (useful if you encounter GPU memory issues)
DEVICE = "cpu"

# Force CUDA
DEVICE = "cuda"

# Auto-detect (default)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
```

#### `NORMALIZE_MEAN` & `NORMALIZE_STD`
- **Type**: Float
- **Default**: `0.5` (both)
- **Description**: Image normalization parameters
- **Usage**: Must match training normalization
  - Applied to input images: `normalized = (image - mean) / std`
  
```python
# Standard normalization
NORMALIZE_MEAN = 0.5
NORMALIZE_STD = 0.5

# ImageNet normalization (if trained with ImageNet stats)
NORMALIZE_MEAN = 0.485
NORMALIZE_STD = 0.229
```

#### `INPUT_SIZE`
- **Type**: Integer
- **Default**: `256`
- **Description**: Input image dimensions (height × width)
- **Usage**:
  - Images are auto-resized to this size
  - Must match training input size
  - 256×256 recommended for kidney segmentation

```python
# Don't change unless retraining with different size
INPUT_SIZE = 256  # 256×256 pixels
```

### Server Configuration

#### Host
- **Default**: `0.0.0.0`
- **Change in**: `uvicorn.run()` call
- **Purpose**: Listen on all network interfaces

```python
# In main.py if __name__ == "__main__":
# To listen only on localhost:
uvicorn.run(app, host="127.0.0.1", port=8000)

# To listen on specific IP:
uvicorn.run(app, host="192.168.1.100", port=8000)
```

#### Port
- **Default**: `8000`
- **Change in**: `uvicorn.run()` call
- **Usage**: Access API at http://localhost:8000

```python
# Different port
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### CORS Configuration

Located in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For Production** (restrict origins):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Frontend Configuration

### File: `frontend/.env.local`

```
VITE_API_URL=http://localhost:8000
```

### Configuration Parameters

#### `VITE_API_URL`
- **Type**: String (URL)
- **Default**: `http://localhost:8000`
- **Description**: Backend API endpoint
- **Usage**: API calls are made to this URL

```bash
# Development (local)
VITE_API_URL=http://localhost:8000

# Production
VITE_API_URL=https://api.medimaging.com

# Different port
VITE_API_URL=http://localhost:8001

# Different host
VITE_API_URL=http://192.168.1.100:8000
```

### File: `frontend/tailwind.config.js`

Customize colors and fonts:

```javascript
theme: {
  extend: {
    colors: {
      'medical': {
        'navy': '#0f172a',
        'dark': '#1e293b',
        'teal': '#06b6d4',
        'cyan': '#00bcd4',
        'accent': '#0ea5e9'
      }
    },
    fontFamily: {
      sans: ['-apple-system', '...']
    }
  }
}
```

### File: `frontend/vite.config.js`

Development server and build settings:

```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,  // Change frontend port
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

## Model Architecture Configuration

### File: `backend/model.py`

HybridUNet class initialization:

```python
model = HybridUNet(
    in_channels=1,        # Input channels (grayscale)
    out_channels=3,       # Output classes (Background, Kidney, Tumor)
    base_channels=32      # Base number of channels
)
```

### Parameters

#### `in_channels`
- **Default**: `1`
- **Usage**: Number of input channels
  - 1 for grayscale (standard CT)
  - 3 for RGB
  - Don't change unless modifying architecture

#### `out_channels`
- **Default**: `3`
- **Usage**: Number of output classes
  - 3 for (Background, Kidney, Tumor)
  - Change to 2 or 4 for different segmentation tasks

#### `base_channels`
- **Default**: `32`
- **Usage**: Controls model size
  - 32: Standard (default)
  - 64: Larger model (slower but better accuracy)
  - 16: Smaller model (faster but lower accuracy)

## GradCAM Configuration

### File: `backend/gradcam.py`

```python
gradcam = GradCAM(model, target_layer='dec1')
```

#### `target_layer`
- **Default**: `'dec1'` (last decoder stage)
- **Options**: Any layer name in model
  - `'bottleneck'`: Attention mechanism
  - `'dec1'`, `'dec2'`, `'dec3'`, `'dec4'`: Decoder layers
  - `'enc1'`, `'enc2'`, `'enc3'`, `'enc4'`: Encoder layers

```python
# Different layer for attention visualization
gradcam = GradCAM(model, target_layer='bottleneck')
```

## Report Generation Configuration

### File: `backend/generate_report.py`

`ReportGenerator` class parameters:

```python
report_gen = ReportGenerator(
    patient_id="P001",
    patient_name="John Doe"
)
```

#### Report Metrics Calculation

```python
# Tumor area calculation (in the report generation)
pixel_size_mm = 0.1  # Assume 0.1mm per pixel
tumor_area_mm2 = tumor_area_pixels * (pixel_size_mm ** 2)
tumor_area_cm2 = tumor_area_mm2 / 100
```

Adjust `pixel_size_mm` for different scanner resolutions:

```python
# Example: CT scanner with 0.5mm resolution
pixel_size_mm = 0.5  # Results in larger area estimates
```

## Performance Tuning

### For Faster Inference
1. **Reduce base_channels**:
   ```python
   model = HybridUNet(base_channels=16)
   ```

2. **Use CPU on high-throughput server**:
   ```python
   DEVICE = "cpu"  # Fast for multiple concurrent requests
   ```

3. **Implement batching** (modify main.py):
   ```python
   # Process multiple images at once
   ```

### For Better Accuracy
1. **Increase base_channels**:
   ```python
   model = HybridUNet(base_channels=64)
   ```

2. **Ensure proper normalization** matches training:
   ```python
   NORMALIZE_MEAN = 0.5
   NORMALIZE_STD = 0.5
   ```

3. **Use GPU**:
   ```python
   DEVICE = "cuda"
   ```

## Security Configuration

### Frontend Security

Add to `frontend/vite.config.js`:
```javascript
export default defineConfig({
  server: {
    // Only allow API calls to your domain
    proxy: {
      '/api': {
        target: 'https://api.secure-domain.com',
        ...
      }
    }
  }
})
```

### Backend Security

In `backend/main.py`:

**Authentication (if needed)**:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/predict")
async def predict(
    file: UploadFile,
    credentials: HTTPAuthCredentials = Depends(security)
):
    # Verify token
    ...
```

**Rate Limiting**:
```bash
pip install slowapi

from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(request: Request, ...):
    ...
```

## Deployment Configuration

### Docker

Create `Dockerfile` for backend:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### Environment Variables (Production)

Create `.env` file:
```
MODEL_PATH=/models/best_model.pth
DEVICE=cuda
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=info
```

## Logging Configuration

Add to `backend/main.py`:
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Model loaded successfully")
logger.error("Failed to load model: %s", error_msg)
```

## Summary: Common Customizations

| Customization | File | Variable | Default |
|---------------|------|----------|---------|
| Model location | main.py | `MODEL_PATH` | "best_model.pth" |
| Use GPU/CPU | main.py | `DEVICE` | Auto-detect |
| Input size | main.py | `INPUT_SIZE` | 256 |
| API port | main.py | uvicorn port | 8000 |
| Frontend port | vite.config.js | server.port | 5173 |
| API endpoint | .env.local | `VITE_API_URL` | http://localhost:8000 |
| Color scheme | tailwind.config.js | colors | teal/navy |

## Next Steps

1. **Configure for your setup**: Update paths and parameters
2. **Set environment variables**: Create `.env` files
3. **Test configuration**: Run create_dummy_model.py
4. **Verify**: Check API docs at /docs
5. **Deploy**: Use Docker or your preferred platform
