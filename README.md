<div align="center">

# 🚀 LLM Cost Autopilot
### *Intelligent Multi-Model LLM Gateway & Cost Optimization Router*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1.svg?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Observability-000000.svg?logo=opentelemetry&logoColor=white)](https://opentelemetry.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Cut your LLM API inference costs by up to **80%** without sacrificing quality using intelligent prompt complexity classification, semantic vector caching, resilience fallbacks, and automated model benchmarking.*

---

</div>

## 📌 Overview

**LLM Cost Autopilot** is an enterprise-grade AI gateway designed to dynamically analyze incoming user prompts, predict task complexity, and route requests to the most cost-effective Large Language Model (e.g., **Google Gemini Flash 1.5**, **OpenAI GPT-4o-mini**, **Anthropic Claude 3.5 Sonnet**, or local **Ollama Llama 3**).

By placing LLM Cost Autopilot in front of your applications, simple queries (like translations or short summaries) are handled by lightning-fast, low-cost models, while complex tasks (like system architecture or algorithm design) are seamlessly escalated to premium models.

---

## ✨ Key Features

- 🧠 **Dual-Engine Complexity Classification**: Uses a trained **Logistic Regression ML model** over sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`) with automatic fallback to a **7-Heuristic Rule Engine** (regex code/SQL/math detection, word count, constraint density).
- ⚡ **Semantic Vector Caching**: Powered by **PostgreSQL + `pgvector`**. Identifies similar queries ($\ge 92\%$ cosine similarity) and returns stored responses instantly for **$0 cost** and **<10ms latency**.
- 🚦 **Dynamic Multi-Provider Routing**: Automatically maps task complexity (`LOW`, `MEDIUM`, `HIGH`) to registered LLMs in `models.yaml`.
- 🛡️ **Fault-Tolerant Resilience**:
  - **Provider Health Checks**: Verifies API readiness before routing.
  - **Rate Limit Cooldowns**: Automatically handles HTTP 429 rate limits by enforcing a 60-second backoff and skipping to secondary fallback providers.
- 🕵️ **Shadow Evaluation**: Asynchronously samples 5% of cheap model requests in the background, runs them against premium models, and computes response equivalence via embeddings/LLM Judge.
- 🔄 **Self-Healing Feedback Loop**: Captures user negative feedback (`/v1/feedback`) and shadow evaluation quality gaps to automatically retrain the router ML model.
- 📊 **Full Observability Stack**: Native support for **OpenTelemetry**, **Prometheus**, **Grafana**, and **Redis**.
- 🧪 **Multi-Model Benchmark & Dolly 15k Integrations**: Built-in dataset tools to benchmark candidate LLMs using **Databricks Dolly 15k** and custom prompt generators.

---

## 🏗️ System Architecture

```text
                                  ┌───────────────────────────────┐
                                  │      Client Application       │
                                  └───────────────┬───────────────┘
                                                  │ POST /v1/chat
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │    FastAPI Gateway Server     │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │     Semantic Vector Cache     │
                                  │    (PostgreSQL + pgvector)    │
                                  └───────┬───────────────┬───────┘
                                          │               │
                              CACHE HIT   │               │ CACHE MISS
                     (Similarity >= 92%)  │               │
                                          ▼               ▼
                                 ┌─────────┐     ┌────────────────────────┐
                                 │ $0 COST │     │   Classifier Engine    │
                                 │ < 10ms  │     │  (ML + Heuristic Rules)│
                                 └─────────┘     └────────┬───────────────┘
                                                          │
                                         Maps Complexity  │ (LOW / MEDIUM / HIGH)
                                                          ▼
                                                 ┌────────────────────────┐
                                                 │   Intelligent Router   │
                                                 │(Health & Cooldown Check│
                                                 └────────┬───────────────┘
                                                          │
               ┌───────────────────────────┬──────────────┴───────────────┬───────────────────────────┐
               │ LOW                       │ MEDIUM                       │ HIGH                      │ LOCAL
               ▼                           ▼                              ▼                           ▼
 ┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────┐
 │ Google Gemini Flash 1.5  │ │   OpenAI GPT-4o-mini     │ │ Anthropic Claude 3.5     │ │    Ollama (Llama 3)      │
 │     ($0.075 / 1M)        │ │      ($0.15 / 1M)        │ │      ($3.00 / 1M)        │ │       ($0.00 / 1M)       │
 └──────────────────────────┘ └──────────────────────────┘ └──────────────────────────┘ └──────────────────────────┘
```

---

## 📁 Repository Structure

```text
LLM_Autopilot/
├── api/
│   ├── main.py                     # FastAPI server routes (/v1/chat, /v1/feedback, /health)
│   └── telemetry.py                # OpenTelemetry & Prometheus instrumentation
├── router/
│   ├── intelligent_router.py       # Core routing engine, fallback chains, cost & savings math
│   ├── classifier.py               # ML-based Logistic Regression complexity classifier
│   ├── rule_engine.py               # Heuristic-based regex fallback rule engine
│   └── semantic_cache.py           # PostgreSQL + pgvector embedding storage & lookup
├── providers/
│   ├── init.py                     # BaseProvider abstract class definition
│   ├── Openai_llm_provider.py      # OpenAI & OpenRouter provider implementation
│   ├── gemini_provider.py          # Gemini provider wrapper
│   ├── anthropic_provider.py       # Claude provider wrapper
│   └── ollama_provider.py         # Local Ollama provider wrapper
├── DATASET_BUILDER/
│   ├── benchmark_dataset_builder.py# Multi-model benchmarking & LLM Judge evaluator
│   ├── prepare_dolly_dataset.py    # Databricks Dolly 15k dataset downloader & parser
│   └── train_classifier.py         # ML model training script (exports classifier_model.joblib)
├── docker-compose.yml              # Multi-container stack (Postgres + pgvector, Redis, OTel, Grafana)
├── models.yaml                     # Model registry configuration (pricing, quality, providers)
├── requirements.txt                # Python package dependencies
└── README.md                       # Project documentation
```

---

## ⚡ Quick Start

### 1. Prerequisites
- [Python 3.10+](https://www.python.org/)
- [Docker & Docker Compose](https://www.docker.com/)

### 2. Environment Setup
Clone the repository and install dependencies:
```bash
git clone https://github.com/your-username/LLM_Autopilot.git
cd LLM_Autopilot
pip install -r requirements.txt
```

Set your OpenRouter or OpenAI API Key:
```bash
# On Linux/macOS
export OPENROUTER_API_KEY="your_openrouter_api_key_here"

# On Windows PowerShell
$env:OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

### 3. Start Database & Infrastructure
Launch PostgreSQL (`pgvector`), Redis, OpenTelemetry Collector, Prometheus, and Grafana using Docker Compose:
```bash
docker-compose up -d
```

### 4. Run the API Gateway
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
The API is now running at `http://localhost:8000`.

---

## 📖 API Documentation

### 1. Chat Completion (`POST /v1/chat`)

Routes an incoming user prompt to the optimal model based on complexity and returns token costs and savings.

**Request:**
```json
POST /v1/chat
Content-Type: application/json

{
  "prompt": "Write a Python function to find the longest palindromic substring using dynamic programming.",
  "system_prompt": "You are an expert computer science tutor."
}
```

**Response:**
```json
{
  "log_id": 42,
  "response": "Here is the implementation of the longest palindromic substring algorithm...",
  "complexity_label": "HIGH",
  "complexity_score": 8.2,
  "model_used": "anthropic/claude-3.5-sonnet",
  "provider": "anthropic",
  "prompt_tokens": 32,
  "completion_tokens": 140,
  "cost": 0.002196,
  "savings": 0.000000
}
```

*For a simple request (e.g. "Translate 'Hello' to French"):*
```json
{
  "log_id": 43,
  "response": "Bonjour",
  "complexity_label": "LOW",
  "complexity_score": 2.1,
  "model_used": "google/gemini-flash-1.5",
  "provider": "gemini",
  "prompt_tokens": 8,
  "completion_tokens": 2,
  "cost": 0.000001,
  "savings": 0.000053
}
```

---

### 2. Submit Feedback (`POST /v1/feedback`)

Allows end users to submit rating feedback for a query. Negative feedback is logged for model retraining.

```json
POST /v1/feedback
Content-Type: application/json

{
  "log_id": 42,
  "feedback": "positive"
}
```

---

### 3. Health Check (`GET /health`)

```json
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "router_initialized": true
}
```

---

## 🧪 Dataset Benchmarking & ML Training

You can benchmark candidate LLMs and train your own ML routing model using real-world datasets like **Databricks Dolly 15k**:

### Step 1: Download & Sample Dolly 15k Dataset
```bash
python DATASET_BUILDER/prepare_dolly_dataset.py --sample 10 --output data/dolly_prompts.csv
```

### Step 2: Run Multi-Model Benchmarking & LLM Quality Judge
Executes every prompt across candidate models, measures latency & cost, scores outputs using an LLM Quality Judge, and selects the optimal model per prompt:
```bash
python DATASET_BUILDER/benchmark_dataset_builder.py --prompts-file data/dolly_prompts.csv --output data/dolly_benchmark_dataset.csv
```

### Step 3: Train the Logistic Regression Router
Trains the complexity classifier model on your benchmark dataset embeddings and saves the trained model:
```bash
python DATASET_BUILDER/train_classifier.py --dataset data/dolly_benchmark_dataset.csv
```
This generates `router/classifier_model.joblib`, enabling your router to make instant ML predictions!

---

## 📊 Observability & Monitoring Dashboards

When running `docker-compose up -d`, the observability suite is accessible at:

| Service | Endpoint | Description |
|---|---|---|
| **FastAPI Gateway** | `http://localhost:8000` | Gateway Server & Interactive Swagger Docs (`/docs`) |
| **Prometheus UI** | `http://localhost:9090` | Metrics Collection & Query Engine |
| **Grafana Dashboards** | `http://localhost:3000` | Visual dashboards for cost savings, latency & cache hit ratios |
| **Jaeger Traces** | `http://localhost:16686` | End-to-end distributed transaction tracing |

---

## ⚙️ Model Registry Configuration (`models.yaml`)

Custom models, providers, and pricing rates can be easily updated in `models.yaml`:

```yaml
openai/gpt-4o-mini:
  provider: openai
  input_cost_per_m: 0.15
  output_cost_per_m: 0.60
  tier: cheap
  quality: 8.5

google/gemini-flash-1.5:
  provider: gemini
  input_cost_per_m: 0.075
  output_cost_per_m: 0.30
  tier: cheap
  quality: 8.3

anthropic/claude-3.5-sonnet:
  provider: anthropic
  input_cost_per_m: 3.00
  output_cost_per_m: 15.00
  tier: premium
  quality: 9.8

llama3:
  provider: ollama
  input_cost_per_m: 0.00
  output_cost_per_m: 0.00
  tier: local
  quality: 7.5
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to open an Issue or submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

<div align="center">
  <sub>Built with ❤️ by the LLM Autopilot Team</sub>
</div>
