# SFX generation log (raw variants)

Generated 2026-10-02T16:33:37-04:00 – 2026-10-02T16:36:42-04:00. Raw WAVs live in `E:\7270\tools\sfx_raw` (not in the repo).

- Model: `stable_audio_open_1.0.safetensors` sha256 `7b20458a071231aaf32613b6fbc7945f28f34dbba4f295bb49bad56f5f66b57e`
- Text encoder: `t5_base.safetensors` sha256 `a90903540cc02cbeb7ff9f823f1a80eb778c7e22426a0e620b01c77a5ec8f5b4`
- ComfyUI v0.38.1 (commit `20ca544ee0436721d8eb5f544665e490609f72c8`), torch 2.11.0+cu128, NVIDIA GeForce RTX 5060 Laptop GPU
- Sampler `dpmpp_3m_sde_gpu`, scheduler `exponential`, steps 100, cfg 7.0, denoise 1.0
- Negative prompt: "music, melody, speech, vocals, singing, low quality, noise, hum"
- Gain before save: -6 dB (fallback -9 dB for any file that still clips)
- History: First run clipped in 10/18 files; regenerated at -6 dB (same seeds, so content is unchanged and only the level differs). The clipped first run is kept in _clipped_run1/.
- Reproducibility: dpmpp_3m_sde_gpu is a stochastic (SDE) sampler: the same seed reproduces the same audio only on the same machine with the same software versions (GPU, driver, torch, ComfyUI and model files above).

| File | Sound | Seed | Requested s | Actual s | Rate / ch / bits | Gain dB | Clipped samples | Gen time s | Prompt | SHA-256 |
|---|---|---|---|---|---|---|---|---|---|---|
| `SFX-CAST_seed1.wav` | SFX-CAST | 1 | 1.5 | 1.486 | 44100 / 2 / 16 | -6 | 0 | 10.3 | short magical fire spell cast, quick whoosh with crackling flames, bright and punchy, game sound effect | `8ecc2c241f99c47d…` |
| `SFX-CAST_seed2.wav` | SFX-CAST | 2 | 1.5 | 1.486 | 44100 / 2 / 16 | -6 | 0 | 7.7 | short magical fire spell cast, quick whoosh with crackling flames, bright and punchy, game sound effect | `dae98ce3d44a4704…` |
| `SFX-CAST_seed3.wav` | SFX-CAST | 3 | 1.5 | 1.486 | 44100 / 2 / 16 | -6 | 0 | 8.8 | short magical fire spell cast, quick whoosh with crackling flames, bright and punchy, game sound effect | `6e90de8337555a36…` |
| `SFX-WOLF-DOWN_seed1.wav` | SFX-WOLF-DOWN | 1 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 8.7 | small wolf yelp followed by a soft thud on stone, short, game sound effect | `a02275ed36f7d7a4…` |
| `SFX-WOLF-DOWN_seed2.wav` | SFX-WOLF-DOWN | 2 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 9.3 | small wolf yelp followed by a soft thud on stone, short, game sound effect | `11bf1cb9140f10e8…` |
| `SFX-WOLF-DOWN_seed3.wav` | SFX-WOLF-DOWN | 3 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 7.2 | small wolf yelp followed by a soft thud on stone, short, game sound effect | `f3fcebe1aed4ba60…` |
| `SFX-HURT_seed1.wav` | SFX-HURT | 1 | 1.0 | 1.022 | 44100 / 2 / 16 | -6 | 0 | 9.8 | short soft body impact hit with a cloth rustle, game damage sound | `586de883fc9be097…` |
| `SFX-HURT_seed2.wav` | SFX-HURT | 2 | 1.0 | 1.022 | 44100 / 2 / 16 | -6 | 0 | 7.3 | short soft body impact hit with a cloth rustle, game damage sound | `cc598a6f12bf3569…` |
| `SFX-HURT_seed3.wav` | SFX-HURT | 3 | 1.0 | 1.022 | 44100 / 2 / 16 | -6 | 0 | 8.8 | short soft body impact hit with a cloth rustle, game damage sound | `83c113a778793e1b…` |
| `SFX-FAIL_seed1.wav` | SFX-FAIL | 1 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 7.2 | low descending magical tone fading into darkness, short game failure sound | `76b595a1892eafcb…` |
| `SFX-FAIL_seed2.wav` | SFX-FAIL | 2 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 9.5 | low descending magical tone fading into darkness, short game failure sound | `88fcf906eb0a3a74…` |
| `SFX-FAIL_seed3.wav` | SFX-FAIL | 3 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 7.3 | low descending magical tone fading into darkness, short game failure sound | `d3d7172c846fa858…` |
| `SFX-CLEAR_seed1.wav` | SFX-CLEAR | 1 | 3.0 | 2.972 | 44100 / 2 / 16 | -6 | 0 | 13.5 | short bright rising magical chime, warm and hopeful, game level complete jingle | `501dbd4675c398cb…` |
| `SFX-CLEAR_seed2.wav` | SFX-CLEAR | 2 | 3.0 | 2.972 | 44100 / 2 / 16 | -6 | 0 | 9.8 | short bright rising magical chime, warm and hopeful, game level complete jingle | `beba6884bf0ec34a…` |
| `SFX-CLEAR_seed3.wav` | SFX-CLEAR | 3 | 3.0 | 2.972 | 44100 / 2 / 16 | -6 | 0 | 6.8 | short bright rising magical chime, warm and hopeful, game level complete jingle | `2b15e886c9c534e1…` |
| `SFX-HEAL_seed1.wav` | SFX-HEAL | 1 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 9.4 | soft warm shimmering magical sparkle rising, gentle healing spell, game sound | `0e858fdf57406621…` |
| `SFX-HEAL_seed2.wav` | SFX-HEAL | 2 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 7.2 | soft warm shimmering magical sparkle rising, gentle healing spell, game sound | `5da87862fc009da1…` |
| `SFX-HEAL_seed3.wav` | SFX-HEAL | 3 | 2.0 | 2.043 | 44100 / 2 / 16 | -6 | 0 | 9.4 | soft warm shimmering magical sparkle rising, gentle healing spell, game sound | `53abe80f54675d2d…` |
