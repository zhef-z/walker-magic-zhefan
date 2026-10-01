# CONCEPT — walker-<game-name>-zhefan

> Draft v1 — written before any generation. Later revisions are added below, not rewritten.
> Drafted with Claude from my design decisions; see FRICTIONAL.md for who decided what.

## The game in two sentences
The player is a young fire mage descending through a dark cave, carrying the only warm light in it at the tip of her staff. She fights her way past wolves and cave hazards, aiming fireballs with the mouse, until she defeats the great wolf guarding the exit.

## Core loop
- **Repeated action:** move forward, spot a threat, aim and cast a fireball (or jump past a hazard).
- **Decision each time:** shoot the wolf now or reposition first; wait for the stalactite to fall or run under it; jump the pit now or deal with the threat nearby first.
- **Risk:** spikes, falling stalactites and wolf lunges cost 1 of 5 HP, and the boss's lunge costs 2; falling into a pit or losing all HP restarts the level. One heal per run means the player also decides when it is safe to spend it.

## Scope of the asset slice
- Player: 5 HP, 1 s of invulnerability and a knockback after each hit.
- Controls: WASD move, Space jump, left mouse cast (fireball flies toward the cursor), E heal, Esc pause, M / N mute music / effects.
- Fireball: 1 damage, short cooldown, destroyed by walls.
- Heal: once per run, 1 s channel on the ground, restores full HP. Taking damage, moving or jumping cancels it without using it up. Shown as a gold particle glow around the mage (reuses an existing pose).
- Enemies: wolf (2 HP; patrols, growls, then lunges, 1 damage); great wolf boss (same wolf at 2× integer scale, 10 HP, lunge deals 2 damage, longer growl and a pause after each lunge, hit flash + HP bar). Defeating the boss opens the exit.
- Hazards: spikes (−1 HP), falling stalactite (shakes and drops dust first, −1 HP), pits (restart; kept easy to jump).
- No crouch; fireball and heal are the only two skills.
- Deadline priority: heal comes first after the must-haves; the stalactite is built only if time allows (see CHANGE-BRIEF.md).
- Out of scope, planned for the full game: more spells, charged fireball, more enemy types.

## Design pillars
1. **Every failure is fair.** The heavier the penalty, the easier the challenge. *Visual:* pits end in clearly marked edge tiles and are well within jump distance; stalactites shake before they fall. *Sound:* a short rock crackle warns before a stalactite drops.
2. **Your fire is the only warmth.** The cave is cold and dark; the mage's fire is the one warm thing in it. *Visual:* the cave uses desaturated cool tones, and the fireball and staff crystal are the only saturated warm colors. *Sound:* the cast has a bright crackling whoosh against a low, hollow cave ambience.
3. **Readable at a glance, even muted.** The player always knows where she is, what hit her, and whether her attack landed. *Visual:* white hair stays the brightest shape on screen; enemies flash white when hit; failure shows a one-line reason. *Sound:* hurt and failure use two clearly different sounds.
4. **Small mage, big threat.** She is fragile but capable. *Visual:* the boss wolf is twice her size and fills the arena. *Sound:* the boss has a low growl that the smaller wolves do not.

## Art direction
Side-view pixel art at small on-screen size, with a dark, cool cave and a single warm light source. Pixel art hides small detail drift between generated frames and makes the silhouette do the work, which serves pillars 1 and 3.
- Reference notes: damp limestone and wet stone reflecting faint light; torch-lit underground chambers where most of the frame falls into deep shadow; a cold palette of slate blue and gray-brown, broken only by ember orange and crystal red.
- Main character: white twin tails tied with small red bows, red eyes, a soft and cute face, staff with a red crystal tip. Hat and outfit: *to be designed in CHARACTER-SHEET.md.*

## Audio direction
The player should feel alone and alert in the dark, with every cast feeling like a small act of defiance.
- Music: one tense, low loop (hollow percussion, sustained low strings) that plays throughout the slice.
- Pause: music pauses with the game.
- Failure: music stops and the failure sound plays; on restart the music begins again from the top.
- Success: when the boss falls and the player reaches the exit, the music stops and the clear sound plays.
- Sound events: cast, wolf defeated, hurt, heal, failure, level clear (exact triggers in CHANGE-BRIEF.md).

## Open decisions
- Facing: always face the cursor, or face movement direction and turn toward the cursor only when casting.
- Hat and outfit design and final palette (CHARACTER-SHEET.md).
- Game name for the project folder.
