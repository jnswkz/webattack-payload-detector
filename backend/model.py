import numpy as np
import onnxruntime as ort
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn

# Get absolute path to model and config files
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "simple_rnn_fixed.onnx"  # Fixed model without classification
COLUMNS_PATH = BASE_DIR / "models" / "columns_fixed.json"
STATS_PATH = BASE_DIR / "models" / "feature_stats_fixed.json"

session = None
columns_config = None
feature_stats = None

def load_model():
    global session, columns_config, feature_stats
    try:
        # Load ONNX model
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        session = ort.InferenceSession(str(MODEL_PATH))
        print(f"Model loaded successfully from {MODEL_PATH}")
        
        # Load columns config
        if not COLUMNS_PATH.exists():
            raise FileNotFoundError(f"Columns config not found: {COLUMNS_PATH}")
        with open(COLUMNS_PATH, "r") as f:
            columns_config = json.load(f)
        print(f"Columns config loaded: {columns_config['feature_columns']}")
        
        # Load feature stats
        if not STATS_PATH.exists():
            raise FileNotFoundError(f"Feature stats not found: {STATS_PATH}")
        with open(STATS_PATH, "r") as f:
            feature_stats = json.load(f)
        print(f"Feature stats loaded for {len(feature_stats)} features")
        
    except Exception as e:
        print(f"Error loading model: {e}")
        raise e

def preprocess_request(raw_request: Dict[str, Any]) -> np.ndarray:
    """
    Convert raw HTTP request data to normalized features.
    Uses 7 features (no classification column - that was data leakage).
    """
    features = []
    
    for column in columns_config["feature_columns"]:
        raw_value = raw_request.get(column, None)
        encoding_map = columns_config["encodings"].get(column, {})
        
        if raw_value is not None and str(raw_value) in encoding_map:
            encoded_value = encoding_map[str(raw_value)]
        else:
            # Unknown value - use mean (neutral in z-score)
            encoded_value = feature_stats[column]["mean"]
        
        # Z-score normalize
        mean = feature_stats[column]["mean"]
        std = feature_stats[column]["std"]
        normalized_value = (encoded_value - mean) / std if std > 0 else 0.0
        features.append(normalized_value)
    
    return np.array(features, dtype=np.float32)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield

# Initialize FastAPI app
app = FastAPI(
    title="Web Attack Payload Detector",
    description="API for detecting web attack payloads using RNN model",
    version="1.0.0",
    lifespan=lifespan
)

# Request/Response models
class RawHttpRequest(BaseModel):
    """
    Raw HTTP request fields matching the training data columns.
    All fields are strings (ordinal encoded during training).
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "Method": "GET",
                "host": "localhost:8080",
                "cookie": "JSESSIONID=1F767F17239C9B670A39E9B10C3825F4",
                "connection": "close",
                "lenght": None,
                "content": None,
                "URL": "http://localhost:8080/tienda1/index.jsp HTTP/1.1"
            }
        }
    )
    Method: Optional[str] = None
    host: Optional[str] = None
    cookie: Optional[str] = None
    connection: Optional[str] = None
    lenght: Optional[str] = None  # String like "Content-Length: 68" or None
    content: Optional[str] = None  # POST body content or None
    URL: Optional[str] = None

class PredictionRequest(BaseModel):
    """Pre-normalized feature values (8 features required)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "features": [0.1, -0.5, 0.3, 0.8, -0.2, 0.0, 0.5, 0.2]
            }
        }
    )
    features: List[float]

class PredictionResponse(BaseModel):
    prediction: int  # 0 = Normal, 1 = Attack
    probability: float
    label: str

class BatchRawRequest(BaseModel):
    requests: List[RawHttpRequest]

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    config_loaded: bool

# Endpoints
@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Web Attack Payload Detector API",
        "docs": "/docs",
        "endpoints": {
            "/predict": "POST - Predict with pre-normalized features",
            "/predict/raw": "POST - Predict with raw HTTP request data",
            "/predict/batch": "POST - Batch prediction with raw requests",
            "/health": "GET - Health check",
            "/model/info": "GET - Model information"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy" if session and columns_config and feature_stats else "unhealthy",
        model_loaded=session is not None,
        config_loaded=columns_config is not None and feature_stats is not None
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Predict using pre-normalized feature values.
    Features should be z-score normalized (8 features required).
    """
    if session is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        features = np.array(request.features, dtype=np.float32)
        input_data = features.reshape(1, -1, 1)
        
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: input_data})
        probability = float(outputs[0][0][0])
        
        prediction = 1 if probability >= 0.5 else 0
        label = "Attack" if prediction == 1 else "Normal"
        
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            label=label
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

@app.post("/predict/raw", response_model=PredictionResponse)
async def predict_raw(request: RawHttpRequest):
    """
    Predict using raw HTTP request data.
    The API will handle encoding and normalization automatically.
    """
    if session is None or columns_config is None or feature_stats is None:
        raise HTTPException(status_code=503, detail="Model or config not loaded")
    
    try:
        # Convert to dict and preprocess
        raw_data = request.model_dump()
        features = preprocess_request(raw_data)
        input_data = features.reshape(1, -1, 1)
        
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: input_data})
        probability = float(outputs[0][0][0])
        
        prediction = 1 if probability >= 0.5 else 0
        label = "Attack" if prediction == 1 else "Normal"
        
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            label=label
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchRawRequest):
    """
    Predict multiple raw HTTP requests at once.
    """
    if session is None or columns_config is None or feature_stats is None:
        raise HTTPException(status_code=503, detail="Model or config not loaded")
    
    try:
        predictions = []
        input_name = session.get_inputs()[0].name
        
        for raw_request in request.requests:
            raw_data = raw_request.model_dump()
            features = preprocess_request(raw_data)
            input_data = features.reshape(1, -1, 1)
            
            outputs = session.run(None, {input_name: input_data})
            probability = float(outputs[0][0][0])
            
            prediction = 1 if probability >= 0.5 else 0
            label = "Attack" if prediction == 1 else "Normal"
            
            predictions.append(PredictionResponse(
                prediction=prediction,
                probability=probability,
                label=label
            ))
        
        return BatchPredictionResponse(predictions=predictions)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch prediction error: {str(e)}")

@app.get("/model/info")
async def model_info():
    """
    Get information about the loaded model and configuration.
    """
    if session is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    
    return {
        "model": {
            "inputs": [{"name": i.name, "shape": i.shape, "type": i.type} for i in inputs],
            "outputs": [{"name": o.name, "shape": o.shape, "type": o.type} for o in outputs]
        },
        "feature_columns": columns_config["feature_columns"] if columns_config else None,
        "num_features": len(columns_config["feature_columns"]) if columns_config else None
    }

@app.post("/debug/predict")
async def debug_predict(request: PredictionRequest):
    """
    Debug endpoint to see raw model output.
    """
    if session is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        features = np.array(request.features, dtype=np.float32)
        input_data = features.reshape(1, -1, 1)
        
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: input_data})
        
        return {
            "input_shape": input_data.shape,
            "input_values": input_data.tolist(),
            "raw_output": outputs[0].tolist(),
            "probability": float(outputs[0][0][0]),
            "prediction": 1 if float(outputs[0][0][0]) >= 0.5 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/debug/preprocess")
async def debug_preprocess(request: RawHttpRequest):
    """
    Debug endpoint to see preprocessing steps.
    """
    if columns_config is None or feature_stats is None:
        raise HTTPException(status_code=503, detail="Config not loaded")
    
    raw_data = request.model_dump()
    features = preprocess_request(raw_data)
    
    return {
        "raw_input": raw_data,
        "feature_columns": columns_config["feature_columns"],
        "normalized_features": features.tolist()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)