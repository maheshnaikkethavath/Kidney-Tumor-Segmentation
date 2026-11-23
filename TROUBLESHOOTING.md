# Troubleshooting Guide

## Getting Started Issues

### Problem: Python Not Found
```
'python' is not recognized as an internal or external command
```

**Windows Solutions:**
1. Reinstall Python with "Add Python to PATH" checked
2. Use `python3` instead of `python`
3. Use full path: `C:\Python311\python.exe`

**Verify Installation:**
```bash
python --version  # Should show Python 3.8+
```

---

### Problem: Node.js Not Found
```
'npm' is not recognized as an internal or external command
```

**Solution:**
1. Download Node.js from nodejs.org
2. Install with all options selected
3. Restart terminal after installation
4. Verify: `node --version` and `npm --version`

---

## Backend Setup Issues

### Problem: Virtual Environment Activation Fails

**Windows:**
```bash
# May need to run PowerShell as Administrator
# Or try:
.\\venv\\Scripts\\activate.bat

# If still fails:
python -m venv venv
source venv/bin/activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

---

### Problem: pip install Fails

```
ERROR: Could not find a version that satisfies the requirement torch
```

**Solution:**
1. Ensure virtual environment is activated:
   ```bash
   source venv/bin/activate  # Unix
   venv\Scripts\activate     # Windows
   ```

2. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

**For CUDA issues:**
```bash
# CPU version (no GPU needed)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

---

### Problem: "Model file 'best_model.pth' not found"

```
FileNotFoundError: Model file 'best_model.pth' not found
```

**Solution:**
1. Copy your trained model to backend directory:
   ```bash
   cd backend
   cp /path/to/your/best_model.pth ./best_model.pth
   ```

2. Or create dummy model for testing:
   ```bash
   python create_dummy_model.py
   ```

3. Or update MODEL_PATH in main.py:
   ```python
   MODEL_PATH = "/path/to/best_model.pth"
   ```

---

### Problem: Port 8000 Already in Use

```
[Errno 98] Address already in use
```

**Solutions:**

**Option 1** - Find and kill the process:
```bash
# Windows PowerShell (as Administrator)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

**Option 2** - Use different port:
```python
# In main.py, change:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

### Problem: CUDA Out of Memory

```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**Solution:**
```python
# In main.py, change:
DEVICE = "cpu"  # Use CPU instead of GPU
```

Or reduce model size:
```python
# In model initialization:
model = HybridUNet(base_channels=16)  # Smaller model
```

---

### Problem: ImportError After Installing Requirements

```
ModuleNotFoundError: No module named '[package_name]'
```

**Solution:**
1. Ensure virtual environment is active
2. Reinstall requirements:
   ```bash
   pip install --force-reinstall -r requirements.txt
   ```

3. Check Python version:
   ```bash
   python --version  # Should be 3.8+
   ```

---

## Frontend Setup Issues

### Problem: npm install Hangs or Fails

**Solution 1** - Clear cache:
```bash
npm cache clean --force
npm install
```

**Solution 2** - Use different registry:
```bash
npm install --registry https://registry.npmjs.org/
```

**Solution 3** - Delete node_modules and try again:
```bash
rm -r node_modules package-lock.json
npm install
```

---

### Problem: Port 5173 Already in Use

```
Port 5173 is in use
```

**Solution:**
```bash
# Use different port
npm run dev -- --port 5174
```

Or edit vite.config.js:
```javascript
server: {
  port: 5174,  // Change from 5173
}
```

---

### Problem: API Calls Fail with CORS Error

```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution 1** - Backend CORS configuration:
Ensure this is in main.py:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Solution 2** - Check API URL:
Create `.env.local` in frontend:
```
VITE_API_URL=http://localhost:8000
```

**Solution 3** - Verify backend is running:
```bash
curl http://localhost:8000/health
```

---

### Problem: Tailwind CSS Not Compiling

```
Styles not showing, only plain white page
```

**Solution:**
1. Ensure tailwind.config.js includes all src:
   ```javascript
   content: [
     "./index.html",
     "./src/**/*.{js,jsx}"
   ]
   ```

2. Rebuild CSS:
   ```bash
   npm run dev  # Restart dev server
   ```

3. Hard refresh browser:
   ```
   Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
   Clear all cache
   ```

---

### Problem: Images Not Displaying After Upload

**Solution:**
1. Check browser console (F12) for errors
2. Verify backend /predict endpoint works:
   ```bash
   curl -X POST -F "file=@test.png" http://localhost:8000/predict
   ```

3. Ensure image is valid PNG/JPG:
   ```bash
   file test.png
   ```

---

## Common Connection Issues

### Problem: "Failed to Connect - Connection Refused"

```
Unable to connect to http://localhost:8000
```

**Checklist:**
- [ ] Backend running? `python main.py`
- [ ] Port 8000 correct in .env? `VITE_API_URL=http://localhost:8000`
- [ ] Backend model loaded? Check console output
- [ ] Firewall blocking port? Add exception
- [ ] Python virtual environment activated? `source venv/bin/activate`

---

### Problem: Image Upload Fails with "400 Bad Request"

```
Error processing image: [error message]
```

**Check:**
1. Image format: Must be PNG or JPG
2. File size: Must be < 10MB
3. Image readable: Try opening in image viewer
4. Console error: Check browser F12 console

---

### Problem: GradCAM Generation Fails

```
Error generating GradCAM
```

**Solution:**
1. First ensure `/predict` works (image processes successfully)
2. Check target_class is 0-2
3. Try with different image
4. Check backend logs for error details

---

## Performance Issues

### Problem: Very Slow Inference (>5 seconds)

**Causes & Solutions:**

**Using CPU instead of GPU:**
```bash
# Check in main.py output
# If it says "device: cpu", you need GPU or accept slower speed
```

**Model too large:**
```python
# Reduce model size in main.py:
model = HybridUNet(base_channels=16)  # Smaller
```

**System overloaded:**
- Close other applications
- Reduce browser tabs
- Restart computer

---

### Problem: Memory Leak or Gradual Slowdown

**Solution:**
```bash
# Restart the backend
# Kill process and run again:
python main.py
```

---

## File Issues

### Problem: Can't Find Configuration Files

```
.env.local not found
```

**Solution:**
1. Create .env.local in frontend:
   ```bash
   echo "VITE_API_URL=http://localhost:8000" > frontend/.env.local
   ```

2. Or copy from template:
   ```bash
   cp frontend/.env.example frontend/.env.local
   ```

---

### Problem: Lost Uploaded Images

Images are not persisted between sessions.

**Note:** By design, images are stored in browser memory only. To persist:

1. Add to `.gitignore`:
   ```
   /uploads/
   ```

2. Create uploads directory in backend

3. Modify main.py to save images:
   ```python
   import os
   os.makedirs("uploads", exist_ok=True)
   
   # Save uploaded file
   with open(f"uploads/{file.filename}", "wb") as f:
       f.write(await file.read())
   ```

---

## Development Issues

### Problem: Hot Module Reloading Not Working

```
Changes not reflected in browser
```

**Solution:**
1. Check that npm run dev is running
2. Hard refresh browser: `Ctrl+Shift+R`
3. Ensure all files saved
4. Restart dev server:
   ```bash
   Ctrl+C
   npm run dev
   ```

---

### Problem: ESLint Errors Blocking Build

```
Linting error found
```

**Solution:**
```bash
npm run lint -- --fix  # Auto-fix issues
```

Or temporarily disable in vite.config.js:
```javascript
// Comment out lint plugin if needed
```

---

## Testing Utilities

### Health Check

```bash
# Test backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","model_loaded":true,"device":"cuda"}
```

### API Documentation

```
http://localhost:8000/docs
```

Open in browser for interactive API documentation.

### Test Image

Create test_image.py in backend:
```python
import cv2
import numpy as np

# Create dummy CT image
img = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
cv2.imwrite("test.png", img)
```

---

## Getting Help

### For Backend Issues
- Check backend/README.md
- Review main.py console output
- Visit http://localhost:8000/docs

### For Frontend Issues
- Check frontend/README.md
- Open browser console (F12)
- Check Network tab for API calls

### For Model Issues
- Check model.py documentation
- Review training code
- Verify input preprocessing

---

## Debug Mode

### Backend Debug Logging

```python
# In main.py:
import logging
logging.basicConfig(level=logging.DEBUG)

# Or:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
```

### Frontend Debug Console

Press F12 in browser:
- Console: Check for JavaScript errors
- Network: Check API requests
- Application: Check stored data

---

## Quick Checklist

If stuck, go through this checklist:

- [ ] Python 3.8+ installed and in PATH
- [ ] Node.js 16+ installed and in PATH
- [ ] Virtual environment created and activated
- [ ] pip install -r requirements.txt completed (no errors)
- [ ] npm install completed (no errors)
- [ ] best_model.pth in backend directory (or create dummy)
- [ ] Backend starts without errors: `python main.py`
- [ ] Backend health check works: `curl http://localhost:8000/health`
- [ ] Frontend starts without errors: `npm run dev`
- [ ] Frontend loads at http://localhost:5173
- [ ] Can upload test image
- [ ] Prediction works
- [ ] Results display correctly

If any check fails, review that section above.

---

## Still Having Issues?

1. **Review the docs:**
   - QUICKSTART.md - Quick 5-minute setup
   - CONFIGURATION.md - All customization options
   - backend/README.md - Backend details
   - frontend/README.md - Frontend details

2. **Check the logs:**
   - Backend console output
   - Browser console (F12)
   - Network requests (F12 Network tab)

3. **Test endpoints:**
   - Visit http://localhost:8000/docs for API test interface
   - Use curl to test endpoints directly

4. **Verify setup:**
   - Create dummy model: `python create_dummy_model.py`
   - Test health: `curl http://localhost:8000/health`
   - Test API docs: Visit http://localhost:8000/docs

5. **Google the error:**
   - Most issues have solutions online
   - Include error message + library name in search

---

**Version:** 1.0.0
**Last Updated:** April 1, 2026
