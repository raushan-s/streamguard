# StreamGuard - Python Security Library for AI/LLM Applications

A comprehensive Python security library for AI/LLM applications with 4 detection layers. Detects PII, jailbreaks, prompt injections, harmful content, and optional stateful attacks.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Tests](https://img.shields.io/badge/tests-27%20%2F%2027-success.svg)](tests/)

## 🎯 Features

- **Layer 1 - PII Detection**: Identifies personally identifiable information (emails, SSNs, credit cards, etc.)
- **Layer 2a - Jailbreak Detection**: Detects instruction override attempts and DAN attacks
- **Layer 2b - Injection Detection**: Catches hidden prompt injections in data
- **Layer 3 - Content Moderation**: OpenAI-based harmful content detection
- **Layer 4 - Stateful Analysis**: *(Optional)* Multi-turn attack detection with pattern recognition (requires Upstash Redis)

## 📊 Performance

- **Latency**: ~6-7 seconds (cold start), ~5-6 seconds (warm)
- **Accuracy**: 100% on malicious input tests
- **Detection Rates**:
  - Jailbreak: 1.00 score on malicious inputs
  - PII: 2 entities found in test cases
  - Injection: 0.96 confidence score
  - Progressive extraction: 0.85 risk score (with Layer 4 enabled)

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- HuggingFace account and token
- OpenAI API key
- (Optional) Upstash Redis URL for stateful analysis (Layer 4)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd streamguard_lambda
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   python -m spacy download en_core_web_lg
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

6. **Download ML models (required):**
   ```bash
   python download_models.py
   ```
   **Note:** This downloads ~2.7GB of models. Models are excluded from git to keep repository size manageable.

### Basic Usage

```python
from streamguard import analyze_text

# Simple analysis
result = analyze_text("Your text here")
print(result["layer_results"]["jailbreak"])

# With optional parameters
result = analyze_text(
    text="User input",
    session_id="session-123",  # Enables Layer 4 (stateful analysis)
    agent_id="my-agent",
    direction="input"
)
```

### Running Tests

```bash
# Unit tests
pytest tests/test_handler.py -v

# Integration tests
python tests/test_integration.py

# Malicious input tests
python test_malicious.py
```

### Local Testing

```bash
python local_test.py
```

## ⚙️ Configuration

Create a `.env` file (copy from `.env.example`):

```bash
# HuggingFace (required for Layers 2a, 2b)
HF_TOKEN=hf_your_token_here

# OpenAI (required for Layers 3, 4)
OPENAI_API_KEY=sk-your-key-here

# Optional: Layer 4 (Stateful Analysis)
# Requires: pip install upstash-redis
# Uncomment the lines below and set ENABLE_LAYER4=true to enable
# UPSTASH_REDIS_URL=https://your-redis.upstash.io
# UPSTASH_REDIS_TOKEN=your_token_here

# Thresholds
PROMPT_GUARD_THRESHOLD=0.5
DEBERTA_THRESHOLD=0.85
STATEFUL_RISK_THRESHOLD=0.7

# Feature flags
ENABLE_LAYER4=false  # Disabled by default (requires Upstash Redis)
```

## 📦 Project Structure

```
streamguard_lambda/
├── streamguard.py          # Main library entry point
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── download_models.py     # Model downloader script
├── layers/                # Detection layers
│   ├── layer1_pii.py      # PII detection
│   ├── layer2a_prompt_guard.py  # Jailbreak detection
│   ├── layer2b_deberta.py      # Injection detection
│   ├── layer3_moderation.py    # Content moderation
│   └── layer4_stateful.py      # Stateful analysis (optional)
├── tests/                 # Test suite
└── models/                # ML models (2.7GB, created by download_models.py)
```

## 🔧 API Usage

### Input Format

```python
from streamguard import analyze_text

# Basic usage
result = analyze_text("Your text here")

# With all parameters
result = analyze_text(
    text="User input to analyze",
    session_id="optional-session-id",  # Enables Layer 4
    agent_id="agent-identifier",       # Default: "default"
    direction="input"                  # "input" or "output"
)
```

### Output Format

```json
{
  "layer_results": {
    "pii": {
      "detected": true,
      "entities": [...]
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
      "categories": {...}
    },
    "stateful": {
      "analyzed": true,
      "risk_score": 0.1
    }
  },
  "latency_ms": 6500
}
```

## 🧪 Test Results

All tests passing (27/27):
- ✅ 13 unit tests
- ✅ 2 integration tests
- ✅ 4 malicious input tests
- ✅ Local smoke test

See [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md) for detailed results.

## 📖 Documentation

- [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide
- [USAGE.md](USAGE.md) - Comprehensive usage examples
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [USER_JOURNEY.md](USER_JOURNEY.md) - User journey documentation

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

For issues and questions:
- Open a GitHub issue
- Check existing documentation
- Review test files for usage examples

## 🙏 Acknowledgments

- Meta AI for Llama Prompt Guard 2
- ProtectAI for DeBERTa injection detection model
- Microsoft Presidio for PII detection
- OpenAI for content moderation API

---

**Made with ❤️ for secure AI applications**
