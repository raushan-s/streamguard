# StreamGuard Installation Guide

Complete step-by-step installation guide for StreamGuard security library.

## System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Python**: 3.12 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 5GB free space (for models and dependencies)
- **Internet**: Required for downloading models and dependencies

## Step 1: Install Python 3.12

### Windows
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer and check "Add Python to PATH"
3. Verify: `python --version`

### macOS
```bash
brew install python@3.12
```

### Linux
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

## Step 2: Clone Repository

```bash
git clone <your-repo-url>
cd streamguard_layers/streamguard_lambda
```

## Step 3: Create Virtual Environment

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** This will take 5-10 minutes and install ~2GB of packages.

## Step 5: Install spaCy Models

```bash
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg
```

## Step 6: Configure Environment

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:

### Get HuggingFace Token (Required)
1. Go to [huggingface.co](https://huggingface.co/)
2. Sign up for an account
3. Go to Settings → Access Tokens
4. Create new token
5. Add to `.env`:
   ```
   HF_TOKEN=hf_your_token_here
   ```

### Get OpenAI API Key (Required)
1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up and go to API Keys
3. Create new secret key
4. Add to `.env`:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

### Get Upstash Redis (Optional - for Layer 4 only)
1. Go to [upstash.com](https://upstash.com/)
2. Create free Redis database
3. Copy REST API URL and token
4. Install upstash-redis: `pip install upstash-redis`
5. Add to `.env`:
   ```
   UPSTASH_REDIS_URL=https://your-redis.upstash.io
   UPSTASH_REDIS_TOKEN=your_token_here
   ENABLE_LAYER4=true
   ```

## Step 7: Download ML Models (Required)

**Important:** Models are excluded from git to keep the repository size manageable. You must download them before running the project.

```bash
python download_models.py
```

This downloads ~2.7GB of models to the `models/` directory:
- Prompt Guard 2 (jailbreak detection)
- DeBERTa v3 (injection detection)

**Note:** You need a HuggingFace token set in your `.env` file before running this script.

## Step 8: Verify Installation

Run the test suite:

```bash
# Quick smoke test
python local_test.py

# Full test suite
pytest tests/test_handler.py -v
```

Expected output: All tests pass ✓

## Troubleshooting

### Issue: "Module not found"
**Solution**: Make sure virtual environment is activated
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Issue: "CUDA out of memory"
**Solution**: The project uses CPU-only PyTorch. If you have GPU PyTorch installed:
```bash
pip uninstall torch torchvision torchaudio
pip install -r requirements.txt
```

### Issue: "HuggingFace authentication error"
**Solution**:
1. Verify HF_TOKEN is set correctly in `.env`
2. Accept Llama model license at [huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M)

### Issue: "spaCy model not found"
**Solution**:
```bash
python -m spacy validate
python -m spacy download en_core_web_sm --force
```

### Issue: "Presidio recognizer errors"
**Solution**: Make sure both spaCy models are installed:
```bash
python -m spacy download en_core_web_sm en_core_web_lg
```

## Next Steps

- Read [README.md](README.md) for usage guide
- Check [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md) for performance metrics
- See test files for usage examples

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Review error messages carefully
3. Open a GitHub issue with:
   - Your operating system and Python version
   - Complete error message
   - Steps to reproduce
