digest: one finished run into a directory a scientist can read in ten minutes and check
=======================================================================================

WHAT THIS IS
------------
One run of the repository's pipelines leaves tens of thousands of files, and nobody can say afterwards what
it found. digest reads one completed run (an m5 run or a latent_skeptic run) and writes <run>/digest/: five
short sections, the standing questions answered, the owner's beliefs judged against quoted evidence, a marimo
notebook, and a copy of every file cited. It reads a run. It never runs workloads, contacts a box or fetches
the network.

  pipeline.js      the wf.js script: three model calls, everything else deterministic
  wf_config.json   Codex primary, OpenCode understudy; Claude and Cursor disabled
  questions.md     the standing questions, asked of every run
  prompts/         reader.md, verdict.md, notebook.md; the script fills {{placeholders}}
  check.py         the mechanical checks (stdlib); writes CHECK.json
  tests/           test_check.py; planted.json, planted_check.py; dry_run.sh, stub_runner.js, stub/m2/

THE THREE CALLS
---------------
1. reader: role ls-general, opus tier, working directory the run root. Claim-blind: it gets the run root, the
   standing questions and layout hints for m5 and latent_skeptic runs, never the owner's beliefs. It may read
   one hop outside the run: a file the run's RUN.md names by path, or ../BRIEF.md, ../QUESTION.md. It returns
   one neutral observation per standing question, then question, answer, constraints, method, analysis
   (500 to 700 words together), citations [{path, supports}] and draft enums.
2. verdict: role qt-bare, opus tier. Its prompt holds the reader's observations and draft enums, then the
   cited files (a fair share of verdict_bytes each, default 200000; a cut file says so), then the owner's
   beliefs and questions, in that order. It returns per belief {belief, verdict: supported | contradicted |
   not_addressed, quote, path, reason}, an answer per owner question, and the final enums.
3. notebook: role ls-general, sonnet tier, working directory the digest. It gets DIGEST.md, QA.md, digest.json
   and MANIFEST.json, may read evidence/, and returns {source} for digest.py.
The models return JSON only; the script writes every file. wf.js passes a non-OpenCode family the Claude tool
list of the call's role, and codex_cli.js picks its sandbox from it: workspace-write (with network) if the list
holds Write, Edit or Bash, read-only otherwise. wf_config.json sets ls-general to "Read,Glob,Grep" and qt-bare's
list is empty, so every Codex call here is read-only. Schemas list questions and beliefs as required keys (Q1..,
B1.., O1..), so wf.js's validator and repair turn demand exactly one entry each.

THE OWNER'S FILE
----------------
Optional, written before the run as <run>/digest/questions.md: a "## Beliefs" and a "## Questions" heading,
each followed by "- " items. Without it the verdict call still runs on the observations and the files, and
sets the final enums.

OUTPUT: <run>/digest/
---------------------
  DIGEST.md      ## Question, ## Answer, ## Problem and constraints, ## Method and assumptions, ## Analysis
  QA.md          standing questions and the reader's answers; owner questions; owner beliefs, each with
                 verdict, quote and path
  digest.json    exactly headline_kind, baseline_kind, equivalence, prediction_hit, evidence, anchor
  digest.py      marimo notebook; DIGEST_DIR at the top (empty: its own directory); reads only evidence/
  digest.html    its export
  evidence/      each cited file at its path under the run root; a one-hop file at evidence/_source/<basename>
  MANIFEST.json  per file {original, copied, sha256, bytes, supports}; commit; models; run root; whether
                 the reader's raw record names the owner file (reader_read_owner_file)
  CHECK.json     every check, pass or fail, with detail
  RUN.md         status, command, pipeline commit, models, wall time, spend (wf/status.json), check result
  wf/            the wf.js record: run.json, journal.jsonl, agents/NNNN-<label>/ with every prompt and reply
DIGEST.md and QA.md cite (evidence/...) only, so the directory stands on its own.

THE SCRIPT
----------
It refuses a digest directory holding anything but questions.md and wf/, or a wf/ with an earlier journal,
unless args.force; force deletes the old outputs and moves the old journal and agents/ to wf/prev-<stamp>/.
After the reader returns it resolves every cited path, and the run fails on one that does not exist, is not a
file, is absolute, is hidden or credential-like, is over max_evidence_mb (default 20), lies in the digest, or
lies outside the run without being the one hop. A citation is a parenthesis holding only a path-like token, or
an entry in citations. The script copies the files, rewrites cited paths in the prose to evidence/, writes the
outputs, runs check.py, and writes RUN.md on every exit path. A failed check leaves every file in place.

CHECKS (check.py <digest dir>)
------------------------------
Words are counted with citations removed; sentences split as gate_scope.py splits them.
  headings          the five ## headings in order, and no other ## heading
  digest_words      500 to 700 words in DIGEST.md
  qa_answer_words   each ### block of QA.md at most 150 words
  sentences         DIGEST.md: mean 14 to 26 words, none over 45, no list lines, no heading below ##
  numbers_cited     a sentence of DIGEST.md or QA.md with a digit outside its citations carries an
                    (evidence/...) citation, and every cited path exists in the digest
  no_outside_paths  no ../, ~/ or absolute path in DIGEST.md or QA.md
  gate_density      latent_skeptic's gate_density.py on DIGEST.md prose, citations removed (<= 10 codes/1000)
  gate_scope        latent_skeptic's gate_scope.py, imported, with one marker added to MARKERS as its docstring
                    invites a host project to do: an (evidence/...) citation scopes a number
  enums             digest.json has exactly the six keys, each an allowed value
  quotes_verbatim   each Quote line of QA.md occurs in its cited file, whitespace normalised
  manifest          sha256 and bytes match each copy; no file under evidence/ is unlisted
  notebook_imports  stdlib and marimo only; never subprocess, socket, urllib, http, shutil, ctypes, dynamic
  notebook_paths    no string in digest.py with a .. component or an absolute path
  notebook_export   $MARIMO export html digest.py -o digest.html -f exits 0 (-f so a re-check overwrites)
The gates are read from ../latent_skeptic/compositions/gates (DIGEST_GATES overrides); missing gates fail.

RUN
---
From the repository root; the args file may live anywhere, and wf/run.json keeps a copy:
  echo '{"run_root": "experiments/reshape-test/20261020-0855-measure"}' > /tmp/digest-m2.json
  MARIMO=/home/hal/dev/interp/janus/.venv-gpu/bin/marimo node dut/pipeline/idea/wf.js \
    --config dut/digest/wf_config.json --script dut/digest/pipeline.js --args /tmp/digest-m2.json \
    --out experiments/reshape-test/20261020-0855-measure/digest/wf --mode fallback --on-refusal halt
args: run_root; out (default <run_root>/digest; --out must be <out>/wf); force; max_evidence_mb;
verdict_bytes. wf.js writes wf/run.json and wf/status.json before the script can refuse, so a refused run
replaces those two files of an earlier digest; everything else is left alone.
Re-check a finished digest: MARIMO=... python3 -I dut/digest/check.py <digest dir>

TESTS
-----
  MARIMO=... python3 -I dut/digest/tests/test_check.py    a synthetic digest passes every check, and one
      bad variant per rule fails exactly that check
  bash dut/digest/tests/dry_run.sh <out dir> [run root]
      no model calls: WF_STUB=tests/stub_runner.js serves the replies in tests/stub/m2/; real evidence copy
      from m2, real check.py and export; then refusal, force, no owner file, and runs that must fail
  python3 -I dut/digest/tests/planted_check.py <digest dir> [planted.json]
      m2 must give prediction_hit partly and a QA paragraph with the CPU library figure (416.7 ms or 19.1x);
      m1 must give anchor page_value_only
The stub replies are written by hand from the m2 files. A pass on them tests the machinery, not the reader.

WHAT IT DOES NOT DO
-------------------
It does not run workloads, contact boxes, fetch the network, edit the run, or run git beyond wf.js's own
rev-parse and status. It does not judge a method beyond what the files show. The export runs the notebook a
model wrote, after the static checks pass or fail; run it where that is acceptable.
