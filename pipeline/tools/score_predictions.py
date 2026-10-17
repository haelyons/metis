"""Score the filed predictions that the Stage-2 replay can decide, from the replay's saved outputs.

Usage: python3 -I tools/score_predictions.py A.json B.json [replay/args_A.json]
  A.json, B.json  the return values of dist/replay_v2.js phase A and phase B, saved verbatim by the orchestrator
  args_A.json     written by tools/prepare_replay_args.py (default: replay/args_A.json beside tools/)
Prints one markdown table: prediction id | measure | filed threshold | observed | PASS/FAIL/UNDECIDABLE.
PASS means the filed prediction holds. FAIL means it does not; "fails-if triggered" in the observed column says
whether the report's own failure condition (which decides the follow-up action) is also met.
Pick numbers are the table.md order (cost.md and novelty-structure.md use the same numbering):
 1 R1 W2, 2 R1 W15, 3 R1 I1, 4 R1 I6, 5 R2 W3, 6 R2 W13, 7 R2 opt-10, 8 R2 opt-12, 9 R3 W7, 10 R3 W11,
 11 R3 O6, 12 R3 O7, 13 R4 B, 14 R4 F, 15 R4 O3, 16 R4 O4, 17 R5 W1, 18 R5 W5, 19 R5 I3, 20 R5 I1.
"PASS" for a pick means the phase-B dramaturg decision (gate_decision) is PASS, whatever G-plan said
("PASS before the compute halt", substrate P1).

Filed predictions, quoted from scratchpad/meta/synthesis/ (measure | prediction | fails if):

cost.md §11
 C1 "Records evaluating after at most one repair; computed planned (or with options) against the stated total" |
    "≥ 18 of 20 evaluate. ≥ 17 of 20 within 2% of the stated values below. 0 budget halts. Repairs ≤ 4." |
    "< 15 within 2%, or any budget halt". Stated values: 1 $333, 2 $893.76, 3 $599.83 with options, 4 $709,
    5 $320, 6 $557.20, 7 $433, 8 $210, 9 $878.48, 10 $684.14, 11 $543, 12 $701, 13 caps summing to $840,
    14 caps $879, 15 $816, 16 $276.08, 17 $194 nominal, 18 $834.46, 19 $437.04, 20 $320 fast.
    Here: planned (planned_with_options for pick 3) within 2% of that value.
 C2 "Scenario rows reproduced (picks 1, 4, 5, 6, 10, 11, 20)" | "≥ 80% within 3%" | "< 60%: drop scenarios to
    annotation and render the producer's figures as GUESS". Here: the producer's stated scenario figures as cost.md
    gives them (§11: pick 1 $616, pick 20 $743; §2.3: pick 5 pessimistic $511; §2.4: pick 6 $677 / $762 / $876); a
    stated figure is reproduced when some eval.scenarios[].total of that record is within 3% of it; only records that
    have scenarios count. Picks 4, 10 and 11 have no comparable stated figure in cost.md (pick 10's "$1,030 (over
    budget)" is the production line only), so they are not scored.
 C3 "Proxy anchors in picks 1, 2, 5, 6, 9, 13, 14" | "≥ 6 of 7 encoded PROXY with a non-empty `differs_in`" |
    "≥ 3 encoded CITED". Here: a pick counts when it has at least one PROXY number with non-empty differs_in;
    "encoded CITED" is approximated by "no PROXY number at all".
 C4 "Card flags" | "\"Unmeasured\" fires on pick 15 (no pilot, `est`:65) and on ≤ 3 others. Pick 18's gate fails
    at base. Pick 16's P2 margin is ≤ 1.0." | "Misses pick 15 or pick 18, or fires \"unmeasured\" on ≥ 6".
    Here: "unmeasured" = an eval.flags string matching /unmeasured|no phase measures it/i (cost.md §8.2: a load-bearing
    uncertain input with no measured_by); any eval.gates[].passes false; eval.lines in phase P2 with a margin.
 C5 "`need` extracted for picks 2, 3, 16, 18" | "≥ 3 of 4" | "< 2".
 C7 "Dramaturg cost items" | "≤ 2.6 page checks per pick; 0 picks blocked by cost items; ≤ 20% of cost items
    downgraded" | "> 35% downgraded". Here: cost items are refs num:/rate:; page checks = distinct non-Lambda URLs of
    num: items per dramaturged pick (cost.md §6 counts pages excluding Lambda); downgraded = UNSUPPORTED,
    UNREACHABLE or CONTRADICTED (cost.md §6: a failed citation shows as [g]).
 C8 "Items about N × price, arithmetic in a sentence, or $1,000" | "0 sent" | "Any: a mechanical leak; fix".
    Here: phase-B dramaturg items (planted cards excluded) whose ref is rate:, or whose own text (every string field
    but ref and url) holds N × $price, an arithmetic sentence "a op b = c", or "$1,000".
 C9 (mechanical parts) "Writer and card" | "0 typed computed numbers; 100% of placeholders resolve; re-asks ≤ 20%;
    median block ≤ 16 lines." | "a median block over 20 lines". Here: a typed computed number is a numeric token
    in the raw writer text, outside placeholders, within 0.5% of a menu value ≥ 10 other than 1000. The replay runs
    no writer re-ask, so re-asks are UNDECIDABLE. The human-reading part is not mechanical and is not scored.
 C10 "The 7 picks with non-cost derived numbers (4, 5, 7, 8, 9, 13, 17)" | "In ≥ 5, those numbers are placeholders
    over DERIVED numbers or are absent; 0 REJECTs give a derived number as a reason" | "≥ 3 still rejected on
    derived numbers". Here: a REJECT gives a derived number as a reason when a blocking item's note matches
    /deriv|arithmetic/i. The first clause needs a hand read of which numbers those are: UNDECIDABLE.
 C11 "Halts and repairs on budget" | "0 halts; the repair route is used only for stated vs computed
    self-contradiction" | "Any halt". Here: budget halt = planned > budget_usd and total_stated > budget_usd.
 C1·P1 (cost.md §11, "Overlap with sub P1") "of the 8 picks whose only blocking reasons were derived numbers
    (`est`:58: 5, 11, 12, 15, 17, 18, 19, 20), at least 6 PASS in the replay. It fails if 4 or fewer PASS".

criteria.md §11
 K1 "(1) `open` on the 69 physical options. (2) `verdict_copy.py`'s correlation between verdict code and `open` on
    the 32 coded options. (3) W11's `open`." | "≥18 of the 24 famous-field options score `open` ≤2. At most 1 of
    last run's 5 physical top picks (W2, W3, W7, B, W1) is still its branch's top. |ρ| ≤ 0.25 (old score: 0.49).
    W11 scores ≥4." | "Fewer than 12 of 24, or ρ ≥ 0.4". Here: `open` is the mean of the 3 samples rounded, as fed
    to pick_run; famous fields are novelty-structure.md:97-103; verdict codes are verdict_copy.py's regexes on the
    stored summaries (reproduces n = 32, ρ = 0.49 on the old score).
 K2 "NA count; branches whose top was decided by the seed; frontier-list size" | "0 NA. The seed decides the top in
    ≤3 of 10 branches. The frontier list has 3–12 entries across the 5 roots." | "More than 3 decided by seed ...
    More than 20 frontier entries". Here: decided by the seed = a top pick whose
    tie_note says "broken by seeded order".
 K3 "3 option-critic samples per branch" | "The 3 samples agree on the top pick in ≥7 of 10 branches. ≥80% of
    options get the same `distance` label in all 3." | "4–6 branches ... ≤3 ... `distance` below 80%".
    Here: each sample's top pick is pick_run on that sample alone.

flow.md §2.9
 P8′ "The new option critic's labels on all 69 stored physical options, against ns:97–103's 24 famous fields
    outside the root" | "ELSEWHERE on at least 20 of the 24; ELSEWHERE on at most 5 of the other 45" |
    "Below 18 of 24, or more than 8 false ELSEWHERE labels". Here: the label is the median of the 3 samples.
 P9′ "(a) cross-root pairs recovered, against cut rows 1–18 (31 pairs); (b) the 9 pairs with title Jaccard ≥ 0.4;
    (c) branch picks replaced by collisions" | "(a) at least 24 of 31; (b) 9 of 9 after at most one resample;
    (c) 4 or fewer per run" | "(a) below 18 ... (c) above 6". Here: (a) the 18 clusters as encoded in
    flow-work/replay.py `exact`; (b) Jaccard pairs = gate_dedup_jaccard violations against singleton clusters,
    minus violations against the accepted clusters; (c) inventory rows with status `collided`.
 P10′ "Extracted `compute_tested` on the 20 stored plans" | "R: \"no\" on 0–2 of 10 physical plans and on 5–8 of 10
    interp plans, I1 among them. At most 5 of the 7 C6 picks are \"no\"" | "R: 3 or more physical \"no\", or \"no\"
    on exactly the 7 C6 picks". I1 = pick 3 (R1 I1). C6 picks (cutoffs.md:144-166): 7, 8, 12, 14, 15, 16, 19.
 P24 "Replay outcomes for W2-flagged and B3-flagged picks" | "W2-flagged physical picks: 3 or more of 8 pass.
    B3-flagged picks (total ≥ 14) pass at no less than half the rate of the others." | "W2-flagged picks pass 2 or
    fewer of 8, or B3-flagged picks pass at under half the others' rate". W2-flagged (flow.md §2.1): picks 1, 2, 5,
    9, 13, 14, 17, 18. B3: old option-critic total ≥ 14.

options-and-card.md §9
 O3 "`qt-extract` on the 20 stored producer.md files" | "`prior_max_level` comparable in at least 6 of the 10
    physical plans. The script marks these within the prior: #2 W15 (1M below 4M), #5 and #17 DNS (2,048 or less,
    below 8,192). It marks #10 W11 beyond (16,384 above 150). `decides` is yes or partly for #5, #9, #13 and #17." |
    "Any of these mechanical labels wrong". Here: comparable = prior_max_level is a number;
    beyond_prior = max(compute_axis.levels) > prior_max_level when both exist.
 P2′ (mechanical parts) "Mechanical: decision numbers, check tolerances and axis levels present in each card.
    Repair rate. Number-preservation failures." | "Render 100% by construction; writer at least 80% ... Repair needed
    on at most 5 of 10 records; number-preservation failures at most 1." Here, on the 10 writer side-cell records:
    every numeric token of predictions.decision_rule and of anchor.tolerance, and the smallest and largest
    compute_axis level (the span the rendered axis line prints), appears among the numeric tokens of the card body
    (text.js txt_numbers rules; the rendered card is cut at its Judges/Halted line); repair needed = gate_cardfields
    not ok.
 O4 "`searched`" | "Share of plans with `searched = false`" | "At least 15 of 20 in both" | "This is a harness
    measurement, not a success test. If it holds in F, the human decides whether to reserve search for producers".
    Here: phase-A plans with novelty.searched false, out of 20.
 O6 (mechanical parts) "Card form (§4.1)" | "Word count including the header; sections present; check tolerance and
    decision number present" | "260–320 words on at least 90% of cards. Every required section on 100%. The tolerance
    and the decision number on 100% of rendered cards". The decision-change test is a human reading, not scored.
    Here, on phase-A cards: words as text.js txt_words counts them (tokens holding a letter or digit) in the body
    before the Judges/Halted line, header included, HTML anchor and "·" removed; required sections are Question, What
    is known, Hypothesis, If compute is the lever (or If the hypothesis holds), If not, Test, Compute axis, Check
    first, Would not show, Cost, and Judges (or Halted at); tolerance present = every numeric token of
    anchor.tolerance in the body (cards whose plan has a tolerance); decision number present = at least one numeric
    token of predictions.decision_rule in the body.

reshape and baseline (sequential-structure change, 2026-10-16; replay parts only)
 HP3 "`reshape` on the stored options, inside K3's three samples (stored options carry no `sequential`, so no floor
    applies and the judge reads the summary)" | "≤ 3 of 119 score ≥ 4, because no stored summary names a condition. The
    7 options that name a chain one answer waits on (R2 W5, R5 W3, R3 W10, R5 W15, R2 W12, R5 W14, R3 W8) average
    ≥ 1.0 above the other physical options. Copies-only options score ≤ 2: R1 W2, R2 W13, R3 W11, R4 A."
    Here: `reshape` is the rounded mean of the 3 samples, as fed to pick_run (B.new_scores).
 HP5 "Card `reshape` and `baseline` on the 20 stored plans, extracted with the new schema" | "All score `reshape` ≤ 2.
    W13 (#6) scores 1 and W11 (#10) scores 2 in at least 2 of 3 samples. `baseline` is NA on at least 18 (at most 2
    extracts treat compaction as a method)." Here: samples are B.critic entries per key (one per run of phase B;
    concatenate runs to get more); with fewer than 3 samples, min(2, n) of the n must match; plans with no critique are
    not counted; a stored plan with no restructuring record is read as method none.

substrate.md §9
 P1 "20 producer.md files → `qt-extract` → G-plan → writer → dramaturg" | "At least 18 of 20 records pass G-plan
    without a halt. Cost items block at most 2 REJECTs ... At least 8 of 20 PASS before the compute halt." |
    "PASS ≤ 5, or cost items block ≥ 4". Here: a halt counts unless its only G-plan reason is compute_tested = "no",
    the halt this prediction is stated before; a record with no plan is a halt.
 P6 "Overlap pairs on the stored roots" | "Flags R2/R5, and R1/R4." | "Misses R2/R5".
"""
import json
import os
import re
import statistics
import sys

BUDGET = 1000
EXPECTED_TOTAL = {1: 333, 2: 893.76, 3: 599.83, 4: 709, 5: 320, 6: 557.20, 7: 433, 8: 210, 9: 878.48, 10: 684.14,
                  11: 543, 12: 701, 13: 840, 14: 879, 15: 816, 16: 276.08, 17: 194, 18: 834.46, 19: 437.04, 20: 320}
FAMOUS = {'R1': ['W14', 'W15', 'W16', 'W17', 'W18'], 'R2': ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7'], 'R3': ['W7'],
          'R4': ['A', 'B', 'C', 'H', 'I'], 'R5': ['W1', 'W2', 'W3', 'W4', 'W5', 'W9']}
OLD_PHYSICAL_TOPS = ['R1:physical:W2', 'R2:physical:W3', 'R3:physical:W7', 'R4:physical:B', 'R5:physical:W1']
P, I = 'physical', 'interp'
CUT_CLUSTERS = [  # cutoffs.md rows 1-18, as encoded in flow-work/replay.py `exact` (31 cross-root pairs)
    [('R2', P, 'W3'), ('R5', P, 'W1')], [('R2', I, 'opt-10'), ('R5', I, 'I3'), ('R3', I, 'O3')],
    [('R1', P, 'W15'), ('R4', P, 'F')], [('R2', P, 'W4'), ('R3', P, 'W7'), ('R5', P, 'W2')],
    [('R2', I, 'opt-4'), ('R5', I, 'I1'), ('R4', I, 'O8'), ('R1', P, 'W3')], [('R1', I, 'I6'), ('R4', I, 'O1')],
    [('R1', I, 'I1'), ('R4', I, 'O2')], [('R1', P, 'W14'), ('R4', P, 'C')], [('R2', P, 'W5'), ('R5', P, 'W3')],
    [('R2', P, 'W6'), ('R5', P, 'W4')], [('R2', P, 'W9'), ('R5', P, 'W16')], [('R2', P, 'W10'), ('R5', P, 'W6')],
    [('R2', P, 'W12'), ('R5', P, 'W14')], [('R2', I, 'opt-11'), ('R5', I, 'I2')], [('R2', I, 'opt-5'), ('R5', I, 'I8')],
    [('R2', I, 'opt-7'), ('R5', I, 'I7'), ('R4', I, 'O7')], [('R2', I, 'opt-8'), ('R5', I, 'I6'), ('R4', I, 'O9')],
    [('R1', I, 'I12'), ('R4', I, 'O10')]]
C6_PICKS = [7, 8, 12, 14, 15, 16, 19]
W2_FLAGGED = [1, 2, 5, 9, 13, 14, 17, 18]
DERIVED_ONLY_REJECTS = [5, 11, 12, 15, 17, 18, 19, 20]
DOWNGRADED = {'UNSUPPORTED', 'UNREACHABLE', 'CONTRADICTED'}
CHAIN_NAMED = [('R2', 'W5'), ('R5', 'W3'), ('R3', 'W10'), ('R5', 'W15'), ('R2', 'W12'), ('R5', 'W14'), ('R3', 'W8')]   # HP3
COPIES_ONLY = [('R1', 'W2'), ('R2', 'W13'), ('R3', 'W11'), ('R4', 'A')]                                               # HP3
STATED_SCENARIOS = {1: [616], 5: [511], 6: [677, 762, 876], 20: [743]}   # C2, from cost.md §11, §2.3, §2.4
CARD_SECTIONS = ['**Question.**', '**What is known.**', '**Hypothesis.**', ('**If compute is the lever.**', '**If the hypothesis holds.**'),
                 '**If not.**', '**Test.**', '*Compute axis.*', '**Check first.**', '**Would not show.**', '*Cost.*', ('**Judges.**', '**Halted at')]
C8_TEXT = [r'\d\s*[×x*]\s*\$\s?\d', r'\d[\d,.]*\s*[-+×x*/−]\s*\$?\d[\d,.]*\s*=\s*\$?\d', r'\$\s?1,?000(?![,.]?\d)']   # N × $price, a op b = c, $1,000
UNMEASURED = r'unmeasured|no phase measures it'   # cost.js: "<input> is load-bearing and no phase measures it"
# text.js txt_numbers / txt_norm_number ([\p{L}\p{N}_] is \w here): "1,979" -> "1979", "20k" -> "20000", "5.0" -> "5"
NUM = re.compile(r'(?<![\w.])(?:[-\u2212])?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?(?:[kKM](?!\w))?')


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def verdict_code(summary):  # verdict_copy.py, verbatim rules
    head = summary[:160]
    if re.search(r'NOT COMPUTE-BOUND|[Cc]ompute-solved', head): return 1
    if re.search(r'[Pp]artly|Mixed|[Bb]oth|[Mm]ostly', head) and re.search(r'compute', head, re.I): return 3
    if re.search(r'compute-bound|COMPUTE-BOUND|[Cc]ompute-constrained|[Cc]ompute-heavy', head, re.I): return 5
    return None


def spearman(a, b):  # verdict_copy.py's rank and sp
    def rank(xs):
        s = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0] * len(xs); i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[s[j + 1]] == xs[s[i]]: j += 1
            for k in range(i, j + 1): r[s[k]] = (i + j) / 2
            i = j + 1
        return r
    ra, rb = rank(a), rank(b); n = len(a); ma, mb = sum(ra) / n, sum(rb) / n
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** .5
    return sum((x - ma) * (y - mb) for x, y in zip(ra, rb)) / den if den else float('nan')


def js_str(x):
    return str(int(x)) if float(x).is_integer() and abs(x) < 1e21 else repr(float(x))


def norm_number(t):
    m = re.match(r'^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)([kKM])?$', t.strip().replace(',', '').replace('\u2212', '-'))
    if not m: return t.strip()
    return js_str(float(m.group(1) + ('e6' if m.group(2) == 'M' else 'e3' if m.group(2) else '')))


def nums(s):
    return [norm_number(t) for t in NUM.findall(str(s or ''))]


def get(d, path, default=None):
    for k in path.split('.'):
        if not isinstance(d, dict) or k not in d: return default
        d = d[k]
    return d


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    A, B = load(sys.argv[1]), load(sys.argv[2])
    args = load(sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, 'replay', 'args_A.json'))
    keys = [f"{p['root']}:{p['branch']}:{p['id']}" for p in args['picks']]
    num_of = {k: i + 1 for i, k in enumerate(keys)}
    rec = {num_of[r['pick']['key']]: r for r in A['records']}
    dram = {num_of[d['key']]: d for d in B['dramaturg'] if d and d['key'] in num_of}
    passed = {n: bool(get(dram.get(n), 'decision.result') == 'PASS') for n in range(1, 21)}
    plan = {n: (rec.get(n) or {}).get('plan') for n in range(1, 21)}
    ev = {n: (rec.get(n) or {}).get('eval') for n in range(1, 21)}
    rows = []

    def row(pid, measure, threshold, observed, ok, trigger=None):
        status = 'UNDECIDABLE' if ok is None else ('PASS' if ok else 'FAIL')
        if status == 'FAIL' and trigger is not None:
            observed += f"; fails-if triggered: {'yes' if trigger else 'no'}"
        rows.append((pid, measure, threshold, observed, status))

    def full_key(root, br, short):
        for o in args['options_by_branch'][f'{root}:{br}']:
            if o['id'] == short or o['id'].startswith(short + '-'): return f"{root}:{br}:{o['id']}"
        raise KeyError((root, br, short))

    # ---- cost.md §11
    evaluating = [n for n in range(1, 21) if ev[n] and ev[n].get('ok')]
    within, misses = [], []
    for n in evaluating:
        got = ev[n].get('planned_with_options' if n == 3 else 'planned')
        (within if isinstance(got, (int, float)) and abs(got - EXPECTED_TOTAL[n]) <= 0.02 * EXPECTED_TOTAL[n] else misses).append((n, got))
    budget_halts = [n for n in range(1, 21) if ev[n] and plan[n] and (ev[n].get('planned') or 0) > BUDGET
                    and (get(plan[n], 'cost.total_stated') or 0) > BUDGET]
    expr_repairs = [n for n in range(1, 21) if any(r.get('kind') == 'expr' for r in (rec.get(n) or {}).get('repairs', []))]
    row('C1', 'records evaluating after ≤1 repair', '≥ 18 of 20', f'{len(evaluating)} of 20', len(evaluating) >= 18)
    row('C1', 'computed planned within 2% of stated total', '≥ 17 of 20 (fails if < 15)',
        f"{len(within)} of 20; off: {', '.join(f'#{n} {g:.2f} vs {EXPECTED_TOTAL[n]}' if isinstance(g, (int, float)) else f'#{n} {g}' for n, g in misses) or 'none'}",
        len(within) >= 17, len(within) < 15)
    row('C1', 'budget halts', '0', f'{len(budget_halts)} {budget_halts}', not budget_halts, bool(budget_halts))
    row('C1', 'expression repairs', '≤ 4', f'{len(expr_repairs)} {expr_repairs}', len(expr_repairs) <= 4)
    with_sc = [n for n in STATED_SCENARIOS if ev[n] and ev[n].get('scenarios')]
    stated = [(n, x) for n in with_sc for x in STATED_SCENARIOS[n]]
    hit = [(n, x) for n, x in stated if any(isinstance(s.get('total'), (int, float)) and abs(s['total'] - x) <= 0.03 * x for s in ev[n]['scenarios'])]
    share2 = len(hit) / len(stated) if stated else None
    row('C2', 'stated scenario figures reproduced within 3% (records with scenarios)', '≥ 80% (fails if < 60%)',
        f"{len(hit)} of {len(stated)} on picks {with_sc}; no scenarios in record: {[n for n in STATED_SCENARIOS if n not in with_sc]}; picks 4, 10, 11 not scored",
        None if share2 is None else share2 >= 0.8, None if share2 is None else share2 < 0.6)

    def has_proxy(n):
        return any(x.get('basis') == 'PROXY' and x.get('differs_in') for x in (plan[n] or {}).get('numbers', []))
    c3 = [1, 2, 5, 6, 9, 13, 14]
    no_proxy = [n for n in c3 if plan[n] and not any(x.get('basis') == 'PROXY' for x in plan[n].get('numbers', []))]
    c3_ok = [n for n in c3 if has_proxy(n)]
    row('C3', 'proxy anchors (picks 1,2,5,6,9,13,14) encoded PROXY with differs_in', '≥ 6 of 7 (fails if ≥ 3 CITED)',
        f'{len(c3_ok)} of 7; no PROXY at all: {no_proxy}', len(c3_ok) >= 6, len(no_proxy) >= 3)

    unmeasured = [n for n in range(1, 21) if ev[n] and any(re.search(UNMEASURED, str(f), re.I) for f in ev[n].get('flags', []))]
    others = [n for n in unmeasured if n != 15]
    row('C4', '"unmeasured" flag', 'fires on #15 and ≤ 3 others', f'fires on {unmeasured}',
        15 in unmeasured and len(others) <= 3, 15 not in unmeasured or len(unmeasured) >= 6)
    g18 = ev[18] and any(g.get('passes') is False for g in ev[18].get('gates', []))
    row('C4', "pick 18's gate fails at base", 'fails', 'no eval' if not ev[18] else ('fails' if g18 else 'passes'),
        None if not ev[18] else bool(g18), None if not ev[18] else not g18)
    m16 = [l.get('margin') for l in (ev[16] or {}).get('lines', []) if str(l.get('phase', '')).strip().upper() == 'P2'
           and isinstance(l.get('margin'), (int, float))]
    row('C4', "pick 16's P2 margin", '≤ 1.0', f'{m16}' if m16 else 'no P2 line with a margin',
        (min(m16) <= 1.0) if m16 else None)
    c5 = [n for n in [2, 3, 16, 18] if any(l.get('need') for l in get(plan[n], 'cost.lines', []) or [])]
    row('C5', '`need` extracted (picks 2,3,16,18)', '≥ 3 of 4 (fails if < 2)', f'{len(c5)} of 4 {c5}', len(c5) >= 3, len(c5) < 2)

    cost_items = lambda d: [i for i in (d.get('findings') or {}).get('items', []) if re.match(r'(num|rate):', str(i.get('ref')))]
    pages = []
    for d in dram.values():
        urls = {str(i.get('url')) for i in d.get('items', []) if str(i.get('ref', '')).startswith('num:') and i.get('url')
                and 'lambda.ai' not in str(i.get('url'))}
        pages.append(len(urls))
    blocked_cost = [n for n, d in dram.items() if get(d, 'decision.result') == 'REJECT'
                    and any(re.match(r'(num|rate):', str(b.get('ref'))) for b in get(d, 'decision.blocking', []) or [])]
    ci = [i for d in dram.values() for i in cost_items(d)]
    down = [i for i in ci if i.get('status') in DOWNGRADED]
    share = len(down) / len(ci) if ci else 0.0
    row('C7', 'page checks per pick (distinct non-Lambda URLs of num: items)', '≤ 2.6',
        f'{statistics.mean(pages):.2f} over {len(pages)} picks' if pages else 'no dramaturg items', (statistics.mean(pages) <= 2.6) if pages else None)
    row('C7', 'picks blocked by cost items', '0', f'{len(blocked_cost)} {blocked_cost}', not blocked_cost)
    row('C7', 'cost items downgraded', '≤ 20% (fails if > 35%)', f'{len(down)} of {len(ci)} ({share:.0%})', share <= 0.20, share > 0.35)
    leak = []
    for n, d in dram.items():
        for i in d.get('items', []):
            text = ' '.join(v for k, v in i.items() if isinstance(v, str) and k not in ('ref', 'url'))
            if str(i.get('ref', '')).startswith('rate:') or any(re.search(r, text) for r in C8_TEXT): leak.append(f"#{n} {i.get('ref')}")
    row('C8', 'items about N × price, arithmetic in a sentence, or $1,000 sent to the dramaturg', '0 (fails if any)',
        f"{len(leak)} {leak[:8]} over {sum(len(d.get('items', [])) for d in dram.values())} items" if dram else 'no dramaturg items',
        not leak if dram else None, bool(leak) if dram else None)

    wrecs = [r for r in A['records'] if r.get('writer_raw') is not None]
    typed, ph_total, ph_bad = [], 0, []
    for r in wrecs:
        menu = {m['id']: m.get('value') for m in r.get('menu') or []}   # values are formatted strings ("$684.14")
        raw = r['writer_raw']
        for pid in re.findall(r'\{([a-z_][a-z0-9_]*)\}', raw):
            ph_total += 1
            if pid not in menu: ph_bad.append(f"#{num_of[r['pick']['key']]} {{{pid}}}")
        vals = [float(t) for v in menu.values() for t in nums(v) if abs(float(t)) >= 10 and float(t) != BUDGET]
        for t in nums(re.sub(r'\{[a-z_][a-z0-9_]*\}', ' ', raw)):
            if any(abs(float(t) - v) <= 0.005 * abs(v) for v in vals): typed.append(f"#{num_of[r['pick']['key']]} {t}")
    row('C9', 'typed computed numbers in writer text', '0', f'{len(typed)} {typed[:8]} over {len(wrecs)} writer cards',
        not typed if wrecs else None)
    row('C9', 'placeholders resolving', '100%', f'{ph_total - len(ph_bad)} of {ph_total}; unresolved {ph_bad[:8]}',
        not ph_bad if wrecs else None)
    row('C9', 'writer re-asks', '≤ 20%', 'the replay runs no writer re-ask', None)
    blocks = [len(r['block'].splitlines()) for r in A['records'] if r.get('block')]
    med = statistics.median(blocks) if blocks else None
    row('C9', 'median cost-block lines', '≤ 16 (fails if > 20)', f'{med} over {len(blocks)} blocks', (med <= 16) if blocks else None,
        (med > 20) if blocks else None)

    c10 = [n for n in [4, 5, 7, 8, 9, 13, 17] if get(dram.get(n), 'decision.result') == 'REJECT'
           and any(re.search(r'deriv|arithmetic', str(b.get('note', '')), re.I) for b in get(dram.get(n), 'decision.blocking', []) or [])]
    row('C10', 'derived numbers placeholders or absent (picks 4,5,7,8,9,13,17)', '≥ 5 of 7', 'needs a hand read of which numbers', None)
    row('C10', 'REJECTs giving a derived number as a reason (same picks)', '0 (fails if ≥ 3)', f'{len(c10)} {c10}', not c10, len(c10) >= 3)
    row('C11', 'halts on budget', '0; repair only for stated vs computed', f'{len(budget_halts)} halts; expression repairs on {expr_repairs}',
        not budget_halts, bool(budget_halts))
    cp = [n for n in DERIVED_ONLY_REJECTS if passed[n]]
    row('C1·P1', 'PASS among picks 5,11,12,15,17,18,19,20', '≥ 6 of 8 (fails if ≤ 4)', f'{len(cp)} of 8 {cp}', len(cp) >= 6, len(cp) <= 4)

    # ---- criteria.md §11
    new = {o['key']: o for b in B['new_scores'].values() for o in b}
    famous = [f'{r}:physical:{i}' for r, ids in FAMOUS.items() for i in ids]
    phys = [k for k in new if ':physical:' in k]
    fam_low = [k for k in famous if get(new.get(k), 'scores.open', 9) <= 2]
    row('K1', '`open` ≤ 2 on the 24 famous-field options', '≥ 18 of 24 (fails if < 12)', f'{len(fam_low)} of {len(famous)}',
        len(fam_low) >= 18, len(fam_low) < 12)
    tops = {p['key'] for p in B['pick_run']['picks'] if p['kind'] == 'top'}
    still = [k for k in OLD_PHYSICAL_TOPS if k in tops]
    row('K1', 'old physical top picks still top', '≤ 1 of 5', f'{len(still)} {still}', len(still) <= 1)
    xs, ys = [], []
    for k in phys:
        root, _, oid = k.split(':', 2)
        summ = next(o['summary'] for o in args['options_by_branch'][f'{root}:physical'] if o['id'] == oid)
        c = verdict_code(summ)
        if c is not None and isinstance(get(new[k], 'scores.open'), (int, float)):
            xs.append(c); ys.append(new[k]['scores']['open'])
    rho = spearman(xs, ys) if len(xs) > 2 else float('nan')
    row('K1', '|ρ| verdict code vs `open` (coded physical options)', '≤ 0.25 (fails if ρ ≥ 0.4)', f'ρ = {rho:.2f} on {len(xs)}',
        None if rho != rho else abs(rho) <= 0.25, None if rho != rho else rho >= 0.4)
    w11 = get(new.get('R3:physical:W11'), 'scores.open')
    row('K1', "W11's `open`", '≥ 4', str(w11), None if w11 is None else w11 >= 4)

    raw_vals = [s.get('value') for samples in B['option_critic'].values() for smp in samples if smp
                for it in smp.get('items', []) for s in it.get('scores', [])]
    na = [v for v in raw_vals if not (isinstance(v, int) and 1 <= v <= 5)]
    row('K2', 'NA (non 1..5) values in option-critic samples', '0', f'{len(na)} of {len(raw_vals)}', not na)
    seeded = [p['key'] for p in B['pick_run']['picks'] if p['kind'] == 'top' and 'seeded order' in (p.get('tie_note') or '')]
    row('K2', 'branches whose top was decided by the seed', '≤ 3 of 10', f'{len(seeded)} {seeded}', len(seeded) <= 3)
    fr = len(B['pick_run'].get('frontier', []))
    row('K2', 'frontier-list entries', '3–12 (fails if > 20)', str(fr), 3 <= fr <= 12, fr > 20)

    runs = B.get('pick_run_by_sample') or []
    agree, comparable = 0, 0
    for bk in B['option_critic']:
        root, br = bk.split(':')
        t = [next((p['key'] for p in (r or {}).get('picks', []) if p['kind'] == 'top' and p['root'] == root and p['branch'] == br), None)
             for r in runs]
        if len(t) == 3 and all(t):
            comparable += 1
            agree += len(set(t)) == 1
    row('K3', 'branches where the 3 samples agree on the top pick', '≥ 7 of 10 (4–6: mean of 2; ≤ 3: seeded top)',
        f'{agree} of {comparable} with 3 samples', agree >= 7 if comparable else None)
    same, total = 0, 0
    for bk, samples in B['option_critic'].items():
        if len(samples) != 3 or not all(samples): continue
        lab = [{it['id']: it.get('distance') for it in s.get('items', [])} for s in samples]
        for oid in lab[0]:
            total += 1
            same += lab[0][oid] == lab[1].get(oid) == lab[2].get(oid)
    row('K3', 'options with the same `distance` in all 3 samples', '≥ 80%', f'{same} of {total} ({same / total:.0%})' if total else 'none',
        (same / total >= 0.8) if total else None)

    # ---- flow.md §2.9
    fam_else = [k for k in famous if get(new.get(k), 'distance') == 'ELSEWHERE']
    other_else = [k for k in phys if k not in famous and new[k].get('distance') == 'ELSEWHERE']
    row("P8′", 'ELSEWHERE on the 24 famous-field options', '≥ 20 of 24 (fails if < 18)', f'{len(fam_else)} of {len(famous)}',
        len(fam_else) >= 20, len(fam_else) < 18)
    row("P8′", 'ELSEWHERE on the other 45 physical options', '≤ 5 (fails if > 8)', f'{len(other_else)} of {len(phys) - len(famous)} {other_else}',
        len(other_else) <= 5, len(other_else) > 8)
    cluster_of = {m: i for i, c in enumerate(B['dedup'].get('clusters') or []) for m in c.get('members', [])}
    pairs = []
    for c in CUT_CLUSTERS:
        ks = [full_key(*t) for t in c]
        pairs += [(a, b) for i, a in enumerate(ks) for b in ks[i + 1:] if a.split(':')[0] != b.split(':')[0]]
    rec_pairs = [p for p in pairs if p[0] in cluster_of and cluster_of[p[0]] == cluster_of.get(p[1])]
    row("P9′(a)", 'cut rows 1–18 cross-root pairs sharing a cluster', '≥ 24 of 31 (fails if < 18)', f'{len(rec_pairs)} of {len(pairs)}',
        len(rec_pairs) >= 24, len(rec_pairs) < 18)
    jn, jv = B['dedup'].get('jaccard_pairs_n'), B['dedup'].get('jaccard_violations_n')
    row("P9′(b)", 'title-Jaccard ≥ 0.4 cross-root pairs merged, ≤ 1 resample', '9 of 9',
        f"{jn - jv} of {jn} after {len(B['dedup'].get('samples', [])) - 1} resample(s)" if jn is not None and jv is not None else 'not recorded',
        (jv == 0) if jv is not None else None)
    coll = [r['key'] for r in B['pick_run'].get('inventory', []) if r.get('status') == 'collided']
    row("P9′(c)", 'branch picks replaced by collisions', '≤ 4 (fails if > 6)', f'{len(coll)} {coll}', len(coll) <= 4, len(coll) > 6)

    ct = {n: get(plan[n], 'compute_tested') for n in range(1, 21)}
    phys_n = [n for n in range(1, 21) if args['picks'][n - 1]['branch'] == 'physical']
    interp_n = [n for n in range(1, 21) if args['picks'][n - 1]['branch'] == 'interp']
    pno, ino = [n for n in phys_n if ct[n] == 'no'], [n for n in interp_n if ct[n] == 'no']
    allno = sorted(pno + ino)
    row("P10′", '`compute_tested` "no", physical plans', '0–2 of 10 (fails if ≥ 3)', f'{len(pno)} {pno}', len(pno) <= 2, len(pno) >= 3)
    row("P10′", '`compute_tested` "no", interp plans, I1 (#3) among them', '5–8 of 10, #3 included', f'{len(ino)} {ino}',
        5 <= len(ino) <= 8 and 3 in ino)
    c6no = [n for n in C6_PICKS if ct[n] == 'no']
    row("P10′", '"no" among the 7 C6 picks', '≤ 5 of 7 (fails if "no" on exactly the 7)', f'{len(c6no)} {c6no}',
        len(c6no) <= 5, allno == C6_PICKS)
    w2p = [n for n in W2_FLAGGED if passed[n]]
    row('P24', 'W2-flagged physical picks passing', '≥ 3 of 8 (fails if ≤ 2)', f'{len(w2p)} of 8 {w2p}', len(w2p) >= 3, len(w2p) <= 2)
    old_total = {f"{bk}:{s['id']}": s.get('total') for bk, items in args['old_scores'].items() for s in items}
    b3 = [n for n in range(1, 21) if (old_total[keys[n - 1]] or 0) >= 14]
    rest = [n for n in range(1, 21) if n not in b3]
    rb, rr = sum(passed[n] for n in b3) / len(b3), sum(passed[n] for n in rest) / len(rest)
    row('P24', 'B3-flagged (old total ≥ 14) pass rate vs others', '≥ half the others\' rate',
        f'{rb:.2f} ({len(b3)} picks) vs {rr:.2f} ({len(rest)} picks)', rb >= rr / 2)

    # ---- options-and-card.md §9
    def bp(n):
        lv, pm = get(plan[n], 'compute_axis.levels'), get(plan[n], 'novelty.prior_max_level')
        if not lv or not isinstance(pm, (int, float)): return None
        return max(lv) > pm
    comp = [n for n in phys_n if isinstance(get(plan[n], 'novelty.prior_max_level'), (int, float))]
    row('O3', '`prior_max_level` comparable, physical plans', '≥ 6 of 10', f'{len(comp)} of 10 {comp}', len(comp) >= 6)
    marks = {2: False, 5: False, 17: False, 10: True}
    wrong = [f'#{n}={bp(n)}' for n, want in marks.items() if bp(n) is not want]
    row('O3', 'beyond_prior: #2, #5, #17 within; #10 beyond', 'all 4 right', 'all right' if not wrong else f'wrong: {wrong}', not wrong)
    dec = {n: get(plan[n], 'novelty.decides') for n in [5, 9, 13, 17]}
    wrongd = [f'#{n}={d}' for n, d in dec.items() if d not in ('yes', 'partly')]
    row('O3', '`decides` yes or partly: #5, #9, #13, #17', 'all 4', 'all 4' if not wrongd else f'wrong: {wrongd}', not wrongd)

    def carries(text, pl):
        # the rendered card's body only: the appendix after Judges/Halted repeats plan numbers in the cost block
        have = set(nums(re.split(r'\n\n\*\*(?:Judges|Halted at)', text or '')[0]))
        lv = [x for x in get(pl, 'compute_axis.levels', []) or [] if isinstance(x, (int, float))]
        need = nums(get(pl, 'predictions.decision_rule')) + nums(get(pl, 'anchor.tolerance')) + ([js_str(min(lv)), js_str(max(lv))] if lv else [])
        return all(t in have for t in need)
    ten = [r for r in wrecs if r.get('plan')]
    rc = sum(carries(r.get('card') or '', r['plan']) for r in ten)
    wc = sum(carries(r.get('writer_text') or '', r['plan']) for r in ten)
    row("P2′", 'decision numbers, tolerances, axis levels present: render', '100%', f'{rc} of {len(ten)}', rc == len(ten) if ten else None)
    row("P2′", 'decision numbers, tolerances, axis levels present: writer', '≥ 80%', f'{wc} of {len(ten)}', wc >= 0.8 * len(ten) if ten else None)
    rep = [num_of[r['pick']['key']] for r in ten if r.get('cardfields') and not r['cardfields'].get('ok')]
    row("P2′", 'card-field repair needed (10 side-cell records)', '≤ 5 of 10', f'{len(rep)} {rep}', len(rep) <= 5 if ten else None)
    npf = sum(len(r.get('np_failures') or []) for r in ten)
    row("P2′", 'number-preservation failures (same records)', '≤ 1', str(npf), npf <= 1 if ten else None)

    plans = [plan[n] for n in range(1, 21) if plan[n]]
    nosearch = [n for n in range(1, 21) if plan[n] and get(plan[n], 'novelty.searched') is False]
    row('O4', 'plans with `searched` false', '≥ 15 of 20', f'{len(nosearch)} of 20 ({len(plans)} plans)', len(nosearch) >= 15)

    def words(text):
        return sum(1 for w in re.sub(r'<[^>]*>|·', ' ', text).split() if any(ch.isalnum() for ch in w))
    cards = [(num_of[r['pick']['key']], r['card'], r.get('plan') or {}) for r in A['records'] if r.get('card')]
    bodies = [(n, re.split(r'\n\n\*\*(?:Judges|Halted at)', c)[0], c, p) for n, c, p in cards]
    in_range = [n for n, b, _, _ in bodies if 260 <= words(b) <= 320]
    row('O6', 'card words incl. header, 260–320', '≥ 90% of cards',
        f"{len(in_range)} of {len(bodies)}; out: {[f'#{n} {words(b)}' for n, b, _, _ in bodies if n not in in_range][:10]}",
        len(in_range) >= 0.9 * len(bodies) if bodies else None)
    missing = [f"#{n} {lab if isinstance(lab, str) else lab[0]}" for n, _, c, _ in bodies for lab in CARD_SECTIONS
               if not any(x in c for x in ((lab,) if isinstance(lab, str) else lab))]
    row('O6', 'required sections present', '100% of cards', f"{len(bodies) - len({m.split()[0] for m in missing})} of {len(bodies)}; missing {missing[:8]}",
        not missing if bodies else None)
    tol = [(n, b, p) for n, b, _, p in bodies if get(p, 'anchor.tolerance')]
    tol_miss = [f'#{n}' for n, b, p in tol if not all(t in set(nums(b)) for t in nums(get(p, 'anchor.tolerance')))]
    dec_miss = [f'#{n}' for n, b, _, p in bodies if not set(nums(get(p, 'predictions.decision_rule'))) & set(nums(b))]
    row('O6', 'check tolerance present (cards with a tolerance)', '100%', f'{len(tol) - len(tol_miss)} of {len(tol)}; missing {tol_miss}',
        not tol_miss if tol else None)
    row('O6', 'a decision number present (from decision_rule)', '100%', f'{len(bodies) - len(dec_miss)} of {len(bodies)}; missing {dec_miss}',
        not dec_miss if bodies else None)

    # ---- reshape and baseline (replay parts of HP3, HP5)
    rs = {k: get(o, 'scores.reshape') for k, o in new.items() if isinstance(get(o, 'scores.reshape'), (int, float))}
    high = sorted(k for k, v in rs.items() if v >= 4)
    row('HP3', '`reshape` ≥ 4 among the stored options', '≤ 3 of 119', f'{len(high)} of {len(rs)} {high[:8]}', len(high) <= 3 if rs else None)
    chain = [full_key(r, P, i) for r, i in CHAIN_NAMED]
    cv = [rs[k] for k in chain if k in rs]
    ov = [v for k, v in rs.items() if ':physical:' in k and k not in chain]
    gap = statistics.mean(cv) - statistics.mean(ov) if cv and ov else None
    row('HP3', 'mean `reshape`, the 7 chain-naming options minus the other physical options', '≥ 1.0',
        f'{statistics.mean(cv):.2f} ({len(cv)}) − {statistics.mean(ov):.2f} ({len(ov)}) = {gap:.2f}' if gap is not None else 'no scores',
        gap >= 1.0 if gap is not None else None)
    copies = {f'{r} {i}': rs.get(full_key(r, P, i)) for r, i in COPIES_ONLY}
    row('HP3', '`reshape` on copies-only options R1 W2, R2 W13, R3 W11, R4 A', 'each ≤ 2', str(copies),
        all(v <= 2 for v in copies.values()) if all(v is not None for v in copies.values()) else None)

    samples = {}
    for c in B.get('critic') or []:
        if c and c.get('key') in num_of and c.get('critique'): samples.setdefault(num_of[c['key']], []).append(c['critique'])

    def score(crit, name):
        return next((x.get('value') for x in crit.get('scores', []) if x.get('criterion') == name), None)
    first = {n: cs[0] for n, cs in samples.items()}
    card_rs = {n: score(c, 'reshape') for n, c in first.items() if score(c, 'reshape') is not None}
    over2 = sorted(n for n, v in card_rs.items() if not (isinstance(v, (int, float)) and v <= 2))
    row('HP5', 'card `reshape` ≤ 2 on the stored plans (first sample)', 'all',
        f'{len(card_rs) - len(over2)} of {len(card_rs)}; not: {[f"#{n}={card_rs[n]}" for n in over2]}; no reshape score: {sorted(set(first) - set(card_rs))}',
        not over2 if card_rs else None)
    for n, want in ((6, 1), (10, 2)):
        got = [score(c, 'reshape') for c in samples.get(n, [])][:3]
        need = min(2, len(got))
        row('HP5', f'#{n} ({keys[n - 1]}) card `reshape` = {want}', '≥ 2 of 3 samples', f'{sum(v == want for v in got)} of {len(got)}: {got}',
            sum(v == want for v in got) >= need if got else None)
    na = [n for n, c in first.items() if score(c, 'baseline') == 'NA']
    nob = [n for n, c in first.items() if score(c, 'baseline') is None]
    row('HP5', 'card `baseline` NA on the stored plans (first sample)', '≥ 18',
        f'{len(na)} of {len(first)}; scored: {sorted(set(first) - set(na) - set(nob))}; no baseline score: {nob}', len(na) >= 18 if first else None)

    # ---- substrate.md §9
    halted = {n: (rec.get(n) or {}).get('halted') for n in range(1, 21)}
    compute_only = [n for n in range(1, 21) if halted[n] and halted[n].get('gate') == 'G-plan'
                    and all(str(x).startswith('compute_tested is no') for x in halted[n].get('reasons', []))]
    no_halt = [n for n in range(1, 21) if rec.get(n) and (not halted[n] or n in compute_only)]
    row('P1', 'records passing G-plan without a halt (before the compute halt)', '≥ 18 of 20',
        f'{len(no_halt)} of 20; compute_tested-only halts not counted: {compute_only}', len(no_halt) >= 18)
    npass = sum(passed.values())
    row('P1', 'PASS before the compute halt', '≥ 8 of 20 (fails if ≤ 5)', f'{npass} {[n for n in passed if passed[n]]}', npass >= 8, npass <= 5)
    row('P1', 'REJECTs blocked by cost items', '≤ 2 (fails if ≥ 4)', f'{len(blocked_cost)} {blocked_cost}', len(blocked_cost) <= 2, len(blocked_cost) >= 4)
    flagged = {frozenset((p.get('a'), p.get('b'))) for p in get(B, 'overlap.raw.pairs', []) or []}
    hit = [x for x in (('R2', 'R5'), ('R1', 'R4')) if frozenset(x) in flagged]
    row('P6', 'overlap pairs on the stored roots', 'flags R2/R5 and R1/R4 (fails if misses R2/R5)',
        f"flagged {sorted('/'.join(sorted(f)) for f in flagged)}", None if not get(B, 'overlap.raw') else len(hit) == 2,
        frozenset(('R2', 'R5')) not in flagged)

    esc = lambda s: str(s).replace('|', '\\|')
    print('| prediction | measure | filed threshold | observed | result |')
    print('|---|---|---|---|---|')
    for r in rows:
        print('| ' + ' | '.join(esc(c) for c in r) + ' |')


if __name__ == '__main__':
    main()
