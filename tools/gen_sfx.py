"""Generate raw sound-effect variants with Stable Audio Open 1.0 through ComfyUI.

Reads tools/sfx_prompts.json, runs one ComfyUI job per (sound, seed), converts the
lossless FLAC that ComfyUI writes into WAV, and logs every setting per file.
Raw audio stays outside the repo; nothing is trimmed or selected here.

Run with the ComfyUI venv:
    E:/7270/tools/ComfyUI/.venv/Scripts/python.exe tools/gen_sfx.py
"""

import datetime
import hashlib
import json
import platform
import subprocess
import sys
import time
import urllib.request
import uuid
import wave
from pathlib import Path

import av
import numpy as np

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "tools" / "sfx_prompts.json"
REPO_LOG_COPY = REPO / "design" / "audio" / "sfx-gen-log.md"

COMFY = Path(r"E:\7270\tools\ComfyUI")
COMFY_PY = COMFY / ".venv" / "Scripts" / "python.exe"
OUT = Path(r"E:\7270\tools\sfx_raw")
FLAC_DIR = OUT / "_flac"
HOST = "127.0.0.1"
PORT = 8188
BASE = f"http://{HOST}:{PORT}"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def http_json(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def server_up():
    try:
        http_json("/system_stats")
        return True
    except OSError:
        return False


def start_server():
    """Start ComfyUI bound to localhost only, writing outputs into FLAC_DIR."""
    log = open(OUT / "_comfy_server.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(COMFY_PY), "main.py", "--listen", HOST, "--port", str(PORT),
         "--output-directory", str(FLAC_DIR)],
        cwd=COMFY, stdout=log, stderr=subprocess.STDOUT,
    )
    for _ in range(300):
        if proc.poll() is not None:
            sys.exit(f"ComfyUI exited early (code {proc.returncode}); see {OUT / '_comfy_server.log'}")
        if server_up():
            return proc
        time.sleep(1)
    proc.terminate()
    sys.exit("ComfyUI did not come up within 300 s")


def workflow(cfg, sound, seed, prefix, gain_db):
    s = float(sound["seconds"])
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": cfg["model"]}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": cfg["text_encoder"], "type": "stable_audio"}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": sound["prompt"], "clip": ["2", 0]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": cfg["negative"], "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningStableAudio",
              "inputs": {"positive": ["3", 0], "negative": ["4", 0], "seconds_start": 0.0, "seconds_total": s}},
        "6": {"class_type": "EmptyLatentAudio", "inputs": {"seconds": s, "batch_size": 1}},
        "7": {"class_type": "KSampler",
              "inputs": {"model": ["1", 0], "seed": seed, "steps": cfg["steps"], "cfg": cfg["cfg"],
                         "sampler_name": cfg["sampler"], "scheduler": cfg["scheduler"],
                         "positive": ["5", 0], "negative": ["5", 1], "latent_image": ["6", 0],
                         "denoise": cfg["denoise"]}},
        "8": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
        # The decoder can exceed +-1.0, which the 16-bit save hard-clips; attenuate before saving.
        "10": {"class_type": "AudioAdjustVolume", "inputs": {"audio": ["8", 0], "volume": int(gain_db)}},
        "9": {"class_type": "SaveAudio", "inputs": {"audio": ["10", 0], "filename_prefix": prefix}},
    }


def clipped_samples(path):
    with wave.open(str(path)) as w:
        dtype = {2: np.int16, 4: np.int32}[w.getsampwidth()]
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=dtype).astype(np.int64)
    full = np.iinfo(dtype).max
    return int((np.abs(a) >= full - 1).sum())


def run_job(graph):
    client = str(uuid.uuid4())
    pid = http_json("/prompt", {"prompt": graph, "client_id": client})["prompt_id"]
    while True:
        hist = http_json(f"/history/{pid}")
        if pid in hist:
            entry = hist[pid]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status.get("messages", []))[:2000])
            files = entry.get("outputs", {}).get("9", {}).get("audio", [])
            if files:
                f = files[0]
                return FLAC_DIR / f.get("subfolder", "") / f["filename"]
            if status.get("completed"):
                raise RuntimeError("job finished without an audio output")
        time.sleep(0.5)


def flac_to_wav(src, dst):
    """Decode FLAC and write WAV with the same integer samples (no resampling, no dither)."""
    with av.open(str(src)) as c:
        stream = c.streams.audio[0]
        rate, channels = stream.rate, stream.channels
        chunks, fmt = [], None
        for frame in c.decode(stream):
            fmt = frame.format
            a = frame.to_ndarray()
            a = a.T if fmt.is_planar else a.reshape(-1, channels)
            chunks.append(a)
    pcm = np.concatenate(chunks)
    if pcm.dtype == np.int16:
        width = 2
    elif pcm.dtype == np.int32:
        width = 4
    else:
        raise RuntimeError(f"unexpected FLAC sample format {fmt.name}")
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(np.ascontiguousarray(pcm).tobytes())
    return rate, channels, width * 8, len(pcm) / rate


def write_logs(meta, entries):
    (OUT / "gen_log.json").write_text(json.dumps({"run": meta, "files": entries}, indent=2), encoding="utf-8")
    lines = [
        "# SFX generation log (raw variants)",
        "",
        f"Generated {meta['started']} – {meta.get('finished', 'in progress')}. Raw WAVs live in `{OUT}` (not in the repo).",
        "",
        f"- Model: `{meta['model']}` sha256 `{meta['model_sha256']}`",
        f"- Text encoder: `{meta['text_encoder']}` sha256 `{meta['text_encoder_sha256']}`",
        f"- ComfyUI {meta['comfyui_version']} (commit `{meta['comfyui_commit']}`), torch {meta['torch']}, {meta['gpu']}",
        f"- Sampler `{meta['sampler']}`, scheduler `{meta['scheduler']}`, steps {meta['steps']}, cfg {meta['cfg']}, denoise {meta['denoise']}",
        f"- Negative prompt: \"{meta['negative']}\"",
        f"- Gain before save: {meta['gain_db']} dB (fallback {meta['fallback_gain_db']} dB for any file that still clips)",
        f"- History: {meta['history']}",
        f"- Reproducibility: {meta['reproducibility']}",
        "",
        "| File | Sound | Seed | Requested s | Actual s | Rate / ch / bits | Gain dB | Clipped samples | Gen time s | Prompt | SHA-256 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in entries:
        if e.get("error"):
            lines.append(f"| — | {e['sound']} | {e['seed']} | {e['requested_seconds']} | FAILED | | | | | {e['prompt']} | {e['error'][:120]} |")
        else:
            note = f" ({e['note']})" if e.get("note") else ""
            lines.append(
                f"| `{e['file']}` | {e['sound']} | {e['seed']} | {e['requested_seconds']} | {e['actual_seconds']:.3f} | "
                f"{e['sample_rate']} / {e['channels']} / {e['bits']} | {e['gain_db']}{note} | {e['clipped_samples']} | "
                f"{e['gen_seconds']:.1f} | {e['prompt']} | `{e['sha256'][:16]}…` |")
    text = "\n".join(lines) + "\n"
    (OUT / "gen_log.md").write_text(text, encoding="utf-8")
    REPO_LOG_COPY.parent.mkdir(parents=True, exist_ok=True)
    REPO_LOG_COPY.write_text(text, encoding="utf-8")


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    FLAC_DIR.mkdir(parents=True, exist_ok=True)

    import torch  # only for the log header
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=COMFY, capture_output=True, text=True).stdout.strip()
    version = subprocess.run(["git", "describe", "--tags"], cwd=COMFY, capture_output=True, text=True).stdout.strip()
    print("hashing model files…", flush=True)
    meta = {
        "started": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": cfg["model"], "model_sha256": sha256(COMFY / "models" / "checkpoints" / cfg["model"]),
        "text_encoder": cfg["text_encoder"],
        "text_encoder_sha256": sha256(COMFY / "models" / "text_encoders" / cfg["text_encoder"]),
        "comfyui_version": version, "comfyui_commit": commit,
        "torch": torch.__version__, "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "python": platform.python_version(),
        "reproducibility": (f"{cfg['sampler']} is a stochastic (SDE) sampler: the same seed reproduces the same audio only on "
                            "the same machine with the same software versions (GPU, driver, torch, ComfyUI and model files above)."),
        **{k: cfg[k] for k in ("sampler", "scheduler", "steps", "cfg", "denoise", "negative", "gain_db",
                               "fallback_gain_db", "history")},
    }

    log_path = OUT / "gen_log.json"
    entries = json.loads(log_path.read_text(encoding="utf-8"))["files"] if log_path.exists() else []
    entries = [e for e in entries if not e.get("error")]  # retry earlier failures

    proc = None if server_up() else start_server()
    try:
        for sound in cfg["sounds"]:
            for seed in cfg["seeds"]:
                name = f"{sound['id']}_seed{seed}"
                wav = OUT / f"{name}.wav"
                if wav.exists():
                    print(f"skip {name} (exists)", flush=True)
                    continue
                print(f"generating {name} ({sound['seconds']} s)…", flush=True)
                base = {"sound": sound["id"], "seed": seed, "requested_seconds": sound["seconds"],
                        "prompt": sound["prompt"], "negative": cfg["negative"], "steps": cfg["steps"],
                        "cfg": cfg["cfg"], "sampler": cfg["sampler"], "scheduler": cfg["scheduler"],
                        "denoise": cfg["denoise"]}
                t0 = time.time()
                note = None
                try:
                    gain = cfg["gain_db"]
                    flac = run_job(workflow(cfg, sound, seed, f"{name}_{gain}dB", gain))
                    rate, ch, bits, dur = flac_to_wav(flac, wav)
                    clipped = clipped_samples(wav)
                    if clipped:
                        note = f"clipped {clipped} samples at {gain} dB; regenerated at {cfg['fallback_gain_db']} dB"
                        print(f"  {note}", flush=True)
                        gain = cfg["fallback_gain_db"]
                        flac = run_job(workflow(cfg, sound, seed, f"{name}_{gain}dB", gain))
                        rate, ch, bits, dur = flac_to_wav(flac, wav)
                        clipped = clipped_samples(wav)
                except Exception as e:  # keep going; failures are logged and retried next run
                    entries.append({**base, "error": str(e)})
                    print(f"  FAILED: {e}", flush=True)
                    write_logs(meta, entries)
                    continue
                entries.append({**base, "file": wav.name, "flac": str(flac), "actual_seconds": dur,
                                "sample_rate": rate, "channels": ch, "bits": bits, "gain_db": gain,
                                "clipped_samples": clipped, "note": note,
                                "gen_seconds": time.time() - t0, "sha256": sha256(wav),
                                "generated": datetime.datetime.now().astimezone().isoformat(timespec="seconds")})
                print(f"  ok {wav.name} {dur:.3f} s at {gain} dB, clipped={clipped}, {time.time() - t0:.1f} s", flush=True)
                write_logs(meta, entries)
    finally:
        if proc:
            proc.terminate()
            proc.wait(timeout=60)

    meta["finished"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    write_logs(meta, entries)
    failed = [e for e in entries if e.get("error")]
    print(f"done: {len(entries) - len(failed)} ok, {len(failed)} failed; log at {OUT / 'gen_log.md'}")


if __name__ == "__main__":
    main()
