# StreamGuard - Python Security Library for AI/LLM Applications

A comprehensive Python security library for AI/LLM applications with 4 detection layers. Detects PII, jailbreaks, prompt injections, harmful content, and optional stateful attacks.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- **Layer 1 - PII Detection**: Identifies personally identifiable information (emails, SSNs, credit cards, etc.)
- **Layer 2a - Jailbreak Detection**: Detects instruction override attempts and DAN attacks
- **Layer 2b - Injection Detection**: Catches hidden prompt injections in data
- **Layer 3 - Content Moderation**: OpenAI-based harmful content detection
- **Layer 4 - Stateful Analysis**: *(Optional)* Multi-turn attack detection with pattern recognition

## Quick Start

### Prerequisites

- Python 3.12+
- HuggingFace account and token
- OpenAI API key
- (Optional) Upstash Redis URL for stateful analysis (Layer 4)

### Installation

```bash
# Clone the repository
git clone https://github.com/raushan-s/streamguard.git
cd streamguard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### First Run

Models download automatically on first run (~350MB, one-time):

```python
from streamguard import analyze_text

result = analyze_text("Your text here")
# Models download automatically if not cached
```

**What to expect:**
```
INFO: Local model not found, downloading from HuggingFace...
Downloading: 100%|██████████| 202/202 [00:00<00:00, 1809.02it/s]
INFO: Model loaded successfully
```

- **First run**: Downloads ~350MB (Prompt Guard 2 + DeBERTa)
- **Subsequent runs**: Loads instantly from cache
- **Cache location**: `~/.cache/huggingface/hub/`

## Configuration

Create a `.env` file (copy from `.env.example`):

```bash
# Required for Layers 2a, 2b
HF_TOKEN=hf_your_token_here

# Required for Layers 3, 4
OPENAI_API_KEY=sk-your-key-here

# Optional: Layer 4 (Stateful Analysis)
# UPSTASH_REDIS_URL=https://your-redis.upstash.io
# UPSTASH_REDIS_TOKEN=your_token_here
# ENABLE_LAYER4=true

# Thresholds (optional)
PROMPT_GUARD_THRESHOLD=0.5
DEBERTA_THRESHOLD=0.85
STATEFUL_RISK_THRESHOLD=0.7
```

## Basic Usage

### Simple Example

```python
from streamguard import analyze_text

result = analyze_text("My email is john@example.com")

# Check results
if result['layer_results']['pii']['detected']:
    print("PII found!")
    for entity in result['layer_results']['pii']['entities']:
        print(f"  {entity['entity_type']}: {entity['text']}")
```

### With All Parameters

```python
result = analyze_text(
    text="User input to analyze",
    session_id="user-session-123",  # Enables Layer 4 (stateful analysis)
    agent_id="my-agent",
    direction="input"  # or "output"
)
```

### Checking Each Layer

```python
layer_results = result['layer_results']

# Layer 1: PII Detection
if layer_results['pii']['detected']:
    print(f"PII: {len(layer_results['pii']['entities'])} entities")

# Layer 2a: Jailbreak Detection
if layer_results['jailbreak']['label'] == 'MALICIOUS':
    print("Jailbreak detected!")

# Layer 2b: Injection Detection
if layer_results['injection']['label'] == 'INJECTION':
    print("Injection detected!")

# Layer 3: Content Moderation
if layer_results['moderation']['flagged']:
    print("Content flagged!")

# Layer 4: Stateful Analysis (if enabled)
if layer_results.get('stateful', {}).get('analyzed'):
    risk_score = layer_results['stateful']['risk_score']
    if risk_score > 0.7:
        print("Multi-turn attack detected!")
```

## Output Format

```json
{
  "layer_results": {
    "pii": {
      "detected": true,
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "text": "john@example.com",
          "score": 1.0,
          "start": 10,
          "end": 26
        }
      ],
      "sanitized": "My email is <EMAIL_ADDRESS>"
    },
    "jailbreak": {
      "prompt_guard_score": 0.99,
      "label": "MALICIOUS"
    },
    "injection": {
      "deberta_score": 0.96,
      "label": "INJECTION"
    },
    "moderation": {
      "flagged": false,
      "categories": {
        "harassment": 0.001,
        "violence": 0.0005
      }
    },
    "stateful": {
      "analyzed": true,
      "risk_score": 0.85,
      "patterns_detected": ["PROGRESSIVE_EXTRACTION"],
      "explanation": "Multi-turn attack detected"
    }
  },
  "latency_ms": 1234.56
}
```

## Running Examples & Tests

```bash
# Quick example - see StreamGuard in action
python example_usage.py

# Run all tests
python tests/run_all_tests.py

# Run specific test suites
python tests/test_end_to_end.py    # Full end-to-end tests
python tests/test_malicious.py     # Malicious input tests

# Run pytest unit tests
pytest tests/ -v
```

## Project Structure

```
streamguard/
├── streamguard.py          # Main library entry point
├── config.py               # Configuration management
├── example_usage.py        # Quick start examples
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── download_models.py     # Optional: Manual model download
├── layers/                # Detection layers
│   ├── layer1_pii.py      # PII detection
│   ├── layer2a_prompt_guard.py  # Jailbreak detection
│   ├── layer2b_deberta.py      # Injection detection
│   ├── layer3_moderation.py    # Content moderation
│   └── layer4_stateful.py      # Stateful analysis (optional)
├── examples/              # Usage examples
│   └── quick_demo.py      # Quick demonstration script
└── tests/                 # Test suite
    ├── test_end_to_end.py # Full end-to-end tests
    ├── test_malicious.py  # Malicious input tests
    ├── test_integration.py # Integration tests
    └── test_handler.py    # Handler tests
```

## Model Download Options

### Automatic Download (Recommended for Local Development)

Models download automatically from HuggingFace on first run:
- **Size**: ~350MB (one-time download)
- **Speed**: 1-2 minutes depending on internet
- **Cache**: Stored in `~/.cache/huggingface/hub/`
- **Requirements**: Internet connection + `HF_TOKEN` in `.env`

### Manual Download (Optional - For Lambda/Docker)

For serverless/offline deployments:

```bash
python download_models.py
# Downloads to ./models/ directory (~2.7GB)
```

**Use manual download when:**
- Deploying to AWS Lambda (no internet)
- Building Docker images
- Offline environments
- Reproducible deployments

## Troubleshooting

### Issue: "Cannot find model" error
**Solution:**
1. Ensure `HF_TOKEN` is set in `.env`
2. Check internet connection
3. Accept model license at https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M

### Issue: "HuggingFace access denied"
**Solution:**
1. Visit https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
2. Accept the model license
3. Generate token at https://huggingface.co/settings/tokens
4. Add to `.env`: `HF_TOKEN=hf_your_token_here`

### Issue: Slow first run
**Solution:** Models download once (~350MB). Subsequent runs use cached models and are fast.

### Issue: spaCy model error
**Solution:**
```bash
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Meta AI for Llama Prompt Guard 2
- ProtectAI for DeBERTa injection detection model
- Microsoft Presidio for PII detection
- OpenAI for content moderation API

---

**Made with secure AI applications in mind**
