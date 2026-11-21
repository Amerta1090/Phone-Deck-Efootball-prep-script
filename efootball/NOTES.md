# eFootball prep — layout & strategy notes

## Usage
1. Phone connected over USB debugging, eFootball open on the Division dashboard.
2. Press **To Match** yourself.
3. Run `python3 ~/phone-deck/efootball/efootball_prep.py`
   — it waits for matchmaking, skips the stadium screen, reads the opponent,
   sets all four Individual Instructions and stops on the pre-match Game Plan (~90 s).
4. Check, then press **To Match** yourself. The script never starts a match.

Needs `tesseract-data-eng`. OCR was tuned on real screenshots: card positions and
ratings 30/30, opponent formation/playstyle/strength 4/4.

Device: vivo V2157, landscape 2408x1080. All coordinates below are in a
**1280-wide screenshot frame** (multiply by 2408/1280 = 1.881 for real taps).

**Input quirk:** the game ignores `adb shell input tap`. Use a short press:
`input swipe X Y X Y 120`. Drag-and-drop works with `input draganddrop x1 y1 x2 y2 1200`.

**Match screen:** capturable (it is NOT secure); first seconds are black while loading.
Scoreboard probe: physical pixel (240,30) is yellow (~230,230,0) while the match HUD shows.

## Screen map

### Division dashboard
| Element | Coord |
|---|---|
| Game Plan | 312,124 |
| Match History | 312,270 |
| Advice | 312,417 |
| Back | 225,522 |
| To Match | 1055,522 |

### Game Plan (pitch screen)
| Element | Coord |
|---|---|
| Button 1: Manager menu | 165,110 |
| Button 2: Team (club crest) | 165,218 |
| Button 3: Substitutes panel (left drawer) | 165,325 |
| Button 4: Reserves list (Filter 130,31 / Sort 637,31) | 165,435 |
| Move/position edit (✓ to confirm, same spot) | 499,515 |
| Condition arrows toggle | 780,515 |
| Back / To Match | 225,522 / 1055,522 |

Pre-match Game Plan (after To Match) shows the same pitch, but button 4 is a gear:
gear 165,435 → [X close 165,435 | Match Settings 272,435 | Opponent team 380,435].
Opponent team view has "Switch ATK/DEF" at 1113,342.

### Manager menu (popup, close X at 1104,43)
Division Game Plan has **Change Manager**; pre-match does not, so rows shift:

| Item | Division | Pre-match |
|---|---|---|
| Manager Details | 777,118 | 777,118 |
| Change Manager | 780,189 | — |
| Set Formation | 763,260 | 763,189 |
| Team Playstyle | 770,332 | 770,260 |
| Link-up Play | 757,404 | 757,332 |
| Individual Instructions | 808,475 | 808,404 |

### Individual Instructions
Cards: Attack1 340,260 · Attack2 640,260 · Defence1 937,260 · Defence2 1180,260
(Defence2 is half off-screen; after swiping left the cards shift one slot).
- Attack options: Off 600,150 · Defensive 600,211 · Anchoring 600,271
- Defence options: Off 600,150 · Tight Marking 600,211 · Man Marking 600,271 · Counter Target 600,331
- Player picker grid: columns x=666,783,900,1017; rows y=186,300,420. Done/Next 1034,90 (Next 1022,90).
- Man Marking is two-step: our player → Next → opponent player → Done.
- **Instructions do not carry over between matches/opponents — set them every match.**

### Set Formation
Fluid Formation toggle 1067,212; Formation list 240,272:
Copy from Base Team, 4-4-2, 4-3-3, 4-3-2-1, 4-3-1-2, 4-2-3-1, 4-2-1-3, 4-1-4-1, 4-1-2-3,
3-4-3, 3-2-4-1, 3-2-3-2, 3-1-4-2, 5-3-2, 5-2-2-1, 5-2-1-2.
The Division team is a separate copy of the base team.

### Team Playstyle (popup, Done 640,508)
Possession Game 494,109 · Quick Counter 476,174 · Long Ball Counter 494,240 ·
Out Wide 450,305 · Long Ball 450,370 · Overload 449,435

### Post-match flow
Full-time stats → Next 1055,522 → summary (Stats / Player Ratings 885,270 / Highlights / Advice) → Next →
campaign screen (event) → Next → maybe "Rating increased" popup OK 640,433 → dashboard.

## Squad (Madrid Chamartin B, strength 3220)
4-2-1-3: GK Abbiati 102 · RB Cafu 102(C) · CB 103 · CB 103 · LB Zanetti 103 ·
DMF Vieira 105 · CMF Iniesta 104 · AMF 104 · SS(left) Mbappé 105 · CF Haaland 103 · RWF Lamine Yamal 108.
Bench: Suárez CF 105, Rui Costa AMF 104, Xabi Alonso CMF 103, Messi SS 104, Neymar LWF 104, Forlán CF 103 …
Notes: Rui Costa (Creative Playmaker) rated 4.5 in LBC — don't start him in Long Ball Counter.
Yamal at AMF drops to 96; keep him at RWF.

## Managers (team playstyle proficiency)
| Manager | PG | QC | LBC | OW | LB | Overload |
|---|---|---|---|---|---|---|
| **Mourinho** (current) | 62 | 82 | **90** | 67 | 75 | 59 |
| Fàbregas | **89** | 65 | 56 | 68 | 57 | 56 |
| Xabi Alonso | 72 | **88** | 35 | 51 | 28 | ? |
| Amorim | 62 | 81 | 54 | **89** | 46 | ? |
| Gattuso | 53 | 65 | 57 | **89** | 71 | ? |
| Lampard | 75 | 60 | 58 | 69 | **89** | ? |
| Flick | 76 | 72 | 61 | 75 | 44 | ? |
| Soucek | 70 | 70 | 70 | 70 | 70 | ? |
| Granero | 50 | 50 | 50 | 50 | 50 | ? |

Mourinho's Link-up Plays are unused: Shadow Link A (Deep-lying Forward CF + Classic No.10 AMF)
and 1-2 Cut-in C (Prolific Winger LWF/RWF + Deep-lying Forward CF). No eligible starters yet.

## Strategy rules (Mourinho / Long Ball Counter)
1. Keep LBC with Mourinho by default (90 proficiency).
2. Attack1 = Anchoring → DMF (protect against counters).
3. Attack2 = Defensive → LB (keep three at the back while attacking).
4. Defence1 = Counter Target → fastest forward (Mbappé).
5. Defence2 = Man Marking → DMF on the opponent's main creator:
   priority SS/AMF with the highest rating, else their highest-rated CF.
6. If the opponent's attack shape has ≤3 defenders (e.g. 3-2-5), LBC is ideal — no change.
7. Half-time: if shots on target are fine and opponent has ≤2 on target, change nothing.

## Results log
| # | Opponent | Their style | Shape ATK/DEF | Score | Notes |
|---|---|---|---|---|---|
| 1 | Dijon FCO 3186 (Mourinho) | Long Ball Counter | 4-3-1-2 / 5-2-1-2 | 1-1 | 4-2-2-2, Rui Costa 4.5, Mbappé 7.5 MOTM; their GK 5 saves |
| 2 | Man United 3127 (Lampard) | Long Ball | 3-2-5 / 4-2-3-1 | **2-0 W** | 4-2-1-3 with Haaland+Yamal; interceptions 14-7, they had 1 shot on target |
| 3 | FC Barcelona 3167 | Long Ball Counter | 4-3-1-2 / 4-3-1-2 | 1-0 at 87' (final not checked) | Marked De Bruyne (AMF 102) |
| 4 | Persib 3168 (Mourinho) | Long Ball Counter | 4-3-3 | — | First fully scripted prep; marked Messi (SS 104) |
