| prediction | measure | filed threshold | observed | result |
|---|---|---|---|---|
| C1 | records evaluating after ≤1 repair | ≥ 18 of 20 | 9 of 20 | FAIL |
| C1 | computed planned within 2% of stated total | ≥ 17 of 20 (fails if < 15) | 4 of 20; off: #1 301.00 vs 333, #2 999.10 vs 893.76, #7 394.60 vs 433, #9 1000.00 vs 878.48, #16 612.70 vs 276.08; fails-if triggered: yes | FAIL |
| C1 | budget halts | 0 | 0 [] | PASS |
| C1 | expression repairs | ≤ 4 | 9 [5, 6, 8, 11, 12, 13, 14, 17, 18] | FAIL |
| C2 | stated scenario figures reproduced within 3% (records with scenarios) | ≥ 80% (fails if < 60%) | 2 of 6 on picks [1, 5, 6, 20]; no scenarios in record: []; picks 4, 10, 11 not scored; fails-if triggered: yes | FAIL |
| C3 | proxy anchors (picks 1,2,5,6,9,13,14) encoded PROXY with differs_in | ≥ 6 of 7 (fails if ≥ 3 CITED) | 7 of 7; no PROXY at all: [] | PASS |
| C4 | "unmeasured" flag | fires on #15 and ≤ 3 others | fires on [1, 2, 3, 5, 6, 7, 8, 9, 11, 12, 13, 15, 16, 17, 18, 19, 20]; fails-if triggered: yes | FAIL |
| C4 | pick 18's gate fails at base | fails | passes; fails-if triggered: yes | FAIL |
| C4 | pick 16's P2 margin | ≤ 1.0 | no P2 line with a margin | UNDECIDABLE |
| C5 | `need` extracted (picks 2,3,16,18) | ≥ 3 of 4 (fails if < 2) | 1 of 4 [2]; fails-if triggered: yes | FAIL |
| C7 | page checks per pick (distinct non-Lambda URLs of num: items) | ≤ 2.6 | 0.25 over 20 picks | PASS |
| C7 | picks blocked by cost items | 0 | 0 [] | PASS |
| C7 | cost items downgraded | ≤ 20% (fails if > 35%) | 0 of 8 (0%) | PASS |
| C8 | items about N × price, arithmetic in a sentence, or $1,000 sent to the dramaturg | 0 (fails if any) | 6 ['#2 card:test_summary', '#13 card:question', '#13 card:hypothesis', '#14 card:test_summary', '#14 card:anchor', '#18 card:question'] over 235 items; fails-if triggered: yes | FAIL |
| C9 | typed computed numbers in writer text | 0 | 3 ['#1 256', '#6 10', '#6 10'] over 10 writer cards | FAIL |
| C9 | placeholders resolving | 100% | 57 of 57; unresolved [] | PASS |
| C9 | writer re-asks | ≤ 20% | the replay runs no writer re-ask | UNDECIDABLE |
| C9 | median cost-block lines | ≤ 16 (fails if > 20) | 28.0 over 20 blocks; fails-if triggered: yes | FAIL |
| C10 | derived numbers placeholders or absent (picks 4,5,7,8,9,13,17) | ≥ 5 of 7 | needs a hand read of which numbers | UNDECIDABLE |
| C10 | REJECTs giving a derived number as a reason (same picks) | 0 (fails if ≥ 3) | 0 [] | PASS |
| C11 | halts on budget | 0; repair only for stated vs computed | 0 halts; expression repairs on [5, 6, 8, 11, 12, 13, 14, 17, 18] | PASS |
| C1·P1 | PASS among picks 5,11,12,15,17,18,19,20 | ≥ 6 of 8 (fails if ≤ 4) | 6 of 8 [5, 11, 15, 18, 19, 20] | PASS |
| K1 | `open` ≤ 2 on the 24 famous-field options | ≥ 18 of 24 (fails if < 12) | 22 of 24 | PASS |
| K1 | old physical top picks still top | ≤ 1 of 5 | 0 [] | PASS |
| K1 | \|ρ\| verdict code vs `open` (coded physical options) | ≤ 0.25 (fails if ρ ≥ 0.4) | ρ = -0.10 on 32 | PASS |
| K1 | W11's `open` | ≥ 4 | 3 | FAIL |
| K2 | NA (non 1..5) values in option-critic samples | 0 | 0 of 1221 | PASS |
| K2 | branches whose top was decided by the seed | ≤ 3 of 10 | 2 ['R2:interp:opt-10-physics-extraction', 'R3:physical:W11'] | PASS |
| K2 | frontier-list entries | 3–12 (fails if > 20) | 10 | PASS |
| K3 | branches where the 3 samples agree on the top pick | ≥ 7 of 10 (4–6: mean of 2; ≤ 3: seeded top) | 4 of 10 with 3 samples | FAIL |
| K3 | options with the same `distance` in all 3 samples | ≥ 80% | 102 of 119 (86%) | PASS |
| P8′ | ELSEWHERE on the 24 famous-field options | ≥ 20 of 24 (fails if < 18) | 24 of 24 | PASS |
| P8′ | ELSEWHERE on the other 45 physical options | ≤ 5 (fails if > 8) | 8 of 45 ['R1:physical:W13', 'R3:physical:W4', 'R3:physical:W5', 'R3:physical:W6', 'R3:physical:W8', 'R4:physical:D', 'R4:physical:E', 'R5:physical:W10']; fails-if triggered: no | FAIL |
| P9′(a) | cut rows 1–18 cross-root pairs sharing a cluster | ≥ 24 of 31 (fails if < 18) | 0 of 31; fails-if triggered: yes | FAIL |
| P9′(b) | title-Jaccard ≥ 0.4 cross-root pairs merged, ≤ 1 resample | 9 of 9 | 0 of 9 after 1 resample(s) | FAIL |
| P9′(c) | branch picks replaced by collisions | ≤ 4 (fails if > 6) | 0 [] | PASS |
| P10′ | `compute_tested` "no", physical plans | 0–2 of 10 (fails if ≥ 3) | 0 [] | PASS |
| P10′ | `compute_tested` "no", interp plans, I1 (#3) among them | 5–8 of 10, #3 included | 6 [3, 4, 7, 15, 16, 19] | PASS |
| P10′ | "no" among the 7 C6 picks | ≤ 5 of 7 (fails if "no" on exactly the 7) | 4 [7, 15, 16, 19] | PASS |
| P24 | W2-flagged physical picks passing | ≥ 3 of 8 (fails if ≤ 2) | 7 of 8 [1, 2, 5, 9, 13, 14, 18] | PASS |
| P24 | B3-flagged (old total ≥ 14) pass rate vs others | ≥ half the others' rate | 0.92 (12 picks) vs 0.75 (8 picks) | PASS |
| O3 | `prior_max_level` comparable, physical plans | ≥ 6 of 10 | 7 of 10 [1, 2, 5, 6, 10, 14, 17] | PASS |
| O3 | beyond_prior: #2, #5, #17 within; #10 beyond | all 4 right | all right | PASS |
| O3 | `decides` yes or partly: #5, #9, #13, #17 | all 4 | wrong: ['#13=no'] | FAIL |
| P2′ | decision numbers, tolerances, axis levels present: render | 100% | 4 of 10 | FAIL |
| P2′ | decision numbers, tolerances, axis levels present: writer | ≥ 80% | 0 of 10 | FAIL |
| P2′ | card-field repair needed (10 side-cell records) | ≤ 5 of 10 | 10 [1, 3, 4, 5, 6, 11, 13, 18, 19, 20] | FAIL |
| P2′ | number-preservation failures (same records) | ≤ 1 | 2 | FAIL |
| O4 | plans with `searched` false | ≥ 15 of 20 | 14 of 20 (20 plans) | FAIL |
| O6 | card words incl. header, 260–320 | ≥ 90% of cards | 1 of 20; out: ['#1 382', '#2 400', '#3 365', '#4 328', '#5 408', '#6 381', '#7 348', '#8 359', '#9 407', '#10 432'] | FAIL |
| O6 | required sections present | 100% of cards | 20 of 20; missing [] | PASS |
| O6 | check tolerance present (cards with a tolerance) | 100% | 20 of 20; missing [] | PASS |
| O6 | a decision number present (from decision_rule) | 100% | 17 of 20; missing ['#1', '#11', '#14'] | FAIL |
| HP3 | `reshape` ≥ 4 among the stored options | ≤ 3 of 119 | 0 of 119 [] | PASS |
| HP3 | mean `reshape`, the 7 chain-naming options minus the other physical options | ≥ 1.0 | 1.71 (7) − 1.15 (62) = 0.57 | FAIL |
| HP3 | `reshape` on copies-only options R1 W2, R2 W13, R3 W11, R4 A | each ≤ 2 | {'R1 W2': 1, 'R2 W13': 1, 'R3 W11': 2, 'R4 A': 1} | PASS |
| HP5 | card `reshape` ≤ 2 on the stored plans (first sample) | all | 20 of 20; not: []; no reshape score: [] | PASS |
| HP5 | #6 (R2:physical:W13) card `reshape` = 1 | ≥ 2 of 3 samples | 1 of 1: [1] | PASS |
| HP5 | #10 (R3:physical:W11) card `reshape` = 2 | ≥ 2 of 3 samples | 0 of 1: [1] | FAIL |
| HP5 | card `baseline` NA on the stored plans (first sample) | ≥ 18 | 16 of 20; scored: [2, 5, 10, 13]; no baseline score: [] | FAIL |
| P1 | records passing G-plan without a halt (before the compute halt) | ≥ 18 of 20 | 8 of 20; compute_tested-only halts not counted: [3, 7, 16] | FAIL |
| P1 | PASS before the compute halt | ≥ 8 of 20 (fails if ≤ 5) | 17 [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 18, 19, 20] | PASS |
| P1 | REJECTs blocked by cost items | ≤ 2 (fails if ≥ 4) | 0 [] | PASS |
| P6 | overlap pairs on the stored roots | flags R2/R5 and R1/R4 (fails if misses R2/R5) | flagged ['R2/R5']; fails-if triggered: no | FAIL |
