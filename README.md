# KOCCA 3D Scene Generation API

A powerful REST API that generates 3D scenes from text descriptions using advanced AI algorithms. This project combines layout synthesis, object retrieval, and scene composition to create realistic 3D environments in GLB format.

## 🏗️ Architecture

The system uses a multi-stage pipeline:
1. **Text Analysis** - OpenAI GPT processes natural language descriptions
2. **Layout Synthesis** - Generates spatial arrangements and room layouts  
3. **Object Retrieval** - Finds and selects appropriate 3D models from dataset
4. **Scene Composition** - Assembles final 3D scene with proper positioning and lighting

## 📋 Requirements

- **Python**: 3.8+
- **OS**: Linux (Ubuntu 18.04+ recommended)
- **GPU**: CUDA-compatible GPU with 8GB+ VRAM (optional but recommended)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB+ for full 3D-FUTURE dataset

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/KAIST-VML/KOCCA-SceneGeneration.git
cd KOCCA-SceneGeneration

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
set -a                
source config.env     # modify it before you use
set +a
```

### Dataset Setup

This project requires the **3D-FUTURE dataset** for 3D object models:

```bash
# Create dataset directory
mkdir -p dataset

# Download 3D-FUTURE dataset (registration required)
# Visit: https://tianchi.aliyun.com/specials/promotion/alibaba-3d-future
# Download all parts and extract to dataset/ directory

# Expected structure after extraction:
# dataset/
# ├── 3D-FUTURE-model-part1/
# ├── 3D-FUTURE-model-part2/
# ├── 3D-FUTURE-model-part3/
# └── 3D-FUTURE-model-part4/
```

#### 3D-FUTURE Dataset Information
- **Provider**: 3D-FUTURE: 3D Furniture Shape with Texture provided by Tao Bao (China) Software Co., Ltd. 本数据集由淘宝提供
- **Competition**: IJCAI-PRICAI 2020 3D AI Challenge: Instance Segmentation
- **Registration**: https://tianchi.aliyun.com/competition/entrance/231787/information
- **Website**: https://tianchi.aliyun.com/specials/promotion/alibaba-3d-future
- **Size**: ~40GB total (distributed across 4 parts)
- **Models**: 10,000+ high-quality 3D furniture and room objects

### Configuration

Edit `config.env`:
```bash
# Required: OpenAI API key for text processing
export OPENAI_API_KEY="sk-your-openai-api-key"

# Optional: Custom paths
export SCENE_BASE_PATH="./space-generator"
export SCENE_OUTPUT_DIR="./outputs"
export SCENE_WORK_DIR="."
export export DATASET_BASE_PATH = "your dataset path"
```

### Running the Server

```bash
# Method 1: Using the provided script
bash run.sh

# Method 2: Manual execution
source config.env
python main.py
# ex. 
# python client.py "a cozy living room with a sofa and a coffee table" ./downloads --iterations 200


# Method 3: Production deployment
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will start at `http://localhost:8000`

## 📖 Usage

### Python Client

```python
import requests
from client import SceneGenerationClient

# Initialize client
client = SceneGenerationClient("http://localhost:8000")

# Generate scene
result = client.generate_scene(
    prompt="A modern 4x4 living room with minimalist furniture",
    output_path="./living_room.glb",
    iterations=300
)
```

### Command Line

```bash
# Basic usage
python client.py "A cozy bedroom with wooden furniture" "./bedroom.glb"

# Advanced options
python client.py "A modern kitchen" "./kitchen.glb" \
    --iterations 500 \
    --server-url http://localhost:8000 \
    --check-interval 5
```

### REST API

#### Generate Scene
```bash
curl -X POST http://localhost:8000/api/generate-scene \
  -H "Content-Type: application/json" \
  -d '{
    "scene_descriptor": "A 5x5 modern office space",
    "iterations": 300,
    "openai_api_key": "sk-your-key"
  }'
```

#### Check Status
```bash
curl http://localhost:8000/api/status/{task_id}
```

#### Download Result
```bash
curl http://localhost:8000/download/{task_id} -o scene.glb
```

## 🔧 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health check |
| `POST` | `/api/set-api-key` | Configure OpenAI API key |
| `POST` | `/api/generate-scene` | Start scene generation |
| `GET` | `/api/status/{task_id}` | Check generation progress |
| `GET` | `/download/{task_id}` | Download generated GLB file |

### Request/Response Schemas

#### Scene Generation Request
```json
{
  "scene_descriptor": "string",
  "iterations": 300,
  "openai_api_key": "string"
}
```

#### Status Response
```json
{
  "task_id": "string",
  "status": "processing|completed|failed",
  "stage": "scene_synthesis|text_retrieval|clip_retrieval|scene_composition",
  "progress": 0.75,
  "message": "string",
  "output_file": "string"
}
```

## 📁 Project Structure

```
KOCCA-SceneGeneration/
├── main.py                     # FastAPI server implementation
├── client.py                   # Python client library
├── config.env                  # Environment configuration
├── requirements.txt            # Python dependencies
├── run.sh                      # Server startup script
├── layout_scene_api.sh         # Scene generation pipeline
├── space-generator/            # Core generation algorithms
│   ├── Scene_Synthesis/        # Layout generation module
│   │   ├── models/            # Pre-trained models
│   │   └── utils/             # Utility functions
│   └── retrieval/             # Object retrieval system
│       ├── clip_retrieval.py  # CLIP-based object matching
│       └── text_retrieval.py  # Text-based object search
├── dataset/                    # 3D object dataset (download required)
│   ├── 3D-FUTURE-model-part1/ # Download from Alibaba Tianchi
│   ├── 3D-FUTURE-model-part2/ # Registration required
│   ├── 3D-FUTURE-model-part3/ # ~40GB total size
│   └── 3D-FUTURE-model-part4/ # 10,000+ 3D models
└── outputs/                    # Generated scene files
```

## 🎯 Features

- **Multi-modal Input**: Support for natural language scene descriptions
- **Scalable Architecture**: Async processing with task queue management
- **Rich Object Database**: Integration with 3D-FUTURE dataset (10,000+ models)
- **Format Support**: Outputs industry-standard GLB files
- **Progress Tracking**: Real-time generation progress monitoring
- **RESTful API**: Easy integration with web applications
- **Error Handling**: Comprehensive error reporting and recovery

## 🔧 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black .
isort .

# Type checking
mypy .
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `SCENE_BASE_PATH` | Space generator directory | `./space-generator` |
| `SCENE_OUTPUT_DIR` | Output directory | `./outputs` |
| `SCENE_WORK_DIR` | Working directory | `.` |
| `LOG_LEVEL` | Logging level | `INFO` |

