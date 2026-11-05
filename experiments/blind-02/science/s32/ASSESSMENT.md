# s32 assessment: repair of s31's main comparison so the agents see no number that matches a sealed one (2026-11-05)

**Scope.** Offline: no network, no box, no git, no credentials. I wrote only into `science/s32/`.

**What I read:**
- s31: `ASSESSMENT.md`, `main_design.json`, `_section.md`, `MAIN_BRIEF.md` (via `cmp`), `PREDICTIONS.md`, `predictions.json`, `NARROWING.md`, `NEXT.json`, `status.json`;
- s27 to s30 (s27, s28 and s29 for the provenance of the thread count; s30 and s27 through s31's summaries);
- `dut/pipeline/m5/SCHEMAS.md:115-203` (Sealed comparison, U57/U58), in particular `:121` (placeholders in `env`), `:143` (what the view copies), `:174` (the arm part's substitution);
- MEGADOCK's option parser at the pinned commit, as fetched by blind-02 m5 run7: `m5/run7/agent/results/reproduce/out/a0-smoke/baseline-published/megadock/src/parameter.cpp:115-139` and `control.cpp:33-43`. run7's `agent/results/evaluate/comparison/versions.json` records commit `9575280c…`.

**Tool limits.** Shell use was denied for Python, `cat` redirection and `cp`; `cmp`, `diff` and `wc` were allowed. So I wrote every file with the file tool and checked it with `cmp`, `diff` and ripgrep (`Grep -o`). `check_matches.py` in this folder implements the operator's rule, but it was **not executed**, because Python was denied. The self-check in §C is a full enumeration of tokens with ripgrep, using the same regular expression.

## A. What matched in s31, and why

**Sealed values** (from s31's `main_design.json`, comparisons K1–K10):
- margins: 0.001 (K8, K3), 0.01 and 0.0023 (K2), 0.012 (K6, K7);
- K4's confidence 0.95 and threshold 1.05;
- the twelve reference values of K5, K9 and K10: 17.330, 16.152, 25.509, 25.413; 23.107, 21.536, 34.012, 33.883; 40.536, 35.934, 48.888, 48.676.

Read with "every number (at any depth)" meaning JSON numbers, these are all the sealed values. If the digit runs inside the `reference.source` strings also count, add 0.75, 1–7, −2, −3, 56, −59, 100 and 421.

Enumerating every visible numeric token of s31 (§C method) against these values, I find the following matching pairs:

| # | visible token | where in s31 | sealed value (kind) | usable sealed number or coincidence |
|---|---|---|---|---|
| 1 | `1.0` | arms' commands, `-e 1.0 -d 1.0 -b 1.0` (×3 arms) | 0.95 (K4 confidence), at distance exactly 0.05 | coincidence: MEGADOCK scoring weights carried since run6 (`s27:44`) |
| 2 | `1.0` | same | 1.05 (K4 threshold), at distance exactly 0.05 | coincidence, same |
| 3 | `26` | arms' `env` `OMP_NUM_THREADS` (×3); also hash `ee2fc49ec38f26a2…` | 25.509 (K5 reference, 1dv1) | coincidence: the thread count since run6 (`s27:44`; `s28:174`, "26 threads") |
| 4 | `25` | 6f0e source hash `…1a4c25d16…` (1aua receptor/ligand spec) | 25.413 (K5 reference, 1nr5) | coincidence: hex digest |
| 5 | `16` | 6f0e hash `…25d16aa…`; 3g8c hash `…c4b16f7…` | 16.152 (K5 reference, 1ax2) | coincidence: hex digest |
| 6 | `23` | 6f0e hash `…d1b23d31…` | 23.107 (K9 reference, 1aua) | coincidence: hex digest |
| 7 | `41` | 6f0e hash `…31a41aad…`; 1aua reference hash `…fef41a48` | 40.536 (K10 reference, 1aua) | coincidence: hex digest |
| 8 | `34` | 1ax2 prepared receptor hash `…65ab34cf…` | 34.012 (K9 reference, 1dv1) | coincidence: hex digest |
| 9 | `34` | same | 33.883 (K9 reference, 1nr5) | coincidence: hex digest |
| 10 | `49` | 1nr5 reference hash `ee2fc49ec…` | 48.888 (K10 reference, 1dv1) | coincidence: hex digest |
| 11 | `49` | same | 48.676 (K10 reference, 1nr5) | coincidence: hex digest |
| 12 | `22` | brief, "chain field (column 22)" | 21.536 (K9 reference, 1ax2) | coincidence: the PDB format's chain-ID column |
| 13* | `56` | 6f0e hash `…aa1c56a05…`; 3g8c hash `…85d56a9c…` | 56 inside the reference `source` strings ("ASSESSMENT.md:56-59") | coincidence; counts only if source-string digits are sealed |
| 14* | `1.0` | arms' commands | 1 inside the `source` strings ("tier 1", "blocks 1-3", "gpu_1x") | coincidence; counts only if source-string digits are sealed |

**Classification.** No sealed number was in view. None of the matched visible tokens derives from a margin, threshold, confidence or reference value:
- the hex digests are pinned file hashes, not quantities;
- `26`, `1.0` and `22` are a run setting, scoring weights and a file-format column, all fixed before s27 derived the rule.

So `match_cause` is `coincidental_tokens`. One of them is not an arbitrary coincidence: `26` is the thread count of run6, whose walls produced the K5/K9/K10 references. But it equals no sealed value, and nothing about the references can be recovered from it.

**Count.** Under the stated rule I reproduce 12 pairs (JSON-number reading, exact decimal arithmetic) or 14 (counting digits inside the `source` strings). Counting the source-string values once per comparison (K5, K9, K10) gives 18. I could not reproduce the operator's 19 exactly from the stated rule, and I do not know which reading produced it. §B removes every token of every reading above.

## B. Changes and why the measurement is unchanged

`diff ../s31/main_design.json main_design.json` shows changes only on design lines 7, 10, 16, 19, 25 and 28 (arms), 38–89 (input `spec`s) and 153–154 (evaluator `spec` text). Everything after the evaluator is byte-identical to s31:
- `timeout_s` 180, `replicates` 7, `warmup` 1, `order_seed` 20261103, `timeout_s` 300, `budget_s` 14400, `bootstrap_seed` 31311, `bootstrap_resamples` 10000;
- all ten comparisons with every margin, threshold, confidence, reference value and source string.

Outputs, metrics, `select` patterns, input ids, `prepared` paths, URLs, byte counts and the evaluator pins are unchanged.

1. **`-e`, `-d`, `-b` written as `1` instead of `1.0`** (all three arms). MEGADOCK parses each with `atof` (`parameter.cpp:116`, `:125`, `:138`), so `"1"` and `"1.0"` give the same double. The program echoes the parsed double, not the string (`:122`, `:132`), so even stdout is unchanged. No output or metric reads the argument vector. The argument vectors that `wrap.json` records will read `1` where run9's read `1.0`; that is a difference in the record, not in the computation.
2. **`OMP_NUM_THREADS`** is `"{spec:/omp_threads/tens}{spec:/omp_threads/ones}"`, and every input's `spec` gains `"omp_threads": {"tens": "2", "ones": "6"}`. SCHEMAS.md allows placeholders in `env` strings. A placeholder that resolves to a string is inserted as is, and every occurrence is replaced once (`:121`). The wrapper substitutes before running the arm part (`:174`). So every arm command runs with `OMP_NUM_THREADS=26`, exactly as in s31.
   - The value is the same for all inputs. Placeholders resolve only from the input's `spec`, which is why it is repeated there.
   - The adapters do not read it.
   - I chose this over removing the variable. Unsetting it would make the thread count depend on the box's CPU count, which would change the measurement off a 26-CPU box.
3. **SHA-256 digests in the input `spec`s are arrays of hex strings.** The digest is their concatenation in order, as stated in each spec's `sha256_form` and in the brief. Five digests are split where a digit run matched:
   - 6f0e source (1aua receptor and ligand): 6 pieces;
   - 1aua reference: 2 pieces;
   - 1ax2 prepared receptor: 2 pieces;
   - 3g8c source (1dv1 receptor): 3 pieces;
   - 1nr5 reference: 3 pieces.

   The other fifteen digest values are one-element arrays, so the form is uniform.

   Checks:
   - each concatenation equals s31's digest (ripgrep matched all five whole digests in s31's design, and all five piece arrays verbatim in mine);
   - the fourteen single-piece digests occur verbatim in s31's design.

   The pins, and so the files that setup, `fetch_private.sh` and `evaluate.sh` accept, are unchanged. The brief tells each script to compare against the concatenation. The source and reference digests also stand whole in the materials section of the brief, which the intake agent reads.

   **Residual risk:** a harness script that compares against the array rather than the concatenation fails its check, and setup or the private fetch stops. That is a failed run, not a changed measurement.
4. **Evaluator `spec` text** (`private_data`, `reads`) now says the SHA-256 is the concatenation of the pieces. These are wording changes only.
5. **Brief.**
   - The new section is headed `## Comparison request (science step s32)`.
   - "chain field (column 22)" now reads "the one-character chain identifier field of the PDB format (chainID)", which is the same field.
   - Two bullets were added that explain the SHA-256 array form and the thread-count placeholder.
   - The `fetch_private.sh`, `evaluate.sh` and setup bullets say "the concatenated digest".
   - Every other sentence is s31's.

   **Byte check:**
   - `MAIN_BRIEF.md` bytes 1–39,538 equal `m5/b01_materials/BRIEF_run1.md` (cmp: identical to that file's EOF);
   - its first 1,714 bytes equal `m5/BRIEF.md` (cmp; the seed is 1,714 bytes);
   - the rest equals `_section.md` (`cmp -i 39538:0`): 39,538 + 11,614 = 51,152 bytes.

Nothing sealed moved into view, and no sealed number changed. The design is kept only in this folder.

**Predictions.** `PREDICTIONS.md` and `predictions.json` are s31's: the same run, so the same 20 items and probabilities. `cmp` confirms `predictions.json` is identical. `PREDICTIONS.md` differs only by one added line saying so. Its "§B2" reference means s31's `ASSESSMENT.md`.

## C. Self-check with the stated rule: 0 matches

**Method.** I ran ripgrep `-o` with the rule's expression `-?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?` over:
- `_section.md`, which is byte-identical to the brief after the seed and materials; its heading carries only `32`;
- `main_design.json` lines 1–154: arms, inputs, outputs, metrics and the evaluator's `what`/`spec`. That includes keys outside the screened fields, so it is a superset.

I compared every token against all sealed values of both readings in §A.

**Integer tokens.** With d = 0 and |token| > 10, a token matches only if it lies within 0.5 of a sealed value. The values in range are 16, 17, 22, 23, 25, 26, 34, 36, 41 and 49, plus 56, 100, 421 and −59 under the source-string reading. None occurs:
- the nearest tokens are 21, 24, 35 and 48, each more than 0.5 from every sealed value;
- exponent tokens (`46e1`, `9e17`, `36e84`, `72e23`, `03535815e26`, …) evaluate to 460 or to values of order 10^17 and above, none near a sealed value;
- small integers (|token| ≤ 10, d = 0) are not screened.

**Decimal tokens.** The only ones are `1.2` and `-45.0` in the design, and `12.8`, `8.6`, `9.0` and `8.0` in the brief. Each is more than 0.05 from every sealed value, including 0.75 and the integers 1–7 of the source-string reading.

**Result:** 0 matching pairs. It holds under both readings and with exact or binary-float arithmetic. No token sits within a rounding unit of a boundary, so no ambiguity remains.

**Residual risk** if the operator's tokenizer departs from the stated expression on exponent forms (it splits `9e17` into `9` and `17`): `17`, `23`, `26` and `36` would appear inside a few unsplit digests and the MEGADOCK commit. Under the stated rule they are single tokens, `9e17` and so on, and do not match.

## Next

`NEXT.json`: run the main comparison, `m5` with `MAIN_BRIEF.md` and `main_design.json`, no extra flags. Cost and time are as s31 projected (`science/s31/ASSESSMENT.md`), because nothing that determines them changed.
