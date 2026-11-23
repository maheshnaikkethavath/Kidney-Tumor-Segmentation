# Medical Imaging Application - Kidney & Tumor Segmentation

A full-stack deep learning application for kidney and tumor segmentation using CT scans. Built with FastAPI backend and React/Vite frontend with a premium dark-mode medical dashboard.

## Project Structure

```
fullstack project/
├── backend/
│   ├── model.py              # HybridUNet with Transformer bottleneck
│   ├── gradcam.py            # GradCAM for attention visualization
│   ├── generate_report.py     # Medical report generation
│   ├── main.py               # FastAPI application
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── utils/           # API utilities
│   │   ├── App.jsx          # Main app component
│   │   ├── main.jsx         # React entry point
│   │   └── index.css        # Tailwind CSS styles
│   ├── index.html           # HTML entry point
│   ├── package.json         # Node dependencies
│   ├── vite.config.js       # Vite configuration
│   ├── tailwind.config.js   # Tailwind CSS config
│   └── postcss.config.js    # PostCSS config
└── README.md
```

## Features

### Backend
- **HybridUNet Model**: Advanced U-Net with Transformer bottleneck and Boundary-Aware Attention
- **3-Class Segmentation**: Background, Kidney, and Tumor classification
- **GradCAM Visualization**: Attention heatmaps for model interpretability
- **Medical Report Generation**: HTML and Markdown report formats
- **RESTful API**: FastAPI with CORS support
- **Error Handling**: Comprehensive error handling and validation

### Frontend
- **Premium Dashboard**: Dark-mode medical aesthetic (teal/navy color scheme)
- **Image Upload**: Drag-and-drop CT scan upload
- **Side-by-Side View**: Original vs. segmentation comparison
- **Mask Opacity Slider**: Interactive segmentation overlay control
- **Attention Heatmaps**: GradCAM visualization for model decisions
- **Report Generation**: Download PDF/Markdown medical reports
- **Real-time Analytics**: Tumor detection, area calculations, and statistics
- **Responsive Design**: Works on desktop and tablet devices

## Installation & Setup

### Backend Setup

1. **Clone/Navigate to Backend Directory**
```bash
cd backend
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Prepare Model File**
- Place your trained `best_model.pth` file in the backend directory
- The model should contain HybridUNet state dict with the expected architecture

5. **Run Backend Server**
```bash
python main.py
```
- Backend will be available at: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to Frontend Directory**
```bash
cd frontend
```

2. **Install Dependencies**
```bash
npm install
```

3. **Create Environment File**
```bash
cp .env.example .env.local
```
Edit `.env.local` if your backend is running on a different URL.

4. **Run Development Server**
```bash
npm run dev
```
- Frontend will be available at: `http://localhost:5173`

5. **Build for Production**
```bash
npm run build
```

## API Endpoints

### Health Check
```
GET /health
```
Check if the API and model are ready.

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "device": "cuda" or "cpu"
}
```

### Predict Segmentation
```
POST /predict
Content-Type: multipart/form-data
```
Upload a CT scan image and get segmentation predictions.

**Parameters:**
- `file`: Image file (PNG, JPG)

**Response:**
```json
{
  "mask_b64": "base64_encoded_png",
  "tumor_detected": true,
  "tumor_area_pixels": 1234,
  "tumor_percentage": 5.23,
  "class_distribution": {
    "background_pixels": 61456,
    "kidney_pixels": 2310,
    "tumor_pixels": 1234
  },
  "input_shape": [256, 256]
}
```

### Generate GradCAM
```
POST /gradcam?target_class=2
Content-Type: multipart/form-data
```
Generate attention heatmap for a specific class.

**Parameters:**
- `file`: Image file (PNG, JPG)
- `target_class`: Class index (0=Background, 1=Kidney, 2=Tumor)

**Response:**
```json
{
  "heatmap_b64": "base64_encoded_heatmap",
  "overlay_b64": "base64_encoded_overlay",
  "target_class": 2,
  "target_class_name": "Tumor"
}
```

### Generate Report
```
POST /report?patient_id=ID&patient_name=NAME&report_format=html
Content-Type: multipart/form-data
```
Generate a comprehensive medical report.

**Parameters:**
- `file`: Image file
- `patient_id`: Optional patient ID (default: "Unknown")
- `patient_name`: Optional patient name (default: "Unknown")
- `report_format`: "html" or "markdown"

**Response:**
```json
{
  "report": "html_or_markdown_content",
  "report_format": "html",
  "tumor_detected": true,
  "tumor_area_pixels": 1234,
  "tumor_percentage": 5.23
}
```

## Model Architecture

### HybridUNet

```
Input: (B, 1, 256, 256) - Grayscale CT slice
    ↓
Encoder (U-Net style with skip connections)
    ↓
Transformer Bottleneck (with Boundary-Aware Attention)
    ↓
Decoder (U-Net style with skip connections)
    ↓
Output: (B, 3, 256, 256) - 3-class segmentation logits
```

**Key Components:**
- **Encoder**: 4 levels of convolution + max pooling
- **Bottleneck**: TransformerBlock with BoundaryAwareAttention
- **Decoder**: 4 levels of transposed convolution + skip connections
- **Attention**: Self-attention mechanism for capturing boundary features

### Input Requirements
- **Size**: 256×256 pixels
- **Channels**: 1 (grayscale)
- **Normalization**: Mean=0.5, Std=0.5
- **Data Type**: Float32

### Output Classes
- **0 - Background**: Non-kidney tissue
- **1 - Kidney**: Healthy kidney tissue
- **2 - Tumor**: Abnormal tissue growth

## Configuration

### Backend Configuration (main.py)
```python
MODEL_PATH = "best_model.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NORMALIZE_MEAN = 0.5
NORMALIZE_STD = 0.5
INPUT_SIZE = 256
```

### Frontend Configuration (.env)
```
VITE_API_URL=http://localhost:8000
```

## Dependencies

### Backend
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `torch==2.1.0` - Deep learning
- `torchvision==0.16.0` - Vision utilities
- `opencv-python==4.8.1.78` - Image processing
- `pillow==10.1.0` - Image handling
- `python-multipart==0.0.6` - File upload support

### Frontend
- `react==18.2.0` - UI library
- `vite==5.0.8` - Build tool
- `tailwindcss==3.3.6` - CSS framework
- `lucide-react==0.294.0` - Icon library
- `axios==1.6.2` - HTTP client

## Usage Example

1. **Start Backend**
```bash
cd backend
python main.py
```

2. **Start Frontend**
```bash
cd frontend
npm run dev
```

3. **Open Browser**
Navigate to `http://localhost:5173`

4. **Upload CT Scan**
- Click upload area or drag-and-drop a CT scan image
- Frontend automatically resizes to 256×256

5. **View Results**
- Original and segmentation comparison
- Adjust mask opacity with slider
- Generate attention heatmap for tumor class
- Download medical report (HTML or Markdown)

## Important Notes

1. **Model File Required**: `best_model.pth` must be present in the backend directory
2. **CORS Enabled**: Frontend can make API calls from different origin
3. **Medical Use**: This is a diagnostic aid only, not for definitive diagnosis
4. **GPU Support**: Automatically uses CUDA if available
5. **Image Format**: Input images are converted to grayscale and resized to 256×256

## Error Handling

### Common Issues

**"Model file 'best_model.pth' not found"**
- Place the trained model file in the backend directory

**"Connection refused" (Frontend to Backend)**
- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in `main.py`

**"CUDA out of memory"**
- Switch to CPU in `main.py`: `DEVICE = "cpu"`

## Performance

- **Inference Time**: ~100-200ms on GPU, ~1s on CPU
- **Model Size**: ~50-100MB
- **Memory Usage**: ~2GB (GPU) / ~8GB (CPU)

## Report Generation

### HTML Report Features
- Patient information
- Analysis results with metrics
- Embedded images (original, segmentation, heatmap)
- Clinical interpretation
- Medical recommendations
- Printable format

### Markdown Report Features
- Structured text format
- Quantitative measurements
- Clinical findings
- Recommendations
- Exportable to PDF via pandoc

## Future Enhancements

- [ ] Batch processing for multiple images
- [ ] 3D volume segmentation
- [ ] Model explainability dashboard
- [ ] Performance metrics tracking
- [ ] Patient database integration
- [ ] Multi-model ensemble support
- [ ] Real-time streaming inference

## License

This project is provided for educational and research purposes.

## Support

For issues or questions:
1. Check error messages in browser console
2. Review backend logs in terminal
3. Verify model file is present
4. Ensure dependencies are correctly installed

---

**Disclaimer**: This application is a diagnostic aid and must be reviewed by qualified medical professionals before clinical use.
