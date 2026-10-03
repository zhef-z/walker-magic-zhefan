# Sources

> Draft — 2026-10-01. Every tool and model used to make assets for this project. Rows marked TODO are filled in before the commit that first uses them.

## Generation tools

| Tool | Version | Source | License | Used for |
|---|---|---|---|---|
| Google Gemini (Gemini web app, image generation) | Model: TODO · Version: TODO | https://gemini.google.com | Google Terms of Service and Generative AI Additional Terms | Every generated image: mage, wolf, FX, cave tiles and background. See **Generated images** below. |
| ComfyUI | v0.38.1 (commit `20ca544ee0436721d8eb5f544665e490609f72c8`) | https://github.com/comfyanonymous/ComfyUI | GPL-3.0 | Running Stable Audio Open locally |
| Stable Audio Open 1.0 | `model.safetensors` at commit `f21265c1e2710b3bd2386596943f0007f55f802e` (sha256 `7b20458a…66b57e`) | https://huggingface.co/stabilityai/stable-audio-open-1.0 | Stability AI Community License (last updated July 5, 2024) — gated; accepted by the author on Hugging Face | Sound effects |
| T5-base text encoder (for Stable Audio Open) | `model.safetensors` at commit `a9723ea7f1b39c1eae772870f3b547bf6ef7e6c1` (sha256 `a9090354…c8f5b4`) | https://huggingface.co/google-t5/t5-base | Apache-2.0 | Text conditioning for Stable Audio Open, as in ComfyUI's official audio example (https://comfyanonymous.github.io/ComfyUI_examples/audio/) |

## Generated images (Google Gemini)

Accepted images stay full size; rejected ones are kept only as 256 px-wide thumbnails in the group's `rejected/` folder.

- **`*-thumb.png`:** thumbnail from a screenshot of the Gemini output; original download not kept. The author made these from screenshots shared in a chat with Claude. This covers all 13 `.png` thumbnails: CHAR-CAST v1, v2, v4 · CHAR-RUN v1, v2 · ENEMY-WOLF-DOWN v2 · WOLF-R1 run v0, run v1, lunge v1, down v1, derived · ENV-TILES v1 · ENV-BG v2.
- **`*-thumb.jpg`:** made from the original downloaded file (CHAR-REF v1, v3 · CHAR-RUN-PASSING v0).

**Workflow change:** the mage and the first wolf round shared one long Gemini chat, and earlier images started leaking into new ones (the mage's head in a wolf frame, cave paintings in the tiles). From the wolf onward, each asset group got its own Gemini chat to stop this context bleed.

### Mage — `design/character/generated/` (chat 1, shared)

| Asset | Status | File | Notes |
|---|---|---|---|
| CHAR-REF v1 | rejected | `rejected/CHAR-REF-v1-thumb.jpg` | Staff broke into loose pixels at 64 px (see CHARACTER-SHEET Revision 1). |
| CHAR-REF v2 | **accepted** | `CHAR-REF-v2.jpg` | Mid-thigh tunic and thicker staff accepted in Revision 1. |
| CHAR-REF v3 | rejected | `rejected/CHAR-REF-v3-thumb.jpg` | Unchanged from v2. |
| CHAR-IDLE v1 | **accepted** | `CHAR-IDLE-v1.jpg` | |
| CHAR-RUN-CONTACT attempt 1 | rejected | `rejected/CHAR-RUN-v1-thumb.png` | Two frames side by side, staff cut off, floating foot, ground line. |
| CHAR-RUN-CONTACT attempt 2 | rejected | `rejected/CHAR-RUN-v2-thumb.png` | Model edited the reference sheet instead of drawing a new pose. |
| CHAR-RUN-CONTACT v3 | **accepted** | `CHAR-RUN-CONTACT-v3.jpg` | |
| CHAR-RUN-PASSING v0 | rejected | `rejected/CHAR-RUN-PASSING-v0-thumb.jpg` | See notes. |
| CHAR-RUN-PASSING v1 | **accepted** | `CHAR-RUN-PASSING-v1.png` | Screenshot; see notes. |
| CHAR-RISE v1 | **accepted** | `CHAR-RISE-v1.jpg` | Staff not raised as the prompt asked, but consistent with IDLE. |
| CHAR-FALL v1 | **accepted** | `CHAR-FALL-v1.jpg` | |
| CHAR-CAST attempts 1–2 | rejected | `rejected/CHAR-CAST-v1-thumb.png`, `rejected/CHAR-CAST-v2-thumb.png` | Reason: TODO. |
| CHAR-CAST v3 | **accepted** | `CHAR-CAST-v3.jpg` | File originally named CAST-v1. Yellow-green crystal glow removed in cleanup; glow added in Godot. |
| CHAR-CAST v4 | rejected | `rejected/CHAR-CAST-v4-thumb.png` | Reason: TODO. |
| CHAR-HURT v1 | **accepted** | `CHAR-HURT-v1.jpg` | |
| CHAR-FAIL v1 | **accepted** | `CHAR-FAIL-v1.jpg` | |
| CHAR-WIN v1 | **accepted** | `CHAR-WIN-v1.jpg` | |

### Wolf — `design/character/generated/`

Round 1 (chat 1, shared with the mage) was abandoned because the long chat mixed earlier images into new ones. The wolf was restarted in a new, text-only chat (chat 2), and every accepted wolf frame comes from that chat.

| Asset | Status | File | Notes |
|---|---|---|---|
| Round 1 run v0 | rejected | `rejected/WOLF-R1-RUN-v0-bleed-thumb.png` | The mage's head leaked into the wolf. |
| Round 1 run v1 | rejected | `rejected/WOLF-R1-RUN-v1-thumb.png` | Screenshot. Abandoned with round 1. |
| Round 1 lunge v1 | rejected | `rejected/WOLF-R1-LUNGE-v1-thumb.png` | Abandoned with round 1. |
| Round 1 down v1 | rejected | `rejected/WOLF-R1-DOWN-v1-thumb.png` | Abandoned with round 1. |
| Round 1 frame derived from down v1 | rejected | `rejected/WOLF-R1-DERIVED-thumb.png` | Legs still in the running pose. |
| ENEMY-WOLF-RUN v2 | **accepted** | `ENEMY-WOLF-RUN-v2.jpg` | Chat 2. |
| ENEMY-WOLF-LUNGE v2 | **accepted** | `ENEMY-WOLF-LUNGE-v2.jpg` | Chat 2. |
| ENEMY-WOLF-DOWN v2 | rejected | `rejected/ENEMY-WOLF-DOWN-v2-thumb.png` | Chat 2. Legs still in the running pose. |
| ENEMY-WOLF-DOWN v3 | **accepted** (partially achieved) | `ENEMY-WOLF-DOWN-v3.jpg` | Chat 2. Eyes closed, head and ears down; legs unchanged. The defeat motion is handled in the engine: white flash, tilt, cool blue-gray particles. |

### FX — `design/character/generated/`

| Asset | Status | File | Notes |
|---|---|---|---|
| FX-FIREBALL-BURST v1 | **accepted** (first try) | `FX-FIREBALL-BURST-v1.jpg` | The downloaded original has semi-transparent ghost blobs and dark fragments along the top; only the fireball and the burst are cropped out in cleanup. |

### Environment — `design/environment/generated/`

| Asset | Status | File | Notes |
|---|---|---|---|
| ENV-TILES v1 | rejected | `rejected/ENV-TILES-v1-thumb.png` | Visible seams when tiled; cave paintings leaked in from the background chat. |
| ENV-TILES v2 | **accepted** | `ENV-TILES-v2.jpg` | Only the uniform dark rock is used as the repeating tile, plus the two end pieces; the brighter wall on the left is discarded. |
| ENV-BG v1 | **accepted** | `ENV-BG-v1.jpg` | Framed composition, fixed to the camera. |
| ENV-BG v2 | rejected | `rejected/ENV-BG-v2-thumb.png` | Cave paintings add warm colors, against pillar 2 ("your fire is the only warmth"). |

## Runtime

| Tool | Version | Source | License |
|---|---|---|---|
| PyTorch | 2.11.0+cu128 | https://pytorch.org · https://download.pytorch.org/whl/cu128 | BSD-3-Clause |
| torchvision | 0.26.0+cu128 | https://github.com/pytorch/vision | BSD-3-Clause |
| torchaudio | 2.11.0+cu128 | https://github.com/pytorch/audio | BSD-2-Clause |
| Python | 3.12.7 | https://www.python.org | PSF-2.0 |
| uv | 0.11.19 | https://github.com/astral-sh/uv | MIT or Apache-2.0 |
| Godot Engine | 4.7.2-stable | https://godotengine.org | MIT |
| Pillow | 12.3.0 | https://python-pillow.org | MIT-CMU |
| NumPy | 2.5.2 | https://numpy.org | BSD-3-Clause (with bundled 0BSD/MIT/Zlib parts) |
| SciPy | 1.18.1 | https://scipy.org | BSD-3-Clause |
| PyAV | 19.0.0 | https://github.com/PyAV-Org/PyAV | BSD-3-Clause |

Project scripts: `tools/clean_sprites.py` (sprite cleanup, settings in `tools/sprites.json`, log in `assets/sprites/EDIT-LOG.md`) and `tools/gen_sfx.py` (sound generation, prompts in `tools/sfx_prompts.json`, log in `design/audio/sfx-gen-log.md`). Both run with the ComfyUI venv.

Hardware: NVIDIA GeForce RTX 5060 Laptop GPU (8 GB), Windows 11.

## Notes

- **SynthID:** images made with Google Gemini carry an invisible SynthID watermark embedded in the pixels. Google designs it to survive common edits such as resizing and cropping, so the CHAR-REF images and their thumbnails should be treated as carrying it.
- **Stable Audio Open attribution:** the Community License (§IV.a) requires that anything distributed with or made from the model keeps the notice "This Stability AI Model is licensed under the Stability AI Community License, Copyright © Stability AI Ltd. All Rights Reserved" and shows "Powered by Stability AI". You own the generated outputs (§IV.c.iii). Commercial use is allowed only for revenue under US $1M and requires registering at https://stability.ai/community-license. This project is coursework (non-commercial).
- **CHAR-RUN-PASSING v1 is a screenshot:** `CHAR-RUN-PASSING-v1.png` (900×1024) is a screenshot of the accepted Gemini output; the original download was lost. Screenshot pixels, not the original file, so it may differ slightly in resolution and color from the other frames.
- **CHAR-RUN-PASSING v0 (rejected):** wide stride, gray ground band, and too similar to RUN-CONTACT for a 2-frame loop. Commit `2a90b0b` mistakenly added this image at full size as `CHAR-RUN-PASSING-v1.jpg`; it was removed in the next commit and replaced by the v0 thumbnail.
- **Run loop:** RUN-CONTACT v3 + RUN-PASSING v1, chosen after comparing loop previews.
- **CHAR-RUN-PASSING v1:** hat about 5% smaller than in the other frames, and less forward lean than RUN-CONTACT v3. During cleanup, scale by head height and re-check the run loop in the engine.
- Model weights and the ComfyUI install live in `E:\7270\tools\`, outside this repo, and are not committed.
