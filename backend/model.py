import numpy as np
import onnxruntime as ort
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn

# Get absolute path to model and config files
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "sqli_lstm.onnx"
TOKENIZER_PATH = BASE_DIR / "models" / "sqli_tokenizer.json"

session = None
tokenizer_config = None


def normalize_sql_input(text: str) -> str:
    """
    Normalize input to match training data format (add spaces around operators).
    The training data has specific formatting with spaces around operators.
    """
    text = re.sub(r'([=<>!]+)', r'  \1  ', text)  # Operators
    text = re.sub(r'([()])', r'  \1  ', text)      # Parentheses
    text = re.sub(r',', ' , ', text)               # Commas
    text = re.sub(r"'", " ' ", text)               # Single quotes
    text = re.sub(r'"', ' " ', text)               # Double quotes
    text = re.sub(r'\s+', ' ', text)               # Normalize multiple spaces
    return text.strip().lower()


def encode_text(text: str, char_to_idx: dict, max_len: int) -> List[int]:
    """Encode text to sequence of character indices"""
    encoded = []
    for char in text[:max_len]:
        encoded.append(char_to_idx.get(char, char_to_idx.get('<UNK>', 1)))
    
    # Pad if necessary
    pad_idx = char_to_idx.get('<PAD>', 0)
    while len(encoded) < max_len:
        encoded.append(pad_idx)
    
    return encoded


def load_model():
    global session, tokenizer_config
    try:
        # Load ONNX model
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        session = ort.InferenceSession(str(MODEL_PATH))
        print(f"Model loaded successfully from {MODEL_PATH}")
        
        # Load tokenizer config
        if not TOKENIZER_PATH.exists():
            raise FileNotFoundError(f"Tokenizer config not found: {TOKENIZER_PATH}")
        with open(TOKENIZER_PATH, "r", encoding="utf-8") as f:
            tokenizer_config = json.load(f)
        print(f"Tokenizer loaded: vocab_size={tokenizer_config['vocab_size']}, max_len={tokenizer_config['max_len']}")
        
    except Exception as e:
        print(f"Error loading model: {e}")
        raise e


def predict_sqli(text: str) -> tuple[float, str]:
    """
    Predict if a text contains SQL injection.
    Returns (probability, label).
    """
    if session is None or tokenizer_config is None:
        raise RuntimeError("Model not loaded")
    
    # Normalize input to match training data format
    normalized = normalize_sql_input(text)
    
    # Encode to character indices
    char_to_idx = tokenizer_config['char_to_idx']
    max_len = tokenizer_config['max_len']
    encoded = encode_text(normalized, char_to_idx, max_len)
    
    # Prepare input for ONNX (batch_size=1, seq_len=max_len)
    input_data = np.array([encoded], dtype=np.int64)
    
    # Run inference
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: input_data})
    probability = float(outputs[0][0][0])
    
    # Threshold at 0.5
    label = "SQLi" if probability >= 0.5 else "Normal"
    
    return probability, label


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


# Initialize FastAPI app
app = FastAPI(
    title="SQL Injection Detector",
    description="API for detecting SQL injection attacks using LSTM model",
    version="2.0.0",
    lifespan=lifespan
)


# Request/Response models
class TextRequest(BaseModel):
    """Request with text to analyze for SQL injection"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "' OR '1'='1' --"
            }
        }
    )
    text: str


class PredictionResponse(BaseModel):
    prediction: int  # 0 = Normal, 1 = SQLi
    probability: float
    label: str
    normalized_input: Optional[str] = None


class BatchTextRequest(BaseModel):
    texts: List[str]


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    tokenizer_loaded: bool


# Endpoints
@app.get("/", response_model=dict)
async def root():
    return {
        "message": "SQL Injection Detector API",
        "version": "2.0.0",
        "model": "LSTM character-level classifier",
        "docs": "/docs",
        "endpoints": {
            "/predict": "POST - Detect SQLi in text",
            "/predict/batch": "POST - Batch SQLi detection",
            "/health": "GET - Health check",
            "/model/info": "GET - Model information"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy" if session and tokenizer_config else "unhealthy",
        model_loaded=session is not None,
        tokenizer_loaded=tokenizer_config is not None
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: TextRequest):
    """
    Detect SQL injection in the provided text.
    The text will be normalized and analyzed using a character-level LSTM model.
    """
    if session is None or tokenizer_config is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        probability, label = predict_sqli(request.text)
        prediction = 1 if label == "SQLi" else 0
        
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            label=label,
            normalized_input=normalize_sql_input(request.text)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchTextRequest):
    """
    Detect SQL injection in multiple texts at once.
    """
    if session is None or tokenizer_config is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        predictions = []
        for text in request.texts:
            probability, label = predict_sqli(text)
            prediction = 1 if label == "SQLi" else 0
            
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
    Get information about the loaded model and tokenizer.
    """
    if session is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    
    return {
        "model": {
            "type": "LSTM character-level classifier",
            "file": str(MODEL_PATH.name),
            "inputs": [{"name": i.name, "shape": i.shape, "type": i.type} for i in inputs],
            "outputs": [{"name": o.name, "shape": o.shape, "type": o.type} for o in outputs]
        },
        "tokenizer": {
            "vocab_size": tokenizer_config["vocab_size"] if tokenizer_config else None,
            "max_len": tokenizer_config["max_len"] if tokenizer_config else None
        },
        "preprocessing": {
            "normalization": "Adds spaces around operators to match training format",
            "encoding": "Character-level with vocabulary mapping"
        }
    }


@app.post("/debug/predict")
async def debug_predict(request: TextRequest):
    """
    Debug endpoint to see preprocessing and raw model output.
    """
    if session is None or tokenizer_config is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Normalize
        normalized = normalize_sql_input(request.text)
        
        # Encode
        char_to_idx = tokenizer_config['char_to_idx']
        max_len = tokenizer_config['max_len']
        encoded = encode_text(normalized, char_to_idx, max_len)
        
        # Prepare input
        input_data = np.array([encoded], dtype=np.int64)
        
        # Run inference
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: input_data})
        probability = float(outputs[0][0][0])
        
        return {
            "original_text": request.text,
            "normalized_text": normalized,
            "encoded_first_50": encoded[:50],
            "input_shape": list(input_data.shape),
            "raw_output": outputs[0].tolist(),
            "probability": probability,
            "prediction": "SQLi" if probability >= 0.5 else "Normal"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)