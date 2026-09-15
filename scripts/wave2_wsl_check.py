"""Wave 2 env probe. Prints versions and HF identity name only — never the token."""

from __future__ import annotations

import torch
import bitsandbytes
import transformers
from huggingface_hub import whoami

from semantic_afterlife.config import get_settings

print("torch", torch.__version__)
print("cuda", torch.cuda.is_available(), torch.version.cuda)
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
    print("vram_bytes", torch.cuda.get_device_properties(0).total_memory)
print("bnb", bitsandbytes.__version__)
print("tfm", transformers.__version__)
settings = get_settings()
print("hf_token_set", bool(settings.hf_token))
info = whoami(token=settings.hf_token)
name = info.get("name") if isinstance(info, dict) else getattr(info, "name", "?")
print("hf_name", name)
