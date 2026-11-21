"""
Convert model.safetensors -> pytorch_model.bin for Qwen and SLM.
Uses safetensors.torch.load_file which does NOT mmap the whole file at once.
Run this ONCE to pre-convert, then api_server.py uses pytorch_model.bin.
"""
import os
import gc
import torch
from pathlib import Path
from safetensors.torch import load_file

MODELS = [
    Path("D:/HACKATHON/indicshield_models/qwen_0_5b/saved_model"),
    Path("D:/HACKATHON/indicshield_models/slm_abliterated/saved_model"),
]

for model_dir in MODELS:
    sf_path = model_dir / "model.safetensors"
    bin_path = model_dir / "pytorch_model.bin"
    if not sf_path.exists():
        print(f"[SKIP] {sf_path} not found")
        continue
    if bin_path.exists():
        print(f"[SKIP] {bin_path} already exists")
        continue
    print(f"Converting {sf_path} -> {bin_path}  (this uses ~{sf_path.stat().st_size/1024**3:.2f} GB RAM temporarily)")
    state_dict = load_file(str(sf_path))
    torch.save(state_dict, str(bin_path))
    del state_dict
    gc.collect()
    print(f"  Done: {bin_path.stat().st_size/1024**3:.2f} GB saved")

print("All conversions complete.")
