# Sources

> Draft — 2026-10-01. Every tool and model used to make assets for this project. Rows marked TODO are filled in before the commit that first uses them.

## Generation tools

| Tool | Version | Source | License | Used for |
|---|---|---|---|---|
| Google Gemini (Gemini web app, image generation) | Model: TODO · Version: TODO | https://gemini.google.com | Google Terms of Service and Generative AI Additional Terms | All in one Gemini chat, in `design/character/generated/`. Accepted, full size: CHAR-REF v2 · CHAR-IDLE v1 · CHAR-RUN-CONTACT v3 · CHAR-RUN-PASSING v1 (PNG screenshot, see notes) · CHAR-RISE v1 · CHAR-FALL v1 · CHAR-CAST v3 · CHAR-HURT v1 · CHAR-FAIL v1 · CHAR-WIN v1. Rejected, 256 px thumbnails in `rejected/`: CHAR-REF v1, v3 · CHAR-RUN-PASSING v0. Rejected, no file kept: CHAR-RUN-CONTACT attempts 1–2 · CHAR-CAST attempts 1–2 |
| ComfyUI | v0.38.1 (commit `20ca544ee0436721d8eb5f544665e490609f72c8`) | https://github.com/comfyanonymous/ComfyUI | GPL-3.0 | Running Stable Audio Open locally |
| Stable Audio Open 1.0 | `model.safetensors` at commit `f21265c1e2710b3bd2386596943f0007f55f802e` (sha256 `7b20458a…66b57e`) | https://huggingface.co/stabilityai/stable-audio-open-1.0 | Stability AI Community License (last updated July 5, 2024) — gated; accepted by the author on Hugging Face | Sound effects |
| T5-base text encoder (for Stable Audio Open) | `model.safetensors` at commit `a9723ea7f1b39c1eae772870f3b547bf6ef7e6c1` (sha256 `a9090354…c8f5b4`) | https://huggingface.co/google-t5/t5-base | Apache-2.0 | Text conditioning for Stable Audio Open, as in ComfyUI's official audio example (https://comfyanonymous.github.io/ComfyUI_examples/audio/) |

## Runtime

| Tool | Version | Source | License |
|---|---|---|---|
| PyTorch | 2.11.0+cu128 | https://pytorch.org · https://download.pytorch.org/whl/cu128 | BSD-3-Clause |
| torchvision | 0.26.0+cu128 | https://github.com/pytorch/vision | BSD-3-Clause |
| torchaudio | 2.11.0+cu128 | https://github.com/pytorch/audio | BSD-2-Clause |
| Python | 3.12.7 | https://www.python.org | PSF-2.0 |
| uv | 0.11.19 | https://github.com/astral-sh/uv | MIT or Apache-2.0 |
| Godot Engine | 4.7.2-stable | https://godotengine.org | MIT |

Hardware: NVIDIA GeForce RTX 5060 Laptop GPU (8 GB), Windows 11.

## Notes

- **SynthID:** images made with Google Gemini carry an invisible SynthID watermark embedded in the pixels. Google designs it to survive common edits such as resizing and cropping, so the CHAR-REF images and their thumbnails should be treated as carrying it.
- **Stable Audio Open attribution:** the Community License (§IV.a) requires that anything distributed with or made from the model keeps the notice "This Stability AI Model is licensed under the Stability AI Community License, Copyright © Stability AI Ltd. All Rights Reserved" and shows "Powered by Stability AI". You own the generated outputs (§IV.c.iii). Commercial use is allowed only for revenue under US $1M and requires registering at https://stability.ai/community-license. This project is coursework (non-commercial).
- **Generated image convention:** accepted images stay full size in `design/character/generated/`; rejected ones are kept only as 256 px-wide thumbnails in `design/character/generated/rejected/`. Rejected run attempts: 1 (two frames side by side, staff cut off, floating foot, ground line), 2 (model edited the reference sheet instead of drawing a new pose).
- **CHAR-RUN-PASSING v1 is a screenshot:** `CHAR-RUN-PASSING-v1.png` (900×1024) is a screenshot of the accepted Gemini output; the original download was lost. Screenshot pixels, not the original file, so it may differ slightly in resolution and color from the other frames.
- **CHAR-RUN-PASSING v0 (rejected):** wide stride, gray ground band, and too similar to RUN-CONTACT for a 2-frame loop. Commit `2a90b0b` mistakenly added this image at full size as `CHAR-RUN-PASSING-v1.jpg`; it was removed in the next commit and replaced by the v0 thumbnail.
- **Run loop:** RUN-CONTACT v3 + RUN-PASSING v1, chosen after comparing loop previews.
- **CHAR-RISE v1:** staff not raised as the prompt asked, but consistent with IDLE, so accepted.
- **CHAR-CAST v3:** third cast attempt (file originally named CAST-v1). Its yellow-green crystal glow is removed in cleanup; the glow is added in Godot instead.
- **CHAR-RUN-PASSING v1:** hat about 5% smaller than in the other frames, and less forward lean than RUN-CONTACT v3. During cleanup, scale by head height and re-check the run loop in the engine.
- Model weights and the ComfyUI install live in `E:\7270\tools\`, outside this repo, and are not committed.
