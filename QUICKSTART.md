# Quick Start Guide

## Prerequisites
- Python 3.8+ (for backend)
- Node.js 16+ (for frontend)
- `best_model.pth` (trained HybridUNet model)

## Step-by-Step Setup

### 1. Backend Setup

**Open Terminal/PowerShell and navigate to the project:**
```bash
cd "fullstack project"
cd backend
```

**Create Python Virtual Environment:**
```bash
python -m venv venv
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

**Install Python Dependencies:**
```bash
pip install -r requirements.txt
```

**Add Your Trained Model:**
- Copy your `best_model.pth` file into the `backend/` directory

**Start Backend Server:**
```bash
python main.py
```

✅ Backend should now be running at: `http://localhost:8000`

### 2. Frontend Setup

**Open a NEW terminal/PowerShell:**
```bash
cd "fullstack project"
cd frontend
```

**Install Node Dependencies:**
```bash
npm install
```

**Start Development Server:**
```bash
npm run dev
```

✅ Frontend should now be running at: `http://localhost:5173`

## Testing the Application

### 1. Check Backend Health
```bash
# In PowerShell/Terminal:
curl http://localhost:8000/health

# Or visit in browser:
# http://localhost:8000/docs
```

### 2. Open Frontend
```
http://localhost:5173
```

### 3. Upload a Test Image
- Prepare a 256×256 grayscale CT scan image (PNG or JPG)
- Click the upload area or drag-and-drop
- Wait for analysis to complete

### 4. View Results
- Original and segmentation comparison
- Mask opacity slider control
- Tumor detection status
- Statistical analysis

### 5. Generate Report
- Click "Generate Report" button
- Select format (HTML or Markdown)
- Download report

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'torch'` | Run: `pip install -r requirements.txt` |
| Backend won't start | Ensure port 8000 is free, or change port in `main.py` |
| Frontend can't connect to backend | Check backend is running, verify URL in `.env.local` |
| `best_model.pth` not found | Copy trained model to `backend/` directory |
| "Port 5173 already in use" | Kill process or use: `npm run dev -- --port 5174` |

## Project Structure

```
fullstack project/
├── backend/
│   ├── main.py              ← Start here for backend
│   ├── model.py
│   ├── gradcam.py
│   ├── generate_report.py
│   ├── requirements.txt
│   ├── best_model.pth       ← Add your model here
│   └── venv/                ← Created after setup
└── frontend/
    ├── src/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── node_modules/        ← Created after npm install
```

## API Endpoints

Once backend is running, test these endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Interactive docs
# Visit: http://localhost:8000/docs
```

## Frontend Features

✨ **What you can do:**
1. Upload CT scan images
2. Get instant segmentation prediction
3. View side-by-side original vs. segmentation
4. Adjust mask transparency with slider
5. Generate attention heatmaps (GradCAM)
6. Download medical reports (HTML/Markdown)
7. View tumor detection and metrics

## Backend APIs

📡 **Available endpoints:**
- `GET /health` - Check API status
- `POST /predict` - Segmentation prediction
- `POST /gradcam` - Attention heatmap
- `POST /report` - Generate medical report

## Next Steps

### For Development
1. Modify components in `frontend/src/components/`
2. Update API calls in `frontend/src/utils/api.js`
3. Customize styling in `frontend/tailwind.config.js`

### For Production
1. Build frontend: `npm run build`
2. Deploy `dist/` folder to web host
3. Update backend URL in environment variables

### For Enhancement
1. Train on more data
2. Add batch processing
3. Implement 3D volume support
4. Add authentication
5. Build patient database

## File Upload Support

✅ **Supported formats:**
- PNG images
- JPG/JPEG images
- Max size: 10MB
- Auto-resized to 256×256

## Environment Variables

**Frontend (.env.local):**
```
VITE_API_URL=http://localhost:8000
```

**Backend (main.py):**
```python
MODEL_PATH = "best_model.pth"
DEVICE = "cuda"  # or "cpu"
INPUT_SIZE = 256
```

## Performance Tips

- Use GPU if available (automatic detection)
- Keep images under 5MB for faster upload
- Close other applications for faster processing
- Modern browsers recommended for better UI

## Important Notes

⚠️ **Please read:**
1. This is a diagnostic aid, not for definitive diagnosis
2. All results must be reviewed by medical professionals
3. Model performance depends on training data quality
4. Ensure proper preprocessing of input images
5. Keep `best_model.pth` file backed up

## Support

If something doesn't work:
1. Check the terminal for error messages
2. Verify all dependencies are installed
3. Ensure ports 8000 and 5173 are available
4. Check that model file exists
5. Review README.md files for detailed info

## What's Included

✅ **Backend:**
- HybridUNet model (Transformer + Boundary-Aware Attention)
- GradCAM visualization
- Medical report generation (HTML/Markdown)
- FastAPI with REST endpoints
- CORS-enabled for frontend

✅ **Frontend:**
- React + Vite
- Tailwind CSS (medical dark theme)
- Image upload with drag-and-drop
- Side-by-side view with opacity control
- Real-time analysis results
- Report download

## Troubleshooting Checklist

- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] Virtual environment activated
- [ ] pip install -r requirements.txt completed
- [ ] npm install completed
- [ ] best_model.pth in backend directory
- [ ] Backend running on localhost:8000
- [ ] Frontend running on localhost:5173
- [ ] No firewall blocking ports 8000/5173

Ready to go! 🚀
