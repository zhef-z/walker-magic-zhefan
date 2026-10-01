# Character sheet — <mage name>

> Draft v1 — written before any generation. Pose images in this version are my own hand sketches;
> generated poses are added later as a revision, and judged against this sheet.
> Items marked *PROPOSED* came from Claude and still need my confirmation.

- **Concept in one sentence:** a cute young fire mage with white twin tails and red eyes, carrying the only warm light into a dark cave.
- **Viewport:** 640×360 base resolution, integer-scaled (3× for 1080p, 6× for 4K). Pixel art, nearest-neighbor filter.
- **On-screen size:** about 64 px tall including the hat (about 18% of screen height); body without the hat about 52 px.
- **Proportions:** slender, girlish figure, not chibi. Head-to-body ratio about 1:3.5 (head about 15 px), long legs relative to torso.
- **Silhouette at on-screen size:** `design/character/silhouette.png` — idle pose filled solid black at 64 px, placed on the actual cave background.
- **Reference:** `design/character/turnaround.png` — front, side, three-quarter and back at the same height, with a height bar.

## Appearance
- White twin tails reaching the waist, tied with small red bows and hanging clear of her back; large red eyes with a highlight pixel; light blush and a small mouth. Cute but not chibi.
- View: body in side view, face turned slightly toward the camera (three-quarter face), so both eyes read in every facing.
- *PROPOSED* Details: high collar on the capelet, wide sleeves with gold cuffs, gold hem trim, red ribbon tail trailing from the hat, staff crystal wrapped by a curled branch.
- (v1 idea of an eyepatch dropped before generation: it made the face less cute and hid one red eye.)
- Staff held in the right hand: dark wood shaft, red crystal at the tip. The crystal is where fireballs spawn and where the heal glow centers.
- *PROPOSED* Hat: tall witch hat whose tip bends backward, wide slightly drooping brim, red ribbon band with a small ember charm.
- *PROPOSED* Outfit: short capelet over a knee-length belted tunic, belt with small pouches, short boots.

## Orientation
- Drawn facing **right** only. Facing left is `flip_h` at runtime.
- The design is left-right symmetric enough that flipping has no visible side effect. The staff-tip marker is mirrored in code so fireballs still leave the crystal.
- Facing follows movement; the mage turns toward the cursor at the moment she casts.

## Poses (10)
| # | Pose | Game state | Playback |
|---|---|---|---|
| 1 | Turnaround (front, side, three-quarter, back, height bar) | reference | — |
| 2 | Idle | standing; also held during the heal channel | loop |
| 3 | Run — contact | moving | loop |
| 4 | Run — passing | moving | loop |
| 5 | Rising | jump, going up | once |
| 6 | Falling | jump, coming down | once |
| 7 | Cast | fireball released from the crystal | once |
| 8 | Hurt | took damage (held ~0.3 s with knockback, then blinks during 1 s invulnerability) | once |
| 9 | Fail | fell into a pit or ran out of HP | once |
| 10 | Victory | boss defeated, exit reached | loop |

Images: `design/character/poses/01-turnaround.png` … `10-victory.png`.

## Collision overlay
`design/character/collision.png` — every pose at 64 px with the collision rectangle drawn over it.
- Shape: rectangle about 14×44 px, from the feet to the chin, centered on the body.
- Outside the shape: hat, twin tails and staff. Only the body can be hurt. This is fair to the player because hair and hat are the parts that swing furthest in the run and jump poses; a hit on a hair tip would feel unearned.
- The rectangle does not change between poses, so the hurtbox never jumps when the animation changes.

## Palette (*PROPOSED*, to be checked against the cave background)
| Use | Hex |
|---|---|
| Hair | #E8E6F0 |
| Eyes, ribbon, staff crystal | #D62839 |
| Hat, capelet | #3A40A0 |
| Trim, ember charm | #D4A63A |
| Tunic, boots | #6B5A4E |
| Skin | #F5DCCD |

Outline #1A1420 and one shade/highlight step per color (e.g. blush #F2A0A8) are derived from these six and are not separate key colors.

Check: the hat/capelet indigo must stay at least one value step brighter than the darkest cave tone, and the hair must be the brightest shape on screen. Fireball and heal glow are warm; enemy art stays cool.

## Consistency rules (every frame is judged against these)
- Same height (64 px with hat), head-to-body ratio 1:3.5 as in the turnaround; reject any frame that drifts toward chibi proportions.
- Eye line at the same height in every standing pose; both eyes visible, same size and highlight position.
- Twin tails always reach the waist; they may swing but not change length.
- Staff length and crystal size fixed; always in the right hand.
- 1 px outline in #1A1420; no extra outline colors.
- Only palette colors above; no new hues introduced by the model.
- Hat shape and bend direction identical in every pose.

## Open
- Name, hat and outfit confirmation.
