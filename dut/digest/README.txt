digest: one finished run into a directory a scientist can read in ten minutes and check
=======================================================================================

WHAT THIS IS
------------
A run of the repository's pipelines leaves tens of thousands of files, and nobody can say afterwards what it
found. digest reads one finished m5 or latent_skeptic run and writes <run>/digest/: ten standing questions
answered and checked sentence by sentence against the cited files, a write-up built from what the check
supported, a marimo notebook, and a copy of every file cited. It reads a run and nothing else.

  pipeline.js      the wf.js script: four model calls (and one repair); wf_config.json: Codex primary,
                   Claude then OpenCode as understudies, Cursor disabled
  questions.md     the ten standing questions, asked of every run
  prompts/         reader.md, verify.md, writer.md, notebook.md, repair.md; the script fills {{placeholders}}
  check.py         the mechanical checks (stdlib); writes CHECK.json; runs the sandboxed export
  tests/           test_check.py; planted.json, planted_check.py; dry_run.sh, stub_runner.js, stub/m2/

THE FOUR CALLS
--------------
Questions produce the working, verification checks the working, trimming produces the write-up.
1. reader: ls-general, strong tier, working directory the run root. Claim-blind: it gets the run root, the
   standing questions and layout hints for m5 and latent_skeptic runs. It may read one hop outside the run: a
   file the run's RUN.md names by path, or ../BRIEF.md, ../QUESTION.md. It returns a neutral answer per
   question (at most 120 words, every number cited), citations [{path, supports}] and draft enums.
2. verify: qt-bare, strong tier, text only. Its prompt holds the answers, each followed by its cited
   sentences with ids (S1..), then the draft enums, then every cited file (a fair share of file_bytes each,
   default 200000; a cut file says so). It returns per sentence {question, sentence, verdict: supported |
   contradicted | not_addressed, quote, path, reason} and the final enums.
3. writer: qt-bare, strong tier, text only. It gets the answers with every sentence marked by its verdict,
   and the enums; it returns the five sections, built from supported sentences only.
4. notebook: ls-general, main tier, working directory the digest; gets DIGEST.md, QA.md, digest.json,
   MANIFEST.json, may read evidence/, returns {source}. If the export fails, notebook-repair gets the source
   and the export's output and returns a corrected source, once.
Tiers (pipeline.js STRONG = opus, MAIN = sonnet, which wf.js maps to tiers): strong is codex/default@high,
then claude/opus, then the OpenCode main model; main is codex/default@medium, then claude/sonnet, then OpenCode.
The models return JSON only; the script writes every file. wf.js passes a non-OpenCode family the Claude tool
list of the call's role, and codex_cli.js picks its sandbox from it: workspace-write with network if the list
holds Write, Edit or Bash, read-only otherwise. wf_config.json sets ls-general to "Read,Glob,Grep" and qt-bare's
list is empty, so every call here is read-only. Schemas list questions and sentences as required keys, so
wf.js's validator and repair turn demand exactly one entry each; verify's path must be one of the files shown.

OUTPUT: <run>/digest/
---------------------
  DIGEST.md      ## Question, ## Answer, ## Problem and constraints, ## Method and assumptions, ## Analysis
  QA.md          per question: the answer, its sources, "Checked: N sentences supported, M contradicted, K not
                 addressed", then each contradicted or not addressed sentence with the verify quote and path
  VERIFY.json    the per-sentence list and its summary
  digest.json    exactly headline_kind, baseline_kind, equivalence, prediction_hit, evidence, anchor
  digest.py      marimo notebook; DIGEST_DIR at the top (empty: its own directory); reads only evidence/
  digest.html    its export
  evidence/      each cited file at its path under the run root; a one-hop file at evidence/_source/<basename>
  MANIFEST.json  per file {original, copied, sha256, bytes, supports}; commit; models; run root
  CHECK.json     every check, pass or fail, with detail. DIGEST.md and QA.md cite (evidence/...) only
  RUN.md         status, command, commit, wall time, spend, and per call: primary, who answered, tokens, time
  wf/            the wf.js record: run.json, journal.jsonl, agents/NNNN-<label>/ with every prompt and reply

THE SCRIPT
----------
It refuses a digest directory holding anything but wf/, or a wf/ with an earlier journal, unless args.force;
force deletes the old outputs and moves the old journal and agents/ to wf/prev-<stamp>/. After the reader it
resolves every cited path; the run fails on one that does not exist, is not a file, is absolute, is hidden or
credential-like, is over max_evidence_mb (default 20), lies in the digest, or lies outside the run without
being the one hop. A citation is a parenthesis holding only a path token with a file extension, or with a
slash naming something that exists. The script copies the files, rewrites cited paths to evidence/, writes
the outputs, runs check.py, and writes RUN.md on every exit path. A failed check leaves every file in place.

CHECKS (check.py <digest dir>)
------------------------------
Words are counted with citations removed; sentences split as gate_scope.py splits them.
  headings          the five ## headings in order, and no other ## heading
  digest_words      500 to 700 words in DIGEST.md
  qa_answer_words   each answer in QA.md at most 150 words (the lines the script adds under it not counted)
  sentences         DIGEST.md: mean 14 to 26 words, none over 45, no list lines, no heading below ##
  numbers_cited     a DIGEST.md or QA.md sentence with a digit outside its citations carries an (evidence/...)
                    citation (the Checked: tally excepted); every cited path exists
  digest_numbers_verified  each DIGEST.md number (digits with decimal points, commas dropped) is in a
                    sentence VERIFY.json marks supported
  no_outside_paths  no ../, ~/ or absolute path in DIGEST.md or QA.md
  gate_density      latent_skeptic's gate_density.py on DIGEST.md prose, citations removed (<= 10 codes/1000)
  gate_scope        latent_skeptic's gate_scope.py, imported, with one marker added to MARKERS as its docstring
                    invites a host project to do: an (evidence/...) citation scopes a number
  enums             digest.json has exactly the six keys, each an allowed value
  quotes_verbatim   each QA.md Quote line and each supported or contradicted VERIFY.json quote is non-empty and
                    occurs in its file (whitespace, * and ` ignored)
  manifest          sha256 and bytes match each copy; no file under evidence/ is unlisted
  notebook_imports  stdlib and marimo only; never subprocess, socket, urllib, http, shutil, ctypes, dynamic
  notebook_paths    no string in digest.py with a .. component or an absolute path
  notebook_export   $MARIMO export html digest.py -o digest.html -f exits 0 inside bwrap ($BWRAP): / read-only,
                    the digest read-write, fresh /dev /proc /tmp, --unshare-net, --die-with-parent. It works on
                    this box; if bwrap refuses, the export runs bare and detail.sandbox says so
The gates are read from ../latent_skeptic/compositions/gates (DIGEST_GATES overrides); missing gates fail.

RUN
---
From the repository root; the args file may live anywhere but the digest, and wf/run.json keeps a copy:
  echo '{"run_root": "experiments/reshape-test/20261020-0855-measure"}' > /tmp/digest-m2.json
  MARIMO=/home/hal/dev/interp/janus/.venv-gpu/bin/marimo node dut/pipeline/idea/wf.js \
    --config dut/digest/wf_config.json --script dut/digest/pipeline.js --args /tmp/digest-m2.json \
    --out experiments/reshape-test/20261020-0855-measure/digest/wf --mode fallback --on-refusal halt
args: run_root; out (default <run_root>/digest; --out must be <out>/wf); force; max_evidence_mb; file_bytes
(a refused run still replaces an earlier digest's wf/run.json and wf/status.json: wf.js writes them first).

TESTS
-----
  MARIMO=... python3 -I dut/digest/tests/test_check.py    a synthetic digest passes; one bad variant per
      rule fails exactly that check; a refusing bwrap falls back and says so
  bash dut/digest/tests/dry_run.sh <out dir> [run root]
      no model calls: WF_STUB=tests/stub_runner.js serves the replies in tests/stub/m2/ (one planted wrong
      sentence, one planted unsupported one); real evidence copy from m2, real check.py and export; then
      refusal, force, repair, and runs or checks that must fail
  python3 -I dut/digest/tests/planted_check.py <digest dir> [planted.json]
      m2 must give prediction_hit partly and a QA paragraph with the CPU library figure (416.7 ms or 19.1x);
      m1 must give anchor page_value_only. Re-check a finished digest: python3 -I dut/digest/check.py <dir>
The stub replies are written by hand from the m2 files. A pass on them tests the machinery, not the models.

WHAT IT DOES NOT DO
-------------------
It does not run workloads, contact boxes, fetch the network, edit the run, or run git beyond wf.js's own
rev-parse and status, and it does not judge a method beyond what the files show.
