# Web Attack Payload Detector

[English](#english) | [日本語](#日本語)

---

## English

### Overview

A machine learning-based web attack detection system that identifies SQL injection (SQLi) attacks in real-time. This project demonstrates how ML models can protect vulnerable web applications by detecting and blocking malicious inputs before they reach the database.

### Features

- 🔍 **SQL Injection Detection**: Character-level LSTM model trained on 30,000+ queries
- 🚀 **Real-time Protection**: FastAPI backend with ONNX runtime for fast inference
- 🌐 **Web Attack Detection**: Additional RNN model for HTTP request analysis
- 🛡️ **Demo Applications**: Vulnerable and secure Flask apps for demonstration

### Project Structure

```
webattack-payload-detector/
├── backend/
│   └── model.py              # FastAPI server with SQLi detection API
├── secure_app/
│   └── app.py                # Flask app protected by ML detection
├── vulnerable_app/
│   └── app.py                # Vulnerable Flask app (for comparison)
├── models/
│   ├── sqli_lstm.onnx        # SQLi detection model (ONNX)
│   ├── sqli_tokenizer.json   # Character tokenizer config
│   ├── simple_rnn_fixed.onnx # HTTP attack detection model
│   └── ...
├── sqli_rnn_training.ipynb   # SQLi LSTM model training notebook
├── web_attack_detection.ipynb # HTTP attack RNN training notebook
├── csic_database.csv         # CSIC 2010 HTTP dataset
└── Modified_SQL_Dataset.csv  # SQL injection dataset
```

### Models

#### 1. SQL Injection Detector (`sqli_lstm.onnx`)
- **Architecture**: Character-level LSTM (Embedding → LSTM → LSTM → Dense)
- **Input**: Raw text (max 223 characters)
- **Output**: Probability of SQL injection (0-1)
- **Accuracy**: ~99% on test set

#### 2. HTTP Attack Detector (`simple_rnn_fixed.onnx`)
- **Architecture**: Simple RNN with normalized HTTP metadata
- **Input**: HTTP request features (Method, URL, cookies, etc.)
- **Output**: Attack probability (0-1)

### Installation

```bash
# Clone the repository
git clone https://github.com/jnswkz/webattack-payload-detector.git
cd webattack-payload-detector

# Install dependencies (requires Python 3.13+)
pip install uv
uv sync
```

### Usage

#### Start the Detection API

```bash
# Start the FastAPI model server
uv run python -m uvicorn backend.model:app --reload --port 8000
```

#### Start the Protected Web App

```bash
# Start the Flask app (protected by ML)
uv run python secure_app/app.py
```

#### API Endpoints

**SQLi Detection API** (http://localhost:8000)

```bash
# Check if input contains SQL injection
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "admin'\'' OR 1=1 --"}'

# Response:
# {"probability": 0.9996, "label": "SQLi", "input_length": 17}
```

### Training the Models

Open the Jupyter notebooks to train the models:

1. **SQL Injection Model**: `sqli_rnn_training.ipynb`
   - Uses `Modified_SQL_Dataset.csv`
   - Character-level tokenization
   - Exports to ONNX via PyTorch

2. **HTTP Attack Model**: `web_attack_detection.ipynb`
   - Uses `csic_database.csv` (CSIC 2010)
   - Feature normalization
   - Exports to ONNX via PyTorch

### Important Notes

⚠️ **Input Normalization Required**: The SQLi model requires input normalization to match the training data format. The backend automatically handles this with the `normalize_sql_input()` function.

### Tech Stack

- **ML Framework**: TensorFlow/Keras, PyTorch
- **Inference**: ONNX Runtime
- **Backend**: FastAPI, Uvicorn
- **Frontend**: Flask, Jinja2
- **Database**: PostgreSQL (Azure)
- **Package Manager**: uv

### License

MIT License

---

## 日本語

### 概要

機械学習を活用したWebアプリケーション攻撃検出システムです。SQLインジェクション（SQLi）攻撃をリアルタイムで検出・ブロックすることで、脆弱なWebアプリケーションを保護する方法を実演します。

### 機能

- 🔍 **SQLインジェクション検出**: 30,000件以上のクエリで学習した文字レベルLSTMモデル
- 🚀 **リアルタイム保護**: ONNX Runtimeを使用したFastAPIバックエンドによる高速推論
- 🌐 **Web攻撃検出**: HTTPリクエスト分析用の追加RNNモデル
- 🛡️ **デモアプリケーション**: 脆弱版と保護版のFlaskアプリを提供

### プロジェクト構成

```
webattack-payload-detector/
├── backend/
│   └── model.py              # SQLi検出APIを提供するFastAPIサーバー
├── secure_app/
│   └── app.py                # ML検出で保護されたFlaskアプリ
├── vulnerable_app/
│   └── app.py                # 脆弱なFlaskアプリ（比較用）
├── models/
│   ├── sqli_lstm.onnx        # SQLi検出モデル（ONNX形式）
│   ├── sqli_tokenizer.json   # 文字トークナイザー設定
│   ├── simple_rnn_fixed.onnx # HTTP攻撃検出モデル
│   └── ...
├── sqli_rnn_training.ipynb   # SQLi LSTMモデルの学習ノートブック
├── web_attack_detection.ipynb # HTTP攻撃RNNの学習ノートブック
├── csic_database.csv         # CSIC 2010 HTTPデータセット
└── Modified_SQL_Dataset.csv  # SQLインジェクションデータセット
```

### モデル

#### 1. SQLインジェクション検出器 (`sqli_lstm.onnx`)
- **アーキテクチャ**: 文字レベルLSTM（Embedding → LSTM → LSTM → Dense）
- **入力**: 生テキスト（最大223文字）
- **出力**: SQLインジェクションの確率（0-1）
- **精度**: テストセットで約99%

#### 2. HTTP攻撃検出器 (`simple_rnn_fixed.onnx`)
- **アーキテクチャ**: 正規化されたHTTPメタデータを使用するSimple RNN
- **入力**: HTTPリクエストの特徴量（メソッド、URL、Cookie等）
- **出力**: 攻撃確率（0-1）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/jnswkz/webattack-payload-detector.git
cd webattack-payload-detector

# 依存関係をインストール（Python 3.13以上が必要）
pip install uv
uv sync
```

### 使い方

#### 検出APIの起動

```bash
# FastAPIモデルサーバーを起動
uv run python -m uvicorn backend.model:app --reload --port 8000
```

#### 保護されたWebアプリの起動

```bash
# Flaskアプリを起動（ML保護付き）
uv run python secure_app/app.py
```

#### APIエンドポイント

**SQLi検出API** (http://localhost:8000)

```bash
# 入力にSQLインジェクションが含まれているか確認
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "admin'\'' OR 1=1 --"}'

# レスポンス:
# {"probability": 0.9996, "label": "SQLi", "input_length": 17}
```

### モデルの学習

Jupyterノートブックを開いてモデルを学習できます：

1. **SQLインジェクションモデル**: `sqli_rnn_training.ipynb`
   - `Modified_SQL_Dataset.csv`を使用
   - 文字レベルのトークン化
   - PyTorch経由でONNXにエクスポート

2. **HTTP攻撃モデル**: `web_attack_detection.ipynb`
   - `csic_database.csv`（CSIC 2010）を使用
   - 特徴量の正規化
   - PyTorch経由でONNXにエクスポート

### 重要な注意事項

⚠️ **入力の正規化が必要**: SQLiモデルは学習データの形式に合わせた入力の正規化が必要です。バックエンドでは`normalize_sql_input()`関数で自動的に処理されます。

### 技術スタック

- **MLフレームワーク**: TensorFlow/Keras、PyTorch
- **推論**: ONNX Runtime
- **バックエンド**: FastAPI、Uvicorn
- **フロントエンド**: Flask、Jinja2
- **データベース**: PostgreSQL（Azure）
- **パッケージマネージャー**: uv

### ライセンス

MIT License
