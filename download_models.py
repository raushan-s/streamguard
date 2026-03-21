"""
Download ML models from HuggingFace and save them locally for Lambda deployment.

This script downloads:
1. Prompt Guard 2 (meta-llama/Llama-Prompt-Guard-2-86M) - PyTorch
2. DeBERTa ONNX (protectai/deberta-v3-small-prompt-injection-v2) - ONNX format

Models are saved to: streamguard_lambda/models/
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def download_prompt_guard():
    """Download Prompt Guard 2 model."""
    print("\n" + "="*60)
    print("Downloading Prompt Guard 2...")
    print("="*60)

    # Login to HuggingFace first
    from huggingface_hub import login
    import os

    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable not set. Please set it in .env file.")

    print(f"Logging in to HuggingFace...")
    login(token=hf_token)

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_name = "meta-llama/Llama-Prompt-Guard-2-86M"
    output_dir = Path(__file__).parent.parent / "models" / "prompt-guard-2"

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Saving to: {output_dir}")

    # Download model and tokenizer
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        cache_dir=str(output_dir)
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir=str(output_dir)
    )

    # Save in standard HuggingFace format
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    print(f"[OK] Prompt Guard 2 downloaded to {output_dir}")
    return output_dir


def download_deberta_onnx():
    """Download DeBERTa ONNX model."""
    print("\n" + "="*60)
    print("Downloading DeBERTa ONNX...")
    print("="*60)

    try:
        from optimum.onnxruntime import ORTModelForSequenceClassification
        from transformers import AutoTokenizer

        model_name = "protectai/deberta-v3-small-prompt-injection-v2"
        output_dir = Path(__file__).parent.parent / "models" / "deberta-v3-small-injection-onnx"

        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Saving to: {output_dir}")

        # Download ONNX model
        model = ORTModelForSequenceClassification.from_pretrained(
            model_name,
            export=True,  # Export to ONNX if not already
            cache_dir=str(output_dir / "onnx")
        )

        # Download tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=str(output_dir)
        )

        # Save model
        model.save_pretrained(str(output_dir / "onnx"))
        tokenizer.save_pretrained(str(output_dir))

        print(f"[OK] DeBERTa ONNX downloaded to {output_dir}")
        return output_dir

    except ImportError as e:
        print(f"[ERROR] ONNX dependencies not available: {e}")
        print("Installing optimum...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "optimum[onnxruntime]"])
        # Retry
        return download_deberta_onnx()


def main():
    """Download all models."""
    print("\n" + "="*60)
    print("StreamGuard Model Downloader")
    print("="*60)

    # Create base models directory
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Download Prompt Guard 2
        pg_dir = download_prompt_guard()

        # Download DeBERTa ONNX
        deberta_dir = download_deberta_onnx()

        print("\n" + "="*60)
        print("Download Complete!")
        print("="*60)
        print(f"Models saved to: {models_dir}")
        print(f"  - Prompt Guard 2: {pg_dir}")
        print(f"  - DeBERTa ONNX: {deberta_dir}")
        print(f"\nTotal size: ~{sum(f.stat().st_size for f in models_dir.rglob('*') if f.is_file()) / (1024**3):.2f} GB")

    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
