# CHANGE-BRIEF — plan and predictions

> Draft v1 — written before any generation. Storyboard panel numbers (P1–P7) match STORYBOARD.md.

## Storyboard panels referenced
P1 first view / title · P2 core action (first cast at a wolf) · P3 success (wolf defeated) · P4 failure (fall into a pit) · P5 recovery (restart, heal) · P6 boss fight · P7 end (exit reached)

## Generation tools
- Music: MUS-LOOP from Suno, free plan (v4.5-all model, non-commercial terms, tracks public in Suno's feed). Free accounts have 7 lifetime downloads, so candidates are judged in the browser and logged by screenshot; only the final track is downloaded.
- Sound effects: all SFX from Stable Audio Open, run locally on my RTX 5060, with prompt, seed and duration recorded for reproduction.
- Art: local image model (to be recorded in SOURCES.md when set up).

## Priority (deadline Oct 4)
1. Must: mage states, ENV-BG, ENV-TILES with pits, one wolf, fireball, the five required SFX, MUS-LOOP, pause, mute, fail/restart, exit.
2. Next, in this order: heal spell (SFX-HEAL, FX-HEAL), boss (same wolf at 2×), spikes.
3. If time allows: falling stalactite (SFX-ROCK). Anything cut is listed as a known limitation.

## Asset list
Req = required by the assignment; Opt = only if time allows (a code-drawn placeholder is used otherwise and logged as such).

| ID | Asset | Source | Panels | Req |
|---|---|---|---|---|
| CHAR-REF | turnaround reference, high-res | generated | all | Req |
| CHAR-IDLE | idle (also held during heal) | generated | P1, P5 | Req |
| CHAR-RUN | run: contact + passing | generated | P2 | Req |
| CHAR-RISE / CHAR-FALL | jump up / down | generated | P2, P4 | Req |
| CHAR-CAST | cast | generated | P2, P6 | Req |
| CHAR-HURT | hurt | generated | P6 | Req |
| CHAR-FAIL | fail | generated | P4 | Req |
| CHAR-WIN | victory | generated | P7 | Req |
| ENV-BG | cave background | generated | all | Req |
| ENV-TILES | ground tiles incl. pit edge tiles | generated | P1–P7 | Req |
| ENV-SPIKE | spikes | generated | P2 | Opt |
| ENV-STALACTITE | falling stalactite | generated | P2 | Opt |
| ENV-EXIT | cave exit | generated | P7 | Opt |
| ENEMY-WOLF | run (2–3 frames), lunge, defeated; boss = same art at 2× | generated | P2, P3, P6 | Opt |
| FX-FIREBALL / FX-BURST | fireball (2–3 frames), impact | generated | P2, P3 | Opt |
| FX-HEAL | gold glow | Godot particles (not generated) | P5 | — |
| UI-CROSSHAIR / UI-HEART / UI-HEAL | cursor, HP icon, heal icon | generated or code-drawn | P2, P5 | Opt |
| SFX-CAST | fireball cast | generated (Stable Audio Open) | P2 | Req |
| SFX-WOLF-DOWN | wolf defeated | generated (Stable Audio Open) | P3 | Req |
| SFX-HURT | player hurt | generated (Stable Audio Open) | P6 | Req |
| SFX-FAIL | failure | generated (Stable Audio Open) | P4 | Req |
| SFX-CLEAR | level clear | generated (Stable Audio Open) | P7 | Req |
| SFX-HEAL | heal completed | generated (Stable Audio Open) | P5 | Opt |
| SFX-ROCK | stalactite warning crackle | generated (Stable Audio Open) | P2 | Opt |
| MUS-LOOP | cave music loop | generated (Suno) | P1–P6 | Req |

## Event-to-sound map
Rule: game code emits a signal for the event; an audio node listens and plays the sound. Sound never changes game state, so a muted or missing sound changes nothing.

| Sound | Exact trigger | Double-trigger guard |
|---|---|---|
| SFX-CAST | `Player.cast()` after the cooldown check passes and one fireball is spawned | `is_action_just_pressed` (holding does not repeat); cooldown timer |
| SFX-WOLF-DOWN | `Wolf.take_damage()` when HP reaches 0 | `dead` flag set first; hurtbox disabled with `set_deferred` so a second fireball in the same frame is ignored |
| SFX-HURT | `Player.take_damage()` when not invulnerable | invulnerability timer starts in the same call |
| SFX-HEAL | heal channel timer timeout | `heal_available = false` before the signal; cancel stops the timer |
| SFX-FAIL | `Player.fail()` (pit kill zone or HP 0) | `is_failing` flag; physics stopped |
| SFX-CLEAR | exit `body_entered` after the boss is dead | `cleared` flag |

## Music behavior
- Start: plays from the top when the scene loads.
- Pause (Esc): music pauses with the game and resumes from the same point.
- Failure: music stops immediately, SFX-FAIL plays, the scene reloads after ~1.2 s (longer than SFX-FAIL), music restarts from the top.
- Boss: same loop continues.
- Success / end of slice: on reaching the exit the music stops, SFX-CLEAR plays, a "Cleared" screen stays in silence until the player restarts.
- Mute: M mutes the Music bus, N mutes the SFX bus (`AudioServer.set_bus_mute`).

## Predicted failure cases and checks
1. **Generated frames drift in proportion, especially toward chibi.** Check: overlay every frame on CHAR-REF at 64 px; head height 15 ± 1 px, same eye line.
2. **"Pixel art" output is not on a real pixel grid or uses off-palette colors.** Check: nearest-neighbor downscale to 64 px, then a script counts colors not in the palette ramps (target 0).
3. **The mage disappears against the cave background.** Check: silhouette test on ENV-BG and a grayscale screenshot at 1×; hair must be the brightest shape, indigo one value step above the darkest cave tone.
4. **A wolf-defeated or hurt sound fires twice on one event.** Check (automated): scripted test fires two fireballs into a wolf with 1 HP in the same frame, and holds the cast button for 2 s; count signal emissions per event (expected 1, and cooldown-limited casts).
5. **The music loop clicks or gaps at the seam.** Check: cut at a bar boundary, listen to at least three repetitions, inspect the waveform at the seam.
6. **SFX-FAIL is cut off by the scene reload.** Check: listen to a pit fall; the reload delay must exceed the sound length.
7. **The slice is unreadable with sound muted.** Check: a full muted run; every event must have a visual cue (cast flash, wolf hit flash and fall, hurt pose + blink, fail text, heal glow, Cleared screen).

## Tuning values (predictions, adjusted after playtest)
Player 5 HP, 1 s invulnerability · fireball 1 damage, 0.35 s cooldown · heal once, 1 s channel · wolf 2 HP, 0.5 s growl, 1 damage · boss 10 HP, 0.7 s growl, 2.5–3 s between lunges, 0.8 s pause after each, 2 damage · stalactite 1 damage, 0.6 s shake before falling.
