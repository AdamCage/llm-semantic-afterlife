# Stage 8 / Paper B — Wave 0 census

Readonly fact-gather, 2026-09-09. No weight download (Hub `config.json` /
`tokenizer_config.json` / `*.index.json` only). No `afterlife generate`. No API
spend. No harness patches. No ADR. Plan file
`.cursor/plans/paper_b_local_matrix_5105e6af.plan.md` was not edited.

Freeze block F1–F4 is **not** reopened by this census.

| Field | Value |
| --- | --- |
| `status` | `ok` (actionable blockers below; census itself complete) |
| `run_ids` | none |
| `next_agent` | **ADR freeze** (0023–0026). `docs/decisions/` has ADR-0020…0022 only. |
| `do_not` | Download ~175 GB of BF16 shards onto `C:`; start S8 harness before ADR freeze; generate; spend RouterAI/OpenRouter; edit `refs.bib` / `paper/main.tex`; silently replace Gemma or swap Ministral to FP8. |

---

## W0-A HardwareCensus

Measured on host `DESKTOP-VII9120` (MSI MS-7D99), 2026-09-09T18:39Z.

### GPU / driver

| Item | Value |
| --- | --- |
| Name | **NVIDIA GeForce RTX 4080 SUPER** |
| VRAM | **16376 MiB** (~16.0 GiB). In-use at census ~1.4 GiB (desktop / Cursor / Chrome), free ~14.3 GiB |
| Driver | 610.88 (WDDM) |
| CUDA UMD (Windows `nvidia-smi`) | 13.3 |
| WSL `nvidia-smi` | Same card, **16376 MiB**, driver 610.88. `libcuda.so` present under `/usr/lib/wsl/lib/` |

User-stated “12 GB” is **false** for this machine. Official 4080 Super SKU is 16 GB; the meter agrees.

### OS / WSL

| Item | Value |
| --- | --- |
| Registry `ProductName` | Windows 10 Pro (stale string) |
| Actual build | **10.0.26200.9168**, DisplayVersion **25H2**, BuildLab `26100.1.amd64fre.ge_release.240331-1435` → Windows 11 25H2 |
| WSL distros | `Ubuntu` **Stopped**, version **2**; `docker-desktop` Stopped, version 2 |
| Default WSL distro | `docker-desktop` (not Ubuntu). Always invoke `wsl -d Ubuntu` or change default |
| WSL kernel | `6.18.33.2-microsoft-standard-WSL2` |
| WSL RAM seen by Ubuntu | **31 GiB** + 8 GiB swap (host has ~64 GiB; WSL is capped) |

### RAM / disk / HF cache

| Item | Value |
| --- | --- |
| Host RAM | 68 560 121 856 B (**63.8 GiB**); ~47.6 GiB free at census |
| Volumes | **Only `C:`** — NTFS 1862.1 GB, **141.5 GB free** |
| `HF_HOME` / `HUGGINGFACE_HUB_CACHE` / `TRANSFORMERS_CACHE` | unset in process env |
| Default Windows cache | `C:\Users\AdamCage\.cache\huggingface` — **87 GB** already used (other models: TTS, Whisper, SmolLM, …) |
| Paper B shards in that cache | **not present**. Census JSON-only footprints: 12–256 KB per repo |
| WSL `/` | 1007 GB, **529 GB free** |
| WSL `~/.cache/huggingface` | 3.0 GB (unrelated tiny repos) |
| Windows Python `torch` | `2.11.0+cpu`, `cuda=False` (not a Paper B runtime) |
| WSL `torch` | not installed |
| HF auth | `hf auth whoami` → **AdamCage**. `.env` has `HF_TOKEN` (value not recorded here) |

Plan threshold “≥250 GB free before download” is **failed on `C:`** and **passed on WSL Ubuntu `/`**.

### Verdict

```text
vram_budget: 16
os_lane: wsl2
```

- **16 GB VRAM** is the operating budget. INT8 Qwen at `W+B=5120` is in-scope after microbench; BF16 8B/12B as primary is still out (plan §3.1).
- **`os_lane: wsl2`** — Ubuntu 2 exists, GPU is visible inside WSL, and only the Linux filesystem has room for ~175 GB of official BF16 shards. Preferred stack remains WSL2 → PyTorch CUDA → Transformers → bitsandbytes NF4.
- **`windows_native` is not blocked for compute** (same 16 GB card) but **is blocked for the download**: 141.5 GB free < ~175 GB weights, and the Hub cache cannot use symlinks without Developer Mode (duplicate-file tax). Do not start `hf download` of the ten checkpoints onto `C:`.
- **Not `blocked`.** Start Ubuntu, point `HF_HOME` at a path on `/` (not `/mnt/c`), raise WSL memory in `.wslconfig` if 31 GiB becomes tight during Gemma load.

Human decisions before any download: (1) confirm WSL `HF_HOME` on the 529 GB volume; (2) optionally raise WSL RAM; (3) do not free-space-hack by deleting the 87 GB Windows cache unless the human wants that.

---

## W0-B ModelCardCensus

Hub `model_info` + `config.json` / tokenizer / safetensors index (or LFS pointer size). Revisions are **`main` SHAs on 2026-09-09**. Pin these in S8 YAML; do not treat them as frozen until ADR-0024.

`allenai/Olmo-3-7B` is **404**. Canonical base id is **`allenai/Olmo-3-1025-7B`**. The Olmo card itself still *labels* that repo “Olmo 3 7B” in prose.

Think line (`Olmo-3-7B-Think`, `Olmo-3-7B-Think-SFT`, …) exists and is **not** in the Paper B matrix. Instruct-DPO’s card tags `dataset:allenai/Dolci-Think-DPO-7B` — name collision only; the repo id is still the Instruct-DPO checkpoint.

### Ten Paper B checkpoints

| # | Hub id | exists | gated (API) | license tag | `main` SHA (12) | class / loader | `sliding_window` | Hub dtype | safetensors bytes | `transformers` in config | chat template | thinking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `Qwen/Qwen3-8B-Base` | yes | false | Apache-2.0 | `49e3418fbbbc` | `Qwen3ForCausalLM` / **causal** | `null` | bf16 | 16 383 567 872 | 4.51.0 | yes (in `tokenizer_config`) | no dedicated think mode |
| 2 | `Qwen/Qwen3-8B` | yes | false | Apache-2.0 | `b968826d9c46` | `Qwen3ForCausalLM` / **causal** | `null` | bf16 | 16 381 470 720 | 4.51.0 | yes | **default `enable_thinking=True`**; tokens `<think>`=`151667`, `</think>`=`151668` |
| 3 | `mistralai/Ministral-3-8B-Base-2512` | yes | false | Apache-2.0 | `d4883f9b36aa` | `Mistral3ForConditionalGeneration` / **conditional_generation** | text `null` | bf16 | 17 836 052 480 | 5.0.0.dev0 | no jinja in tokencfg; no `chat_template.jinja` | none |
| 4 | `mistralai/Ministral-3-8B-Instruct-2512-BF16` | yes | false | Apache-2.0 | `f6fae9795746` | same / **conditional_generation** | text `null` | **bf16** | **17 836 052 480** | 5.0.0.dev0 | `chat_template.jinja` present | none (not Reasoning-2512) |
| 5 | `allenai/Olmo-3-1025-7B` | yes | false | Apache-2.0 | `a81bae42db39` | `Olmo3ForCausalLM` / **causal** | **4096** (3×slide + 1×full) | bf16 | 14 596 022 272 | 4.57.0 | no | none |
| 6 | `allenai/Olmo-3-7B-Instruct-SFT` | yes | false | Apache-2.0 | `e1452fc572d5` | `Olmo3ForCausalLM` / **causal** | 4096, same pattern | bf16 | 14 596 022 272 | 4.57.1 | `chat_template.jinja` | none |
| 7 | `allenai/Olmo-3-7B-Instruct-DPO` | yes | false | Apache-2.0 | `b33130b7de49` | `Olmo3ForCausalLM` / **causal** | 4096 | bf16 | 14 596 022 272 | 4.57.1 | `chat_template.jinja` | none (park Think) |
| 8 | `allenai/Olmo-3-7B-Instruct` | yes | false | Apache-2.0 | `6e5971d9eba4` | `Olmo3ForCausalLM` / **causal** | 4096 | bf16 | 14 596 022 272 | 4.57.1 | `chat_template.jinja` | RLVR / Dolci-Instruct-RL; not Think |
| 9 | `google/gemma-4-12B` | yes | **false** | `apache-2.0` + [Gemma 4 license page](https://ai.google.dev/gemma/docs/gemma_4_license) | `023679ed352d` | `Gemma4UnifiedForConditionalGeneration` / **conditional_generation** | **1024**, 5×slide + 1×full, last layer global | bf16 | **23 919 549 408** (single `model.safetensors`) | **5.10.0.dev0** | no | card: family has configurable thinking |
| 10 | `google/gemma-4-12B-it` | yes | **false** | same | `707f0a3b8a3c` | same / **conditional_generation** | 1024, same pattern | bf16 | **23 919 549 408** | **5.10.0.dev0** | `chat_template.jinja` | thinking modes; IT eos includes extra ids |

`google/gemma-4-12b` / `…-12b-it` resolve to the same SHAs (case alias).

### Confirmed exclusions / lookalikes

| Id | Role |
| --- | --- |
| `mistralai/Ministral-3-8B-Instruct-2512` (no `-BF16`) | **FP8**. Hub tag `fp8`, `base_model:quantized`, 3 shards, index `total_size` **10 420 523 960**. Card of the BF16 repo calls this the “no-loss FP8 version”. **Do not load.** |
| `allenai/Olmo-3-7B` | **Does not exist** (404). |
| `allenai/Olmo-3-7B-Think*` | Parked Think ladder. Distinct SHAs (`Think` `d97e442d7cc6`, `Think-SFT` `6ff857587e04`). |
| Ministral Reasoning-2512 | Not fetched; plan forbids it. |

### Architecture notes the harness must not ignore

- **Qwen3-8B Instruct thinking.** README: `enable_thinking=True` is the default. Chat template, when `enable_thinking is false`, inserts an empty `<think>\n\n</think>\n\n` prefix. Under Paper B `raw_bytes`, `apply_chat_template` is not used — thinking tokens can still appear in free completion. Per-step guard on `151667`/`151668` (and empty visible text) is mandatory. Base has no think switch.
- **Ministral 3 = 8.4B text + 0.4B Pixtral vision**, `Mistral3ForConditionalGeneration`. Text `sliding_window` is **null** (full attn). Vocab **131072** (card “256k context”, not 262k vocab). `library_name: vllm` on the card; `transformers` still ships `config.json` with `5.0.0.dev0`. Extra gated *description* (privacy policy) is present; API `gated=false`.
- **OLMo 3 Instruct ladder** (card table): Base `Olmo-3-1025-7B` → SFT → DPO → `Olmo-3-7B-Instruct` (RLVR). Hybrid attention: `sliding_window=4096`, pattern 3 sliding + 1 full. At protocol `W=4096` this is **not** an architecture contrast (plan §2.1). Vocab 100278. Causal loader.
- **Gemma 4 12B Unified** is encoder-free multimodal (text / image / audio projected into the decoder). 48 layers, hidden 3840, vocab **262144**, `sliding_window=1024`, 5+1 hybrid, 11.95B params. `pipeline_tag: any-to-any`. Loader risk is **higher** than the Gemma-4-E2B warning already in `local.py`. Card claims **configurable thinking modes** for the whole family — S8 thinking guard is not Qwen-only. Hub `gated=false` and license *tag* Apache-2.0, but `license_link` is still Google’s Gemma 4 license URL. Human should open that page before smoke.

### Disk math (weights only, official BF16)

| Family | GB |
| --- | --- |
| Qwen ×2 | 32.77 |
| Ministral BF16 ×2 | 35.67 |
| OLMo Instruct line ×4 | 58.38 |
| Gemma 12B ×2 | 47.84 |
| **Ten checkpoints** | **≈174.7 GB** |

Plus tokenizers (Gemma `tokenizer.json` ≈32 MB each), runs, embed cache. Plan’s 150–200 GB band is right. **Windows 141.5 GB free cannot hold this set.** WSL 529 GB can.

### Draft `generators_local_paperb.yaml` (not written to `configs/`)

```yaml
# DRAFT ONLY — census 2026-09-09. Pin revision after ADR-0024.
# One generator per generate run. extra_body quant keys must be in _LOAD_KEYS
# before first smoke. serialization is not a GeneratorConfig field yet.

# Qwen causal anchor
- slug: local-qwen3-8b-base
  model_id: Qwen/Qwen3-8B-Base
  api: local
  tokenizer_repo: Qwen/Qwen3-8B-Base
  tokenizer_revision: 49e3418fbbbca6ecbdf9608b4d22e5a407081db4
  continuation: raw_completion
  is_base_model: true
  extra_body:
    revision: 49e3418fbbbca6ecbdf9608b4d22e5a407081db4
    load_in_4bit: true
    bnb_4bit_quant_type: nf4
    bnb_4bit_use_double_quant: true
    bnb_4bit_compute_dtype: bfloat16
    device_map: cuda
    attn_implementation: sdpa
    enable_thinking: false   # inert on Base; record anyway
  loader_risk: causal

- slug: local-qwen3-8b-instruct
  model_id: Qwen/Qwen3-8B
  api: local
  tokenizer_repo: Qwen/Qwen3-8B
  tokenizer_revision: b968826d9c46dd6066d109eabc6255188de91218
  continuation: raw_completion
  is_base_model: false
  extra_body:
    revision: b968826d9c46dd6066d109eabc6255188de91218
    # same NF4 contract
    enable_thinking: false
  loader_risk: causal
  notes: "thinking default ON; raw_bytes bypasses template — step guard required"

# Ministral matched pair — BF16 only
- slug: local-ministral3-8b-base
  model_id: mistralai/Ministral-3-8B-Base-2512
  tokenizer_repo: mistralai/Ministral-3-8B-Base-2512
  tokenizer_revision: d4883f9b36aa2e5d775730d3fdba3d30de51a8ef
  continuation: raw_completion
  is_base_model: true
  extra_body: {revision: d4883f9b36aa2e5d775730d3fdba3d30de51a8ef}
  loader_risk: conditional_generation

- slug: local-ministral3-8b-instruct
  model_id: mistralai/Ministral-3-8B-Instruct-2512-BF16
  tokenizer_repo: mistralai/Ministral-3-8B-Instruct-2512-BF16
  tokenizer_revision: f6fae9795746f63c9be8344932f01275f3c63734
  continuation: raw_completion
  is_base_model: false
  extra_body: {revision: f6fae9795746f63c9be8344932f01275f3c63734}
  loader_risk: conditional_generation
  notes: "NOT mistralai/Ministral-3-8B-Instruct-2512 (FP8)"

# OLMo Instruct ladder — base id is 1025
- slug: local-olmo3-7b-base
  model_id: allenai/Olmo-3-1025-7B
  tokenizer_revision: a81bae42db3975be1671e27b9c9a56da1a9f980f
  continuation: raw_completion
  is_base_model: true
  loader_risk: causal
- slug: local-olmo3-7b-instruct-sft
  model_id: allenai/Olmo-3-7B-Instruct-SFT
  tokenizer_revision: e1452fc572d51966ff4aaeb25118b891eb93e549
  continuation: raw_completion
  loader_risk: causal
- slug: local-olmo3-7b-instruct-dpo
  model_id: allenai/Olmo-3-7B-Instruct-DPO
  tokenizer_revision: b33130b7de49f0c2553b5c2b3bc8409ff3e627d1
  continuation: raw_completion
  loader_risk: causal
- slug: local-olmo3-7b-instruct
  model_id: allenai/Olmo-3-7B-Instruct
  tokenizer_revision: 6e5971d9eba42665f5bd5a0fcf047f299ce1dccc
  continuation: raw_completion
  loader_risk: causal

# Gemma architectural generalization
- slug: local-gemma4-12b-base
  model_id: google/gemma-4-12B
  tokenizer_revision: 023679ed352de9bb66cc873c9009ce3482585c08
  continuation: raw_completion
  is_base_model: true
  extra_body: {revision: 023679ed352de9bb66cc873c9009ce3482585c08, attn_implementation: sdpa}
  loader_risk: conditional_generation
- slug: local-gemma4-12b-it
  model_id: google/gemma-4-12B-it
  tokenizer_revision: 707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7
  continuation: raw_completion
  extra_body: {revision: 707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7, attn_implementation: sdpa}
  loader_risk: conditional_generation
  notes: "OOM => stop; no E4B substitute. transformers 5.10-class required."
```

INT8 twins (Qwen only) reuse the same two ids with `load_in_8bit: true` instead of NF4.

---

## W0-C HarnessGap

Checklist against plan §4. Proposed patches are **not applied**.

| # | Gap | File:line | Evidence | Proposed S8 patch (do not apply here) |
| --- | --- | --- | --- | --- |
| 1 | No bitsandbytes / NF4 / INT8 | `pyproject.toml:80-84` (`local` extra = torch, transformers, accelerate only); `local.py:37-48` `_LOAD_KEYS`; `local.py:346-361` load kwargs | Extra has no `bitsandbytes`. Loader only `device`/`dtype`/`attn_implementation` | Add `bitsandbytes` to extra `local`. Put `load_in_4bit`, `load_in_8bit`, all `bnb_*`, `quantization_config`, `device_map`, `revision` in `_LOAD_KEYS`. Build `BitsAndBytesConfig` in `_load`. Keep CI torch-free |
| 2 | Quant keys leak into `generate()` | `local.py:414-417` | `extra_gen = {k: v for k, v in extra.items() if k not in _LOAD_KEYS}` then `kwargs.update(extra_gen)` | Expand `_LOAD_KEYS` **before** first smoke. Unit test: fake backend sees no `bnb_*` in generate kwargs |
| 3 | No real unload | `local.py:99` `_resolved`; `local.py:282-283` `aclose` only `clear()`; `local.py:297-298` `_model` never deleted | Clearing the dict drops Python refs; no `del`, no `torch.cuda.empty_cache()`, no peak-VRAM events | `unload(model_id)` + `aclose_model`; `empty_cache`; events `local.model.loaded` / `unloaded`; assert one CUDA model in `_resolved` |
| 4 | Process-wide client registry | `registry.py:20` `_CLIENTS`; `registry.py:23-64` `build_client`; `registry.py:67-70` `close_clients` | `aclose` without registry drop leaves a live `LocalClient` holding `_resolved` | `close_clients` must unload CUDA then pop registry. Pin cache key on revision+quant |
| 5 | Multimodal / wrong auto class | `local.py:302,328-337,361` always `AutoModelForCausalLM`; Gemma4 special-case is a warning only | Ministral + Gemma 4 12B are `*ForConditionalGeneration`. Causal auto may fail or pull unused vision | Text-only generate path; same tokenizer as `Tail_W`; vision not invoked. Smoke before matrix |
| 6 | Qwen (and Gemma) thinking | `local.py` has no think-token check; `config.py:201-207` `max_reasoning_tokens` default 0 is hosted-reasoning, not `<think>` | Instruct thinking defaults **on**; raw_bytes skips template | Serialization field + per-step fail if think tokens > 0 or visible text empty. Gemma IT thinking modes too |
| 7 | Serialization not a config field | `config.py:150-223` `GeneratorConfig` has `continuation` but no `serialization` | `_messages_to_text` (`local.py:471-478`) already concatenates raw contents — good for Base, accidental for native chat | Add `serialization: raw_bytes \| native_chat`. Primary = identical encode(seed) for Base and Instruct |
| 8 | `max_concurrent` default 4 | `config.py:79` `afterlife_max_concurrent_trajectories: int = 4`; `trajectory.py:685-686` | Two concurrent local `generate` on 12–16 GB will OOM Gemma | Paper B YAML `max_concurrent: 1`. LocalClient: second concurrent CUDA generate raises |
| 9 | Local embed raises | `local.py:256-261`; `tests/test_local_client.py:176-182` **asserts** the raise | BGE-M3 / Qwen-embed would go RouterAI (money + different backend) | `LocalClient.embed` or `local_embed.py`; content-addressed `sha256(model_id ‖ text)` |
| 10 | P2 is inert but writable | `config.py:250` accepts `P2_sliding_attention`; `generation/trajectory.py` and `generation/window.py` never read `window.protocol` | Every trajectory is P1. YAML `protocol: P2_*` would lie in the manifest | Do not set P2 in Paper B YAML. Park ADR-0017. Optional: reject P2 at validate |
| 11 | Factorial vs GPU unload — **plan §4.14 overstated** | `trajectory.py:644-661` | **Generators are the outermost loop** — planned list is contiguous by model, not interleaved. Hazard is: (a) `asyncio.gather` + default concurrency 4; (b) no unload after a generator group; (c) `_resolved` keeps every `model_id` forever | Prefer **one checkpoint = one generate run**. If multi-generator YAML remains, barrier-unload between groups. Test: two fake ids never resident together |
| 12 | Prompt-keyed response cache | `local.py:128-152` payload includes full `prompt`; `cache.py:7-9,23-24` `sha256(provider ‖ path ‖ payload)` | L2 ≈ thousands of unique W-windows → tens of GB | `cache: steps_only` for ultra-long; JSONL already enough to resume (`trajectory.py` module docstring) |
| 13 | No `target_tokens` ceiling | `config.py:253-260` only `T ≥ W`; `cli.py:211-220` `estimate` prints P1 cost, no 5M wall-clock/disk warning | A 5M YAML is legal and silent | Soft warning in `afterlife estimate` (disk + ETA). Do not silently cap |
| 14 | P1 notation `S = B` | `config.py:266-269` `stride` property still documents `S = B (ADR-0001)` | README/methodology may still say exact stride; `block_size` is already max-B | v1 leftover; Paper B comments must say `B_max` |
| 15 | Tokenizer identity / 262k vocab | ADR-0011 path exists; Gemma vocab 262144, Ministral 131072 | Seed-bank encode/decode not re-measured this census | S8 smoke: 10/10 seed-bank roundtrip `add_special_tokens=False` |
| 16 | `transformers` pin too old for Gemma/Ministral | `pyproject.toml:82` `transformers>=4.51` | Qwen 4.51, OLMo 4.57, Ministral **5.0.dev0**, Gemma **5.10.dev0** | S8 must raise the `local` extra (and document the pin). Not a Wave 0 code change |
| 17 | Vector provenance (ADR-0021) | embed path not local | Rule: verify fails without `data/embeddings_*.parquet` + per-traj vectors | Wave 1-B4 / doctor check |

`WindowConfig.protocol` is the only P2 switch. Grep of `src/semantic_afterlife/generation/` finds **zero** reads of `.protocol`.

---

## W0-D LiteratureDelta (draft only — `refs.bib` not edited)

### Resolution of the DOI

ADR-0020 (2026-09-07) and `docs/literature/related-work.md` §8 recorded
“Execution Horizon Laws / 31-model census” as **not found** under that title.
The DOI in the Paper B plan **resolves**.

| Field | Value |
| --- | --- |
| DOI | [10.21203/rs.3.rs-10101463/v1](https://doi.org/10.21203/rs.3.rs-10101463/v1) |
| Landing | https://www.researchsquare.com/article/rs-10101463/v1 (HTTP 200) |
| Title | *Execution Horizon Laws: A 31-Model Census of Self-Conditioning, a Half-Retention Regularity, and the Limits of First-Step Accuracy in Long-Horizon LLM Execution* |
| Authors | Tianqi Bu (Rutgers); Yuxuan Peng (Nanjing University of Posts and Telecommunications) |
| Posted | 2026-06-23 (accepted 2026-06-20). Crossref type `posted-content` / Research Square *In Review* |
| License | CC BY 4.0 |
| PDF | 569 478 bytes fetched for this census; text layer was not extracted (`pdftotext` / pypdf absent). Abstract below is the **Crossref** abstract (2026-09-09) |

Crossref was indexed 2026-09-02. The 2026-09-07 “not found” search predated easy discovery under the short title. **Lookalike, not this paper:** Sinha, Arun, Goel, Staab, Geiping, *The Illusion of Diminishing Returns: Measuring Long Horizon Execution in LLMs* (arXiv:2509.09677). EHL is a compute-leveraged **re-measurement** of that execution-horizon relation on 31 open-weight models. Do not cite 2509.09677 *as* Execution Horizon Laws.

### What EHL measures (from the Crossref abstract)

Object: **task-execution survival**. A deterministically graded synthetic long-horizon execution task (plan and knowledge supplied; success is a correct state update). Horizon = how many sequential steps a model chains before cumulative success falls below a threshold. The parameter-free map from single-step accuracy to horizon is taken as already established; the paper asks *which* single-step accuracy to feed it.

Census: **31 open-weight models**, 0.5B–72B, six families, base / instruct / reasoning. Headline relations sit on **11–25-model subsets**, not all 31.

Four findings they claim:

1. **Which accuracy** matters more than the law: *self-conditioned asymptotic* accuracy predicts measured-horizon rank at Spearman 0.91; *first-step* accuracy saturates among the strongest models (0.55) — a saturation effect, not universal (cross-task replication).
2. **Self-conditioning** (feeding a model its own prior errors) lowers next-step accuracy monotonically in capability (rank 0.95). Strongest models are hit hardest (~half); floor models lose nothing. They name a **half-retention** regularity (retention near 0.50). Post-error accuracy is the best horizon predictor (Pearson 0.93 vs 0.66 for first-step). A “corrected survival law” fits 3–4× better.
3. Test-time reasoning buys horizon back but is **capability-gated**.
4. Self-conditioning order **replicates** on a content-disjoint task (0.90).

They release per-cell records, scripts, and figures.

### Shared word, different object

Both papers use **self-conditioning**. In EHL (and Sinha et al.) it means: *errors already in the retained task transcript raise the probability of the next execution error*. The prompt, the plan, and a graded objective stay in context. Horizon is **task survival**.

In this project it means: *the generator’s only input is the last `W` tokens of its own continuation* (`X_{t+1} = Tail_W(X_t ⊕ Y_t)`), after the seed has been **physically evicted**. There is no key-value dictionary, no running sum, no success bit. The late object is a **seed-conditioned representation gap** \(G_t\) and a **repetition-lock** state machine — not “did the sum stay correct.”

A sliding window in EHL is a *mitigation* that drops old errors so the agent can keep executing. Our sliding window is the **state**. Eviction is the treatment, not a bugfix.

### One-page novelty delta (for PLAN.md / related-work; not a citation until ADR freeze)

**Neighbour, not predecessor.** EHL is the closest 2026 neighbour that (i) names self-conditioning, (ii) runs a multi-family open-weight census, and (iii) talks about horizons in the \(10^1\)–\(10^3\) step band. It does **not** occupy Paper B’s sentence.

Paper B is not a 31-model execution-survival replica. It is a **four-family, ten-checkpoint** local study of *what determines the late dynamical regime of a self-conditioned LM after complete prompt eviction*, with confirmatory estimands \(G_t\), \(\tau_{\mathrm{lock}}\), fingerprint agreement (L0) and \(\tau_{\mathrm{escape}}\) (L2 only).

| Axis | Execution Horizon Laws | Paper B (this repo) |
| --- | --- | --- |
| State | Task transcript + supplied plan/knowledge | Finite tail of free-form tokens, `W=4096` |
| Prompt after \(t \gg 0\) | Retained | **Gone** (horizon / eviction) |
| Success | Deterministic grade (e.g. running sum) | No task grade. \(G_t\), lock, fingerprints |
| Self-conditioning | Error→error on a graded task | Autoregressive continuation after eviction |
| Thinking / CoT | A treatment that can restore horizon | A **confound**; thinking parked / guarded |
| Scale | 31 models, hosted/open mix | 10 local official-BF16→NF4 checkpoints |
| Claim type | Survival law + half-retention | Determinants of late regime (post-training, architecture as generalization) |

**What Paper B must not write after reading EHL**

- That EHL “already measured semantic afterlife” or scooped \(G_t\).
- That their half-retention number calibrates our degeneracy thresholds (different construct; F1 is frozen).
- That a 31-model *task* census licenses a universal claim about free-form post-eviction dynamics.
- That thinking “fixes” our protocol — in Paper B, thinking breaks `Tail_W` accounting.

**What Paper B should write (after ADR + `refs.bib`)**

- One related-work paragraph: EHL / Sinha et al. study **how long a model can execute a supplied plan** as errors accumulate in a retained context. We study **what the trajectory does after the seed has left the window**, with no plan and no grader. Same informal phrase, disjoint estimands.
- Limitations: we are not an execution-horizon paper; we do not estimate \(H_s(p)\).

Wave 0 does **not** add this to `paper/refs.bib` (anonymous v1 freeze + ADR-0020 still say “do not cite a lookalike”; the DOI is now VERIFIED as the missing title, but bib edits belong to the ADR-freeze / literature agent).

---

## Blockers (human)

1. **Disk / download path.** ~174.7 GB official BF16 is not on disk. `C:` has 141.5 GB free. Download only with `HF_HOME` on WSL `/` (529 GB free). Do not download onto `C:`.
2. **VRAM** is 16 GB, not 12. Gemma 12B NF4 remains the tight cell; OOM ⇒ stop, no E4B swap.
3. **Licenses.** All ten API-`gated=false` and Apache-2.0-tagged. Still: open the [Gemma 4 license page](https://ai.google.dev/gemma/docs/gemma_4_license) (card `license_link`); Ministral cards carry `extra_gated_description` (privacy). `HF_TOKEN` is present for user `AdamCage`.
4. **WSL default distro** is `docker-desktop`. Use `wsl -d Ubuntu`. WSL RAM is 31 GiB.
5. **ADRs 0023–0026 are not written.** Census must not be treated as a freeze. Next agent writes those ADRs (including: Olmo base id `Olmo-3-1025-7B`; Ministral Instruct **BF16**; Gemma loader = conditional_generation; EHL DOI now found; F1–F4 copied verbatim).
6. **`transformers` pin.** Gemma 4 config declares **5.10.0.dev0**; Ministral **5.0.0.dev0**. Current extra `local` is `transformers>=4.51`. S8 harness, not this census.

Non-blockers: Qwen/OLMo Apache ungated; Ministral Instruct-BF16 confirmed not FP8; Think vs Instruct OLMo ids are distinct; 16 GB VRAM is enough on paper for NF4 8B and tight for Gemma 12B.

---

## Return contract

```text
status: ok
files_touched: [docs/stages/stage-8/CENSUS.md]
run_ids: none
numbers: none (no generate; Hub file sizes and SHAs are metadata, not results)
blockers:
  - C: 141.5 GB free < ~174.7 GB BF16 weights; download only in WSL HF_HOME on /
  - Gemma 4 license page + Ministral privacy extra_gated_description
  - ADR-0023..0026 missing
  - transformers extra too old for Gemma 4 / Ministral 3
next_agent: ADR freeze (0023-0026), then S8 harness
do_not:
  - download 10 checkpoints onto C:
  - afterlife generate / spend API
  - implement Wave 1 in this census
  - edit the freeze-ready plan file
  - edit refs.bib or paper/main.tex
  - load Ministral Instruct-2512 (FP8) or Olmo-3-7B (404) or Olmo Think
  - treat plan §4.14 "factorial interleaves models" as accurate (outer loop is generator)
```
