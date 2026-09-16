from huggingface_hub import HfApi
from semantic_afterlife.config import get_settings

settings = get_settings()
api = HfApi(token=settings.hf_token)
for repo in ("google/gemma-4-12B", "google/gemma-4-12B-it", "mistralai/Ministral-3-8B-Base-2512"):
    info = api.model_info(repo)
    print(repo, "gated", info.gated, "sha", info.sha[:12] if info.sha else None)
