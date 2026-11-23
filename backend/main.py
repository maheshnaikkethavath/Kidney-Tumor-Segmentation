import os
import io
import base64
import cv2
import numpy as np
import torch
from contextlib import asynccontextmanager
from typing import Dict, Any, Tuple, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from model import HybridUNet
from gradcam import GradCAM
from generate_report import ReportGenerator

# Configuration
MODEL_PATH = "best_model.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NORMALIZE_MEAN = 0.5
NORMALIZE_STD = 0.5
INPUT_SIZE = 256

# Model registry: maps model name to (checkpoint_path, display_name, use_transformer, use_baa)
MODEL_REGISTRY = {
    "best_model": {
        "path": "best_model.pth",
        "display_name": "HybridUNet",
        "use_transformer": True,
        "use_baa": True,
    },
    "unet_only": {
        "path": "unetmodel.pth",
        "display_name": "U-Net",
        "use_transformer": False,
        "use_baa": False,
    },
    "unet_transformer": {
        "path": "unetandtrans.pth",
        "display_name": "U-Net + Transformer",
        "use_transformer": True,
        "use_baa": False,
    },
}


# Initialize FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, clean up on shutdown."""
    try:
        load_model()
        print("✓ Model loaded successfully on startup")
    except Exception as e:
        print(f"✗ Error loading model on startup: {e}")
        import traceback

        traceback.print_exc()
    yield


app = FastAPI(
    title="Medical Imaging API",
    description="Kidney & Tumor Segmentation API with HybridUNet",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
# Note: allow_credentials=True is incompatible with allow_origins=["*"] in browsers.
# Use specific origins if credentials are needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global models and GradCAM instance
models: Dict[str, HybridUNet] = {}
model: Optional[HybridUNet] = None  # Keep for backward compatibility
gradcam: Optional[GradCAM] = None


def load_model():
    """Load all available models from checkpoints."""
    global model, gradcam, models

    for name, config in MODEL_REGISTRY.items():
        path = config["path"]
        if not os.path.exists(path):
            print(f"Warning: Model file '{path}' not found, skipping '{name}'")
            continue

        print(f"Loading model '{name}' from {path}...")
        m = HybridUNet(
            n_channels=1,
            n_classes=3,
            use_transformer=config["use_transformer"],
            use_baa=config["use_baa"],
        )
        m.load_from_checkpoint(path, device=DEVICE)
        models[name] = m
        print(f"✓ Model '{name}' ({config['display_name']}) loaded successfully")

    if not models:
        raise FileNotFoundError(
            "No model files found. Please ensure at least one model checkpoint exists."
        )

    # Set primary model for backward compatibility
    if "best_model" in models:
        model = models["best_model"]
        gradcam = GradCAM(model, target_layer="up4.conv.double_conv")
        print(f"Primary model set to 'best_model' on device: {DEVICE}")


def preprocess_image(image_array: np.ndarray) -> torch.Tensor:
    """
    Preprocess image for model inference.

    Args:
        image_array: Input image as numpy array (H, W) or (H, W, 3)

    Returns:
        Preprocessed tensor (1, 1, 256, 256)
    """
    # Convert to grayscale if needed
    if len(image_array.shape) == 3:
        image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

    # Resize to 256x256
    image_resized = cv2.resize(image_array, (INPUT_SIZE, INPUT_SIZE))

    # Normalize to [0, 1]
    image_normalized = image_resized.astype(np.float32) / 255.0

    # Apply mean-std normalization
    image_normalized = (image_normalized - NORMALIZE_MEAN) / NORMALIZE_STD

    # Convert to tensor
    tensor = torch.from_numpy(image_normalized).unsqueeze(0).unsqueeze(0)
    tensor = tensor.to(DEVICE)

    return tensor


def postprocess_mask(mask: torch.Tensor) -> Tuple[np.ndarray, np.ndarray]:
    """
    Postprocess model output to segmentation mask.

    Args:
        mask: Model output (1, 3, 256, 256)

    Returns:
        Tuple of (class_mask, color_mask)
            - class_mask: Argmax mask (0, 1, 2) as numpy array
            - color_mask: RGB colored mask
    """
    # Get class predictions
    class_mask = mask.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)

    # Create colored mask (values are in RGB — matches PIL's Image.fromarray expectation)
    color_mask = np.zeros((INPUT_SIZE, INPUT_SIZE, 3), dtype=np.uint8)
    color_mask[class_mask == 0] = [0, 0, 0]  # Background: Black
    color_mask[class_mask == 1] = [0, 188, 212]  # Kidney: Cyan (RGB)
    color_mask[class_mask == 2] = [255, 0, 0]  # Tumor: Red (RGB)

    # No cvtColor needed — color_mask is already RGB for PIL
    return class_mask, color_mask


def mask_to_base64(mask: np.ndarray) -> str:
    """Convert numpy array to base64 PNG string."""
    # Convert to RGB if grayscale
    if len(mask.shape) == 2:
        mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    else:
        mask_rgb = mask

    # Convert to PIL Image and encode as PNG
    image_pil = Image.fromarray(mask_rgb)
    buffer = io.BytesIO()
    image_pil.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode to base64
    b64_string = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return b64_string


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"status": "ok", "model_loaded": model is not None, "device": DEVICE}


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Predict segmentation mask for uploaded CT slice image.

    Args:
        file: Uploaded image file (PNG, JPG)

    Returns:
        Dict containing:
            - mask_b64: Base64 encoded segmentation mask PNG
            - tumor_detected: Boolean indicating tumor detection
            - tumor_area_pixels: Number of pixels classified as tumor
            - tumor_percentage: Percentage of image containing tumor
            - class_distribution: Pixel counts per class
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=f"Model not loaded. Please ensure '{MODEL_PATH}' exists in the backend directory.",
        )

    try:
        # Read image
        contents = await file.read()
        image_array = cv2.imdecode(
            np.frombuffer(contents, np.uint8), cv2.IMREAD_GRAYSCALE
        )

        if image_array is None:
            raise ValueError("Failed to read image file")

        # Preprocess
        input_tensor = preprocess_image(image_array)

        # Inference
        with torch.no_grad():
            output, edge_map = model(input_tensor)

        # Postprocess
        class_mask, color_mask = postprocess_mask(output)

        # Calculate confidence scores (softmax probabilities)
        probabilities = torch.nn.functional.softmax(output, dim=1)
        confidence_scores = {
            "background": float(probabilities[0, 0].max().item()) * 100,
            "kidney": float(probabilities[0, 1].max().item()) * 100,
            "tumor": float(probabilities[0, 2].max().item()) * 100,
        }

        # Calculate metrics
        total_pixels = INPUT_SIZE * INPUT_SIZE
        tumor_pixels = np.sum(class_mask == 2)
        kidney_pixels = np.sum(class_mask == 1)
        background_pixels = np.sum(class_mask == 0)

        tumor_detected = tumor_pixels > 0
        tumor_percentage = (
            (tumor_pixels / total_pixels) * 100 if tumor_pixels > 0 else 0.0
        )

        # Convert mask to base64
        mask_b64 = mask_to_base64(color_mask)

        return {
            "mask_b64": mask_b64,
            "tumor_detected": bool(tumor_detected),
            "tumor_area_pixels": int(tumor_pixels),
            "tumor_percentage": float(tumor_percentage),
            "tumor_confidence": float(confidence_scores["tumor"]),
            "confidence_scores": confidence_scores,
            "class_distribution": {
                "background_pixels": int(background_pixels),
                "kidney_pixels": int(kidney_pixels),
                "tumor_pixels": int(tumor_pixels),
            },
            "input_shape": (int(image_array.shape[0]), int(image_array.shape[1])),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


@app.post("/gradcam")
async def generate_gradcam(
    file: UploadFile = File(...), target_class: int = 2
) -> Dict[str, Any]:
    """
    Generate GradCAM attention heatmap for specified class.

    Args:
        file: Uploaded image file (PNG, JPG)
        target_class: Target class index (0=Background, 1=Kidney, 2=Tumor)

    Returns:
        Dict containing:
            - heatmap_b64: Base64 encoded heatmap PNG
            - overlay_b64: Base64 encoded original image with heatmap overlay
            - target_class: Target class used for heatmap
    """
    if model is None or gradcam is None:
        raise HTTPException(
            status_code=503,
            detail=f"Model not loaded. Please ensure '{MODEL_PATH}' exists in the backend directory.",
        )

    if target_class not in [0, 1, 2]:
        raise HTTPException(
            status_code=400,
            detail="target_class must be 0 (Background), 1 (Kidney), or 2 (Tumor)",
        )

    try:
        # Read image
        contents = await file.read()
        image_array = cv2.imdecode(
            np.frombuffer(contents, np.uint8), cv2.IMREAD_GRAYSCALE
        )

        if image_array is None:
            raise ValueError("Failed to read image file")

        # Preprocess
        input_tensor = preprocess_image(image_array)

        # Generate GradCAM
        heatmap = gradcam.generate(input_tensor, class_idx=target_class)

        # Convert heatmap to colored version
        heatmap_colored = gradcam.get_heatmap_with_colormap(heatmap)

        # Convert original image to RGB for overlay
        original_rgb = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)

        # Create overlay
        overlay = gradcam.overlay_heatmap(original_rgb, heatmap, alpha=0.5)

        # Convert to base64
        heatmap_b64 = mask_to_base64(heatmap_colored)
        overlay_b64 = mask_to_base64(overlay)

        class_names = {0: "Background", 1: "Kidney", 2: "Tumor"}

        return {
            "heatmap_b64": heatmap_b64,
            "overlay_b64": overlay_b64,
            "target_class": target_class,
            "target_class_name": class_names[target_class],
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error generating GradCAM: {str(e)}"
        )


@app.post("/report")
async def generate_report(
    file: UploadFile = File(...),
    patient_id: str = "Unknown",
    patient_name: str = "Unknown",
    report_format: str = "markdown",
) -> Dict[str, Any]:
    """
    Generate medical report for segmentation results.

    Args:
        file: Uploaded image file (PNG, JPG)
        patient_id: Patient ID for report
        patient_name: Patient name for report
        report_format: Format of report ('markdown' or 'html')

    Returns:
        Dict containing:
            - report: Generated report content
            - report_format: Format of the report
            - tumor_detected: Whether tumor was detected
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=f"Model not loaded. Please ensure '{MODEL_PATH}' exists in the backend directory.",
        )

    try:
        # Read image
        contents = await file.read()
        image_array = cv2.imdecode(
            np.frombuffer(contents, np.uint8), cv2.IMREAD_GRAYSCALE
        )

        if image_array is None:
            raise ValueError("Failed to read image file")

        # Preprocess
        input_tensor = preprocess_image(image_array)

        # Inference
        with torch.no_grad():
            output, edge_map = model(input_tensor)

        # Postprocess
        class_mask, _ = postprocess_mask(output)

        # Calculate metrics
        total_pixels = INPUT_SIZE * INPUT_SIZE
        tumor_pixels = np.sum(class_mask == 2)
        tumor_detected = tumor_pixels > 0
        tumor_percentage = (
            (tumor_pixels / total_pixels) * 100 if tumor_pixels > 0 else 0.0
        )

        # Generate report
        report_gen = ReportGenerator(patient_id=patient_id, patient_name=patient_name)

        if report_format == "html":
            report_content = report_gen.generate_html_report(
                tumor_detected=tumor_detected,
                tumor_area_pixels=int(tumor_pixels),
                image_size=INPUT_SIZE,
                tumor_percentage=float(tumor_percentage),
            )
        else:
            report_content = report_gen.generate_markdown_report(
                tumor_detected=tumor_detected,
                tumor_area_pixels=int(tumor_pixels),
                image_size=INPUT_SIZE,
                tumor_percentage=float(tumor_percentage),
            )

        return {
            "report": report_content,
            "report_format": report_format,
            "tumor_detected": bool(tumor_detected),
            "tumor_area_pixels": int(tumor_pixels),
            "tumor_percentage": float(tumor_percentage),
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error generating report: {str(e)}"
        )


def create_svg_from_mask(mask: np.ndarray) -> str:
    """Create SVG representation from segmentation mask with legend."""
    # Embed PNG in SVG
    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB) if len(mask.shape) == 2 else mask
    image_pil = Image.fromarray(mask_rgb)
    buffer = io.BytesIO()
    image_pil.save(buffer, format="PNG")
    buffer.seek(0)
    img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    height = mask.shape[0]
    width = mask.shape[1]
    scale = 2

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width * scale}" height="{height * scale + 60}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Background -->
    <rect width="{width * scale}" height="{height * scale + 60}" fill="white"/>
    
    <!-- Segmentation Image -->
    <image x="0" y="0" width="{width * scale}" height="{height * scale}" xlink:href="data:image/png;base64,{img_b64}"/>
    
    <!-- Legend -->
    <text x="10" y="{height * scale + 20}" font-size="12" font-weight="bold" fill="#333">Segmentation Legend:</text>
    
    <!-- Background Color -->
    <rect x="10" y="{height * scale + 25}" width="15" height="15" fill="#000000"/>
    <text x="30" y="{height * scale + 37}" font-size="11" fill="#333">Background</text>
    
    <!-- Kidney Color -->
    <rect x="130" y="{height * scale + 25}" width="15" height="15" fill="#00bcd4"/>
    <text x="150" y="{height * scale + 37}" font-size="11" fill="#333">Kidney</text>
    
    <!-- Tumor Color -->
    <rect x="220" y="{height * scale + 25}" width="15" height="15" fill="#ff0000"/>
    <text x="240" y="{height * scale + 37}" font-size="11" fill="#333">Tumor</text>
</svg>'''

    return svg


def run_inference_for_model(
    model_inst: HybridUNet,
    input_tensor: torch.Tensor,
    model_name: str,
    display_name: str,
) -> Dict[str, Any]:
    """Run inference with a single model and return formatted results."""
    with torch.no_grad():
        output, edge_map = model_inst(input_tensor)

    class_mask, color_mask = postprocess_mask(output)

    probabilities = torch.nn.functional.softmax(output, dim=1)
    confidence_scores = {
        "background": float(probabilities[0, 0].max().item()) * 100,
        "kidney": float(probabilities[0, 1].max().item()) * 100,
        "tumor": float(probabilities[0, 2].max().item()) * 100,
    }

    total_pixels = INPUT_SIZE * INPUT_SIZE
    tumor_pixels = int(np.sum(class_mask == 2))
    kidney_pixels = int(np.sum(class_mask == 1))
    background_pixels = int(np.sum(class_mask == 0))

    tumor_detected = tumor_pixels > 0
    tumor_percentage = (tumor_pixels / total_pixels) * 100 if tumor_pixels > 0 else 0.0

    mask_b64 = mask_to_base64(color_mask)

    return {
        "model_name": model_name,
        "display_name": display_name,
        "mask_b64": mask_b64,
        "tumor_detected": bool(tumor_detected),
        "tumor_area_pixels": tumor_pixels,
        "tumor_percentage": float(tumor_percentage),
        "tumor_confidence": float(confidence_scores["tumor"]),
        "confidence_scores": confidence_scores,
        "class_distribution": {
            "background_pixels": background_pixels,
            "kidney_pixels": kidney_pixels,
            "tumor_pixels": tumor_pixels,
        },
    }


@app.post("/compare")
async def compare_models(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Run inference with all loaded models and return results for comparison.

    Args:
        file: Uploaded image file (PNG, JPG)

    Returns:
        Dict containing results from each model keyed by model name.
    """
    if not models:
        raise HTTPException(status_code=503, detail="No models loaded.")

    try:
        contents = await file.read()
        image_array = cv2.imdecode(
            np.frombuffer(contents, np.uint8), cv2.IMREAD_GRAYSCALE
        )

        if image_array is None:
            raise ValueError("Failed to read image file")

        input_tensor = preprocess_image(image_array)

        results = {}
        for name, model_inst in models.items():
            display_name = MODEL_REGISTRY[name]["display_name"]
            results[name] = run_inference_for_model(
                model_inst, input_tensor, name, display_name
            )

        return {
            "results": results,
            "input_shape": (int(image_array.shape[0]), int(image_array.shape[1])),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error comparing models: {str(e)}")


@app.get("/models")
async def list_models() -> Dict[str, Any]:
    """List all available models."""
    available = {}
    for name, config in MODEL_REGISTRY.items():
        available[name] = {
            "display_name": config["display_name"],
            "loaded": name in models,
        }
    return {"models": available}


@app.post("/export-segmentation")
async def export_segmentation(
    file: UploadFile = File(...), format: str = "png"
) -> Dict[str, Any]:
    """
    Export segmentation mask as PNG or SVG.

    Args:
        file: Uploaded image file (PNG, JPG)
        format: Export format ('png' or 'svg')

    Returns:
        Dict containing base64 encoded image data and filename
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Read image
        contents = await file.read()
        image_array = cv2.imdecode(
            np.frombuffer(contents, np.uint8), cv2.IMREAD_GRAYSCALE
        )

        if image_array is None:
            raise ValueError("Failed to read image file")

        # Preprocess and predict
        input_tensor = preprocess_image(image_array)
        with torch.no_grad():
            output, edge_map = model(input_tensor)

        class_mask, color_mask = postprocess_mask(output)

        format_lower = format.lower().strip()

        if format_lower == "png":
            # Return PNG as base64
            mask_b64 = mask_to_base64(color_mask)
            return {
                "data": mask_b64,
                "format": "png",
                "filename": "segmentation.png",
                "mime_type": "image/png",
            }

        elif format_lower == "svg":
            # Convert to SVG
            svg_data = create_svg_from_mask(color_mask)
            svg_b64 = base64.b64encode(svg_data.encode("utf-8")).decode("utf-8")

            return {
                "data": svg_b64,
                "format": "svg",
                "filename": "segmentation.svg",
                "mime_type": "image/svg+xml",
            }

        else:
            raise HTTPException(
                status_code=400, detail="Unsupported format. Use 'png' or 'svg'"
            )

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error exporting segmentation: {str(e)}"
        )


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Medical Imaging API - Kidney & Tumor Segmentation",
        "endpoints": {
            "health": "/health",
            "predict": "/predict (POST)",
            "gradcam": "/gradcam (POST)",
            "report": "/report (POST)",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
