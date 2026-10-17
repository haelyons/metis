# question-tree v2 prompts

Generated from `src/prompts.js` (prompt version qt2-2, 2026-10-16); the code is the source of truth. Placeholders the script fills are in [brackets]. Role (`agentType`) and model per call are as `CONTRACT.md` §3 sets them; "session" means the session model.

How the user's prompts were treated (INTEGRATED §4, CONTRACT §0):
- Verbatim, with a suffix appended: PLAYWRIGHT and GUEST (re-ask sentence on S1b only), FRAMER, WIDENER, DEEPENER, INTERP, PRODUCER.
- The PRODUCER's verbatim text loses exactly the words "one machine, up to 8 GPUs, " and the colon before them (budget-only constraint); nothing else in it changes.
- Edited in body: OPTION CRITIC (and its criteria strings), CRITIC (and its criteria strings), DRAMATURG, WRITER (side cell only).
- New: OVERLAP, DEDUP, PRICE_SHEET, EXTRACT, REPAIR_EXPR, REPAIR_FIELDS.
- No generator prompt says which field values halt a pick or move a score (H1). No em-dashes.

## Part 1. The user's prompts

### PLAYWRIGHT

`P_PLAYWRIGHT(EX1, EX2)` · role qt-bare, session model · verbatim, unchanged

**Original (verbatim, CONTEXT.md):**

```text
Here are two questions someone asked. [EX1] [EX2] Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].
```

**Final:**

```text
Here are two questions someone asked. "What limits the development of better crystal foundation models like for battery generation, is it a major blocker at some level, at could that be fixed with a shit ton of GPU parallelism?" "Can scientific paper reviews (maybe specifically ML, DL, data-driven papers) be automated with highly scoped, small subagents following the AISLE model: many open-source models, since they have different blind spots, with tasks scoped to known failure modes like biases, factual reproduction errors, 'do these authors/papers exist' errors and overclaims, including building the suggested experiments and variations and running them on GPUs? Is compute a major blocker at some level, could a shit ton of GPU parallelism fix it?" Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].
```

**Diff and notes:**

- EX1 and EX2 are the original script's texts (`EX1_TEXT`, `EX2_TEXT`), quoted as the original script quoted them. The function output equals the original script's prompt byte for byte.

### GUEST

`P_GUEST(EX1, EX2)` · role qt-bare, session model · verbatim, unchanged

**Original (verbatim, CONTEXT.md):**

```text
You are Harry James Potter-Evans-Verres from Harry Potter and the Methods of Rationality. You test everything, look for exploits in how the world works, and light up when brute force becomes possible. Here are two questions someone asked. [EX1] [EX2] Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].
```

**Final:**

```text
You are Harry James Potter-Evans-Verres from Harry Potter and the Methods of Rationality. You test everything, look for exploits in how the world works, and light up when brute force becomes possible. Here are two questions someone asked. "What limits the development of better crystal foundation models like for battery generation, is it a major blocker at some level, at could that be fixed with a shit ton of GPU parallelism?" "Can scientific paper reviews (maybe specifically ML, DL, data-driven papers) be automated with highly scoped, small subagents following the AISLE model: many open-source models, since they have different blind spots, with tasks scoped to known failure modes like biases, factual reproduction errors, 'do these authors/papers exist' errors and overclaims, including building the suggested experiments and variations and running them on GPUs? Is compute a major blocker at some level, could a shit ton of GPU parallelism fix it?" Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].
```

### Re-ask suffix (S1b only)

`P_REASK(roots)` · no role of its own: appended after a space to PLAYWRIGHT or GUEST · new suffix (substrate §10)

**Final:**

```text
Also make them orthogonal to these: "[kept root 1]" "[kept root 2]" "[kept root 3]".
```

**Diff and notes:**

- Each kept root is quoted, in the style of [EX1] [EX2]. Accepts `[{id, question}]` (what main passes) or `[question]`.

### FRAMER

`P_FRAMER(question, path)` · role qt-research, session model · verbatim + suffix

**Original (verbatim, CONTEXT.md):**

```text
[question] Don't answer until you've defined and thought about the problem as thoroughly as possible without answering. Start by relaying your current understanding, making some predictions, and then proceed. Cite a URL for every factual claim. Write everything to [path]. End with one line, VERDICT: COMPUTE-BOUND or VERDICT: NOT COMPUTE-BOUND, and return JSON: {verdict}.
```

**Final:**

```text
[question] Don't answer until you've defined and thought about the problem as thoroughly as possible without answering. Start by relaying your current understanding, making some predictions, and then proceed. Cite a URL for every factual claim. Write everything to [path]. End with one line, VERDICT: COMPUTE-BOUND or VERDICT: NOT COMPUTE-BOUND, and return JSON: {verdict}. Also return compute_signals: up to three parts of the problem where more parallel compute might change the answer, each as {subproblem, what_compute_buys}, or an empty list.
```

**Diff and notes:**

- Suffix (substrate §10, verbatim): the compute_signals sentence.

### WIDENER

`P_WIDENER(framerPath, path)` · role qt-research, session model · verbatim + suffix

**Original (verbatim, CONTEXT.md):**

```text
Read [framer path]. What sorts of related problems are compute constrained? Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].
```

**Final:**

```text
Read [framer path]. What sorts of related problems are compute constrained? Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}]. Count a related problem as compute constrained when it is still open whether more parallel compute would change its answer, not only when compute is already known to bind there. List both kinds, and mark the second kind settled in compute_open. Also count a problem whose answer takes long because its steps run one after another, even where more hardware would not change the answer, only how soon it arrives. For each option also return root_link: one sentence on which part of the question in [framer path] it bears on, or "none". Return compute_open: one sentence naming the quantity more parallel compute would buy for it (samples, ensemble members, resolution, model runs, model size, search width or seeds), the largest amount of it that any source you cite reports, with that source's URL, and what is still unknown about its effect on the answer above that amount; or "settled:" followed by what is known and its source URL; or "none". Return sequential: the part of the work that one answer waits on step after step (what each step waits for, and roughly how many steps one run takes), how many independent runs the answer needs, and how much of one GPU a single run keeps busy; then whether those steps must run in order, and if not, what change to the computation would let them run at the same time, what would have to be true of the system for that change to pay off, and the nearest source that has tried it, with its URL; or "none:" followed by why the work already splits into independent pieces. Return up to three source URLs. Use the option's heading label in your file as its id.
```

**Diff and notes:**

- Suffix: the two WIDENER-only definition sentences (options-and-card §2.2, then the sequential-structure change; each reinterprets "compute constrained", consent given 2026-10-16), then the shared branch suffix.
- Shared branch suffix: options-and-card §2.2 text, with "model size" added to the quantity list and the URL of the reporting source asked for ("with that source's URL", "its source URL"), so it matches CONTRACT §2.2 `compute_open`; then the `sequential` sentence (CONTRACT §2.2), before "Return up to three source URLs."

### DEEPENER

`P_DEEPENER(framerPath, path)` · role qt-research, session model · verbatim + suffix

**Original (verbatim, CONTEXT.md):**

```text
Read [framer path]. Go deeper on that: where does the compute go, and what would massive parallelism change? List the concrete options it opens up. Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].
```

**Final:**

```text
Read [framer path]. Go deeper on that: where does the compute go, and what would massive parallelism change? List the concrete options it opens up. Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}]. For each option also return root_link: one sentence on which part of the question in [framer path] it bears on, or "none". Return compute_open: one sentence naming the quantity more parallel compute would buy for it (samples, ensemble members, resolution, model runs, model size, search width or seeds), the largest amount of it that any source you cite reports, with that source's URL, and what is still unknown about its effect on the answer above that amount; or "settled:" followed by what is known and its source URL; or "none". Return sequential: the part of the work that one answer waits on step after step (what each step waits for, and roughly how many steps one run takes), how many independent runs the answer needs, and how much of one GPU a single run keeps busy; then whether those steps must run in order, and if not, what change to the computation would let them run at the same time, what would have to be true of the system for that change to pay off, and the nearest source that has tried it, with its URL; or "none:" followed by why the work already splits into independent pieces. Return up to three source URLs. Use the option's heading label in your file as its id.
```

**Diff and notes:**

- Suffix: the shared branch suffix only (its own question already asks what massive parallelism would change).

### INTERP

`P_INTERP(framerPath, path)` · role qt-research, session model · verbatim + suffix

**Original (verbatim, CONTEXT.md):**

```text
Read [framer path]. Are there mech interp (Goodfire style?) solutions to these sorts of problems? Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].
```

**Final:**

```text
Read [framer path]. Are there mech interp (Goodfire style?) solutions to these sorts of problems? Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}]. For an interpretability option the quantity may be models, layers, features, prompts or seeds analysed; write none in compute_open if more of it would not change the answer. For each option also return root_link: one sentence on which part of the question in [framer path] it bears on, or "none". Return compute_open: one sentence naming the quantity more parallel compute would buy for it (samples, ensemble members, resolution, model runs, model size, search width or seeds), the largest amount of it that any source you cite reports, with that source's URL, and what is still unknown about its effect on the answer above that amount; or "settled:" followed by what is known and its source URL; or "none". Return sequential: the part of the work that one answer waits on step after step (what each step waits for, and roughly how many steps one run takes), how many independent runs the answer needs, and how much of one GPU a single run keeps busy; then whether those steps must run in order, and if not, what change to the computation would let them run at the same time, what would have to be true of the system for that change to pay off, and the nearest source that has tried it, with its URL; or "none:" followed by why the work already splits into independent pieces. Return up to three source URLs. Use the option's heading label in your file as its id.
```

**Diff and notes:**

- Suffix: the INTERP-only quantity sentence (options-and-card §2.2, verbatim), then the shared branch suffix.

### OPTION CRITIC

`P_OPTION_CRITIC(root, criteria, options)` · role qt-bare, session model · edited in body

**Original (verbatim, CONTEXT.md):**

```text
Score each option 1-5 on each criterion, or "cannot assess". Criteria: [criteria]. Options: [options]. Return JSON: [{id, scores, total}].
```

**Final:**

```text
Score each option 1-5 on each criterion. There is no NA: a field that says "none" or "none known" scores 1. Give each score a reason of at most 20 words. Score from the quantities, sources and gaps the option names; ignore verdict words such as COMPUTE-BOUND or NOT COMPUTE-BOUND. Also label each option SAME, ADJACENT or ELSEWHERE against the root question, with a reason: SAME if it asks the root question or a sub-question of it, ADJACENT if it has the root's subject but asks a different question, ELSEWHERE if its subject is different. Decide the subject from the title and summary; count root_link only if the summary itself describes the root question's object of study. Do not add up the scores. Decide only from the text below; do not use tools.
Root question: [root question]
Criteria:
[criteria]
Options, one per line:
[options: one JSON object per line with id, title, summary, root_link, compute_open, sequential]
```

**Diff and notes:**

- OPTION CRITIC: the "cannot assess" choice is replaced by "There is no NA" with the none-scores-1 rule; a reason per score; verdict words ignored; SAME/ADJACENT/ELSEWHERE label with definitions and the root_link rule; "Do not add up the scores" replaces the returned total; "Decide only from the text below; do not use tools"; the root question is given; "Return JSON: [{id, scores, total}]" removed (the schema carries the form); each option line carries id, title, summary, root_link, compute_open and sequential.
- Body text: criteria §8.1, plus the SAME/ADJACENT/ELSEWHERE definitions from substrate §5 inlined (criteria §8.1 points to them).
- Given an array, the function keeps only id, title, summary, root_link, compute_open and sequential of each option: no source_urls (options-and-card §2.2: it cannot check them), never scores or distance.

#### OPTION CRITIC criteria

`CRIT_OPTION(branch)` · names physical `stakes, open, reshape`; interp `stakes, open, internals, reshape`

**Original, physical:**

```text
scientific stakes; compute is the main limit; results checkable against a reference; not already solved by existing tools
```

**Original, interp:**

```text
scientific stakes; model weights or activations are accessible; internals could reveal what outputs can't; results checkable against known physics
```

**Final, physical:**

```text
stakes: Suppose the question this option raises were answered, either way. 5 = a choice someone faces (what to buy, build, collect or scale next) turns on the answer, and either answer would move it; 3 = the answer would refine a belief but no choice turns on it, or one answer is already much more likely than the other; 1 = either answer is already expected, or nothing would change. Do not score how famous or important the field is, or how close it is to the root question.
open: Has published work already measured how the answer changes with the quantity compute buys here (samples, ensemble members, resolution, model runs, model size, search width), across the range that $1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours) can reach? 5 = names the quantity and where published measurements stop (or that none exist), and the unmeasured range starts within that reach; 3 = the unmeasured range is reachable only through a smaller stand-in system, or published work already covers part of the reachable range; 1 = names no compute-bought quantity, or published work already covers everything within that reach, so the open range lies only beyond it.
reshape: Does the option name a part of the work that one answer waits on step after step, and a reason those steps might not have to run in order? 5 = names that chain and roughly how long it is; one answer leaves most of a GPU idle (a small state, or few runs needed, so copies side by side would not fill it); names what would have to be true of the system for the steps to be computed at the same time, in a form a cheap measurement could check; and no cited source already computes this chain in parallel for this system; 3 = names the chain and a way to restructure it, but one of these fails: the answer needs many independent runs, so copies side by side already fill the hardware; one run already fills a GPU; or no checkable condition is named; 1 = sequential says none, or the only parallelism is independent pieces (copies, a sweep, one job per GPU), or a cited source already computes this chain in parallel for this system. A method published for a different system does not lower this score. Do not score how famous the method or field is.
```

**Final, interp:**

```text
stakes: Suppose the question this option raises were answered, either way. 5 = a choice someone faces (what to buy, build, collect or scale next) turns on the answer, and either answer would move it; 3 = the answer would refine a belief but no choice turns on it, or one answer is already much more likely than the other; 1 = either answer is already expected, or nothing would change. Do not score how famous or important the field is, or how close it is to the root question.
open: Has published work already measured how the answer changes with the quantity compute buys here (models, layers, features, prompts or seeds analysed), across the range that $1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours) can reach? 5 = names the quantity and where published measurements stop (or that none exist), and the unmeasured range starts within that reach; 3 = the unmeasured range is reachable only through a smaller stand-in system, or published work already covers part of the reachable range; 1 = names no compute-bought quantity, or published work already covers everything within that reach, so the open range lies only beyond it.
internals: Does the summary name specific information the model's internals could carry that its outputs do not, and say why outputs miss it? 5 = names the information and why outputs miss it; 3 = names a general kind (features, a representation, a direction) without what it adds over outputs; 1 = names none.
reshape: Does the option name a part of the work that one answer waits on step after step, and a reason those steps might not have to run in order? 5 = names that chain and roughly how long it is; one answer leaves most of a GPU idle (a small state, or few runs needed, so copies side by side would not fill it); names what would have to be true of the system for the steps to be computed at the same time, in a form a cheap measurement could check; and no cited source already computes this chain in parallel for this system; 3 = names the chain and a way to restructure it, but one of these fails: the answer needs many independent runs, so copies side by side already fill the hardware; one run already fills a GPU; or no checkable condition is named; 1 = sequential says none, or the only parallelism is independent pieces (copies, a sweep, one job per GPU), or a cited source already computes this chain in parallel for this system. A method published for a different system does not lower this score. Do not score how famous the method or field is.
```

**Diff and notes:**

- OPTION CRITIC criteria: the four semicolon criteria become stakes and open (interp adds internals), each with 5/3/1 anchors. "compute is the main limit" and "not already solved by existing tools" become open, scored within $1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours); "results checkable against a reference", "results checkable against known physics" and "model weights or activations are accessible" are dropped; "internals could reveal what outputs can't" becomes internals. Both branches add reshape: whether the option names a step-after-step chain one answer waits on and a checkable reason it need not run in order.
- stakes and internals: criteria §8.1, verbatim.
- open: criteria §8.1 (the version for branches held to the compute-lever test; both are, CONTRACT §0). Its reach clause "across the range one machine can run? One machine means up to 8 GPUs for $1,000: about 31 hours of an 8×H100 node at $31.92 per hour, or 250 H100-hours" and "within one machine's reach" / "everything one machine can reach" are replaced by "$1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours)" and "within that reach".
- open: the quantity list is per branch: physical keeps the criteria §8.1 list; interp names models, layers, features, prompts or seeds analysed (CONTRACT §2.2).
- reshape: the sequential-structure change, verbatim, the same for both branches. It reads the option's `sequential` field; the script floors it to 1 when `sequential` starts with "none", and it is not part of the total.

### PRODUCER

`P_PRODUCER({idTitle, branchPath, path, dir, optionRecord, rootQuestion, framerPath, priceSheetText})` · role qt-producer, session model · verbatim minus the words "one machine, up to 8 GPUs, " and the colon before them + suffix

**Original (verbatim, CONTEXT.md):**

```text
Read option [id] "[title]" in [branch path]. I'm thinking about running something on this with up to $1,000 of GPU credit: one machine, up to 8 GPUs, at Lambda's on-demand prices (https://lambda.ai/pricing). Make it concrete: what to build, the baseline, how to check it's right, and the cost. Cite a URL for every factual claim. Write to [path].
```

**Final:**

```text
Read option [id] "[title]" in [branch path]. I'm thinking about running something on this with up to $1,000 of GPU credit at Lambda's on-demand prices (https://lambda.ai/pricing). Make it concrete: what to build, the baseline, how to check it's right, and the cost. Cite a URL for every factual claim. Write to [path]. Option record: [option record]. Root question: [root question]. Read only [branch path], [framer path], pages you fetch and what you write under [dir]; write only under [dir]. When the plan is written, return it as the record in your output schema; producer.md stays your working file. In the record, put every number the cost or the size of the test depends on in numbers, each with a basis: CITED (a page states this number for this same setting; give the page text that shows it), PROXY (a page states it for a different model, GPU, dataset, size or component; give the page text and say what differs), MEASURED (you ran code: save the script and its output under [dir]/pilot/ and give the output line and the machine), DERIVED (an expression over other ids), DESIGN (your choice), or GUESS (no source; say what it rests on). Give each rate as the per-GPU price and the GPU count, and each line's hours as an expression. The default line is a time box: DESIGN hours at a rate from the prices below, ended by a timer or stop rule; it needs no estimate of the work inside it, but if you have one, put it in need. Use GUESS only where a number drives the plan. For each PROXY or GUESS the cost or result depends on, name the phase that measures it in measured_by, and give that phase's threshold as gate if your plan changes on it. Optional: scenarios (pessimistic or sensitivity cases, as values for the inputs they change), optional lines for stretch work, instead_of for fallbacks, and yields (the number ids that say what the money buys: cases, samples, primes). Refer to the budget as budget_usd and to the price sheet's filesystem price as fs_usd_gib_month. List human time and money outside Lambda in outside_budget. predictions.if_lever and predictions.if_not are the outcomes you expect, on the same measured quantity, if more compute does or does not change the answer. predictions.noise_rule says how you will tell a real difference from run-to-run noise. predictions.expected is the outcome you expect, if_lever, if_not or unsure, with one sentence why. scored_against says what the measured outcome is compared with to decide it is correct. Each source carries the exact sentence from the page that you rely on. In restructuring, sequential_part is the part of this computation that one answer waits on step after step, and how many steps; method is why those steps need not run in order and how your plan computes them at the same time instead, or "none" if the plan only runs independent work side by side or splits each step across GPUs. If method is not none, also give condition, what must be true of this system for the method to pay off and the cheap measurement that checks it; condition_phase, the id of the phase that makes that measurement before the main spend; baseline_sequential, the fastest sequential implementation you will time and how it is tuned; and baseline_copies, independent copies run side by side on the same GPUs, which you will also time. Then compute_axis is the length of the chain or the number of runs the answer needs; predictions.if_lever and predictions.if_not say where on that axis, as numbers, the parallel version does or does not reach the same answer sooner than each baseline, and if_not says how you expect it to fail if it does; anchor checks the parallel result against the sequential one within a stated tolerance; test_summary names both baselines; and novelty.closest_prior is the nearest published parallel version of this computation. Write the record's card fields (question, hypothesis, predictions.if_lever, predictions.if_not, test_summary, novelty.closest_prior, novelty.left_open, anchor.what, limits, restructuring.sequential_part, restructuring.method) for a reader who has not seen your files: plain words, at most 25 words each (hypothesis and predictions.if_lever 22, anchor.what 24, novelty.closest_prior, novelty.left_open and limits 30, test_summary 45, restructuring.sequential_part 18, restructuring.method 22), no labels from your files or from the branch and framer files (write what C2 or E2 stands for, not the label), and keep every number the decision depends on. You may cite a source in any card field as [source id]. novelty.closest_prior is the published result that comes nearest to deciding between if_lever and if_not: what it measured and the largest amount of the compute quantity it used. novelty.prior_max_level is that amount in compute_axis.unit, or null if it is not on the same axis. novelty.decides says whether closest_prior already decides the outcome at your compute levels: no, partly or yes. novelty.searched says whether web search returned results while you planned. Run every local command under timeout. Start no new local run 45 minutes after you begin; if a run you need is unfinished by then, give its inputs basis GUESS with measured_by naming the phase that measures it. Local runs share a 4-core machine with other producers. Lambda's prices as read at the start of this run: [price sheet].
```

**Diff and notes:**

- PRODUCER: removed the words "one machine, up to 8 GPUs, " and the colon before them (budget-only constraint), so it reads "up to $1,000 of GPU credit at Lambda's on-demand prices (https://lambda.ai/pricing)". A seed idea, which has no branch file, reads "in the option record below" in place of the branch path.
- Seed idea (no branch file, framer or root): the first sentence reads `Read option [id] "[title]" in the option record below.`, the read list shrinks to `Read only pages you fetch and what you write under [dir]`, and the root question is `none`. Missing price sheet: `not available; read them from https://lambda.ai/pricing`.
- Suffix, in order: option record and root question (substrate §10); bounded read and record return (substrate §10, with "and what you write under [dir]" added so the producer may read its own pilot outputs); bases (cost §8.5, verbatim); cost form trimmed to the minimal-estimates decision (CONTRACT §0): time boxes are the default and need no work estimate, `need`, scenarios, optional lines, `instead_of` and yields are optional, GUESS only where a number drives the plan, every PROXY or GUESS the cost or result depends on names its measuring phase, and the price sheet's filesystem price is the GIVEN id fs_usd_gib_month, like budget_usd (CONTRACT §2.5); predictions and sources (substrate §10) with noise_rule, expected and scored_against (criteria §8.3); card fields (options-and-card §5.3) with the word caps of CONTRACT §2.5 in place of the report's "25 each (test_summary 45, limits 30)"; the hang guard (flow §2.4, as worded in the task); the price sheet (cost §8.5).
- predictions.expected is stated once (criteria §8.3 and options-and-card §5.3 both had it).
- Restructuring paragraph (the sequential-structure change, verbatim) after the sentence on sources: what `restructuring` holds, and what compute_axis, the predictions, anchor, test_summary and novelty.closest_prior hold on a restructured plan. The card-field list and caps gain restructuring.sequential_part 18 and restructuring.method 22.
- Not in the suffix: any word on which values halt, repair or score (H1).

### WRITER (side cell)

`P_WRITER(root, option, planNoCost, menu)` · role qt-bare, sonnet · edited in body

**Original (verbatim, CONTEXT.md):**

```text
Using only [producer path] and [branch path], write a 150-250 word explanation of this idea. Add no new claims. Invent no terms. Numbers are fine. Keep every sentence to 20 words or fewer. Put a source URL after every factual sentence. Write to [path].
```

**Final:**

```text
Using only the records below, write a 150-250 word explanation of this idea. Add no new claims. Invent no terms, and use no labels from the records as words (option ids like W11, phase ids like P0, criterion labels like C2): say what the thing is. Numbers are fine, but write every cost, hour count, multiple or other computed number as a placeholder from the menu below, like {planned_usd}; never type such a number yourself. You may write the $1,000 budget. Keep every sentence to 20 words or fewer. Give every sentence a section and a basis: SOURCE with a source id from the record, PLAN with the record field it restates, or GIVEN for the question's own budget and prices. Write at least one sentence for each of QUESTION, HYPOTHESIS, TEST, IF_LEVER, IF_NOT and LIMITS. Decide only from the text below; do not use tools. Return only the sentences, one per line, each starting with its section and basis in brackets, like [TEST, PLAN arms].
Root question: [root question]
Option record: [option record]
Plan record: [plan record without cost]
Menu:
[menu: one line per entry as {id} name (value)]
```

**Diff and notes:**

- WRITER (side cell only; the card is rendered from the producer's fields): "Using only [producer path] and [branch path]" becomes "Using only the records below"; "Invent no terms" gains the no-labels clause; "Numbers are fine" gains the placeholder rule (computed numbers only as {menu id}; $1,000 may be written); "Put a source URL after every factual sentence" becomes a section and a basis per sentence; "Write to [path]" becomes "Return only the sentences".
- Body text: substrate §10 with the cost §8.5 placeholder sentence in place of its "Numbers are fine, except ..." sentence. "GIVEN for the question's own budget and hardware" reads "budget and prices" (no hardware is given under the budget-only constraint). The return line names the one-line-per-sentence form, since the writer has no schema.

### DRAMATURG

`P_DRAMATURG(items)` · role qt-web, session model · edited in body

**Original (verbatim, CONTEXT.md):**

```text
Read [write-up path]. For every core claim, fetch the cited source and check it supports the claim. A derived number passes only if every input is cited and the arithmetic is shown. Reject if any core claim is uncited, unsupported, or its source is unreachable. Return JSON: {result: PASS or REJECT, reasons}.
```

**Final:**

```text
For each item below, fetch its source and check that the recorded quote appears on the page and supports the item. A card item is a field of the plan in the producer's words, with the sources it cites: check each factual claim in it against those sources, and any value it carries against the page; what the plan will build, measure or predict needs no source, but a factual claim with no source is UNSUPPORTED. For a cost input, check that the page states the number for the setting given; whether it applies to this plan is not yours to judge. When the page states a different number for a num or rate item, give it as page_value. Decide only from the pages you fetch and the text below; do not read files. Return one status per item, under its ref: SUPPORTED, PARTIAL, UNSUPPORTED, CONTRADICTED or UNREACHABLE, with the page sentence you relied on.
Items, one per line:
[items: one JSON object per line, each with its ref]
```

**Diff and notes:**

- DRAMATURG: reads inline items in place of [write-up path]; one status per item (SUPPORTED, PARTIAL, UNSUPPORTED, CONTRADICTED, UNREACHABLE) with the page sentence, in place of PASS or REJECT; "A derived number passes only if every input is cited and the arithmetic is shown" and "Reject if any core claim is uncited, unsupported, or its source is unreachable" move to the script (it computes every derived number and applies the PASS rule to the statuses); an uncited factual claim in a card item is UNSUPPORTED; cost inputs are checked against the page for the stated setting only, with page_value on a mismatch.
- Body text: substrate §10 and the first cost §8.5 sentence. Substrate's "A PLAN item passes if it restates the named record field" is replaced by the card-item sentence, because on the render path the card items are the plan's own fields (options-and-card §5.3). Cost §8.5's "For a sentence with computed numbers, check that it describes the menu quantity it uses" is left out: rendered cards carry no menu placeholders. The page_value sentence feeds the over-budget re-evaluation in `gate_decision` (CONTRACT §2.6).

### CRITIC

`P_CRITIC(root, option, cardText, planFields, criteria)` · role qt-bare, sonnet · edited in body

**Original (verbatim, CONTEXT.md):**

```text
Read [write-up path]. Score 1-5 on each criterion, quoting the sentence behind each score, or "cannot assess". Criteria: [criteria]. Also give compute payoff: the smallest budget that yields a reportable result at Lambda's on-demand prices (https://lambda.ai/pricing): $250, $500, $1,000, or none. Return JSON.
```

**Final:**

```text
Score the card 1-5 on each criterion. For each score give ref, the card line (card:<field>) that decides it, or plan:<field path> when no card line carries it, and a reason of at most 25 words. Use NA only where a criterion allows it. Then name decides_by: the id of the earliest phase after which decision_rule can be applied whichever outcome occurs, or "none". A phase that only reproduces a published number, or only measures throughput the question does not ask about, does not count. Give decides_by_reason in at most 25 words. Decide only from the text below; do not use tools.
Root question: [root question]
Option record: [option record]
Card:
[card: one line per field as card:<field>: text]
Plan fields: [plan fields]
Criteria:
[criteria]
```

**Diff and notes:**

- CRITIC: reads inline text (root question, option record, card, plan fields) in place of [write-up path]; "quoting the sentence behind each score" becomes ref (card:<field> or plan:<field path>) plus a reason of at most 25 words; "cannot assess" becomes NA only where a criterion allows it; the compute payoff tier ($250, $500, $1,000, none) becomes decides_by, the earliest phase after which the decision rule applies, which the script prices; a phase that only reproduces a published number, or only measures throughput the question does not ask about, does not count; "Decide only from the text below; do not use tools".
- Body text: criteria §8.2, with ref in the CONTRACT §2.6 form (card:<field> or plan:<field path>) and the decides_by definition (criteria §8.2) in the body, so the criteria list names only scored criteria.
- The caller passes plan fields without cost, full_scale, files_read, compute_tested(_why), predictions.expected(_why), novelty.decides and novelty.searched (main's criticView), and never the option critic's output.

#### CRITIC criteria

`CRIT_CARD(branch)` · names physical `stakes, lever, verifiable, open, reshape, baseline`; interp adds `internals` after open

**Original, physical:**

```text
scientific stakes; parallel restructuring; measurable speedup against a baseline; verifiable correctness; novelty against existing tools
```

**Original, interp:**

```text
scientific stakes; model access; what internals reveal that outputs don't; verifiable correctness; novelty
```

**Final, physical:**

```text
stakes: Take the two outcomes this test predicts, as measured here and within the limits in scope_gap. 5 = whichever occurs, a choice someone faces (what to buy, build, collect or scale next) changes, and the test measures the quantity that choice depends on; 3 = the outcomes bear on that choice only through a step this test does not check (a stand-in system, simulation to reality, a single model), or one outcome is already much more likely than the other; 1 = neither outcome would change anything. Do not score how famous the field is or how close it is to the root question.
lever: Could the result tell if_lever from if_not, with compute the only thing that changed? Check four conditions: (a) the predicted difference between if_lever and if_not is larger than what noise_rule says run-to-run noise can produce; (b) compute_axis spans at least 10×; (c) the varied quantity is bought with compute, not with more data, labels or people (when restructuring.method is not none: the arms run on the same hardware and differ only in method); (d) inputs that could also explain the difference are in held_fixed. 5 = all four hold; 3 = one fails or cannot be told from the plan; 1 = two or more fail, or the measured quantity is not the one the question asks about.
verifiable: What is the measured outcome scored against? 5 = an exact or planted truth that does not come from the method under test (a simulation's hidden true run, an exact success flag, a formal checker, planted items), and the setup first reproduces a published number within a stated tolerance; 3 = labels from a model or human rater with an agreement check, or exact truth with no reproduction step; 1 = nothing independent of the method's own output.
open: Does the closest published result already answer this question over this range? 5 = the quoted prior stops short of this range or asks a different question, and the plan states the gap; 3 = the prior answers part of it (a narrower range, a related system), or no prior is named; 1 = the quoted prior already answers it. Reusing published tools, models or benchmarks does not lower this score.
reshape: Does the plan remove a step-after-step dependency that one answer waits on, rather than run independent work side by side? 5 = restructuring names the dependency, why it need not run in order and how the plan computes it at the same time; condition says what must hold for that to pay off; condition_phase measures it before the main spend; and the closest prior does not already do this for this system; 3 = it removes a dependency, but condition is missing or is not measured before the main spend; 2 = it parallelises only within each step (splitting a large state across GPUs) or regroups and rebalances independent work (batching unfinished runs, load balancing, lower precision), leaving the chain in order; 1 = independent copies side by side, or one job per GPU, is the only parallelism, or the plan rebuilds a parallel version the closest prior already reports for this system. Reusing a method published for a different system does not lower this score.
baseline: Is the gain timed against the strongest ways to get the same answer without the plan's method? Check four conditions: (a) baseline_sequential is tuned (compiled, vectorised or multithreaded code, or a published optimised code), not a plain interpreted loop; (b) baseline_copies is timed on the same GPUs; (c) anchor checks the parallel result against the sequential one within a stated tolerance; (d) a named phase times every arm as time or dollars to one answer, so the gain is measured, not only modelled. 5 = all four hold; 3 = one fails or cannot be told from the plan; 1 = two or more fail. NA when restructuring.method is none.
```

**Final, interp:**

```text
stakes: Take the two outcomes this test predicts, as measured here and within the limits in scope_gap. 5 = whichever occurs, a choice someone faces (what to buy, build, collect or scale next) changes, and the test measures the quantity that choice depends on; 3 = the outcomes bear on that choice only through a step this test does not check (a stand-in system, simulation to reality, a single model), or one outcome is already much more likely than the other; 1 = neither outcome would change anything. Do not score how famous the field is or how close it is to the root question.
lever: Could the result tell if_lever from if_not, with compute the only thing that changed? Check four conditions: (a) the predicted difference between if_lever and if_not is larger than what noise_rule says run-to-run noise can produce; (b) compute_axis spans at least 10×; (c) the varied quantity is bought with compute, not with more data, labels or people (when restructuring.method is not none: the arms run on the same hardware and differ only in method); (d) inputs that could also explain the difference are in held_fixed. 5 = all four hold; 3 = one fails or cannot be told from the plan; 1 = two or more fail, or the measured quantity is not the one the question asks about.
verifiable: What is the measured outcome scored against? 5 = an exact or planted truth that does not come from the method under test (a simulation's hidden true run, an exact success flag, a formal checker, planted items), and the setup first reproduces a published number within a stated tolerance; 3 = labels from a model or human rater with an agreement check, or exact truth with no reproduction step; 1 = nothing independent of the method's own output.
open: Does the closest published result already answer this question over this range? 5 = the quoted prior stops short of this range or asks a different question, and the plan states the gap; 3 = the prior answers part of it (a narrower range, a related system), or no prior is named; 1 = the quoted prior already answers it. Reusing published tools, models or benchmarks does not lower this score.
internals: Does the test compare the internals readout with the strongest outputs-only method named in the plan or the option, on the same items, with a numeric margin in decision_rule? 5 = yes; 3 = compares only with a weaker outputs-only method than one named, or gives no margin; 1 = no outputs-only comparison.
reshape: Does the plan remove a step-after-step dependency that one answer waits on, rather than run independent work side by side? 5 = restructuring names the dependency, why it need not run in order and how the plan computes it at the same time; condition says what must hold for that to pay off; condition_phase measures it before the main spend; and the closest prior does not already do this for this system; 3 = it removes a dependency, but condition is missing or is not measured before the main spend; 2 = it parallelises only within each step (splitting a large state across GPUs) or regroups and rebalances independent work (batching unfinished runs, load balancing, lower precision), leaving the chain in order; 1 = independent copies side by side, or one job per GPU, is the only parallelism, or the plan rebuilds a parallel version the closest prior already reports for this system. Reusing a method published for a different system does not lower this score.
baseline: Is the gain timed against the strongest ways to get the same answer without the plan's method? Check four conditions: (a) baseline_sequential is tuned (compiled, vectorised or multithreaded code, or a published optimised code), not a plain interpreted loop; (b) baseline_copies is timed on the same GPUs; (c) anchor checks the parallel result against the sequential one within a stated tolerance; (d) a named phase times every arm as time or dollars to one answer, so the gain is measured, not only modelled. 5 = all four hold; 3 = one fails or cannot be told from the plan; 1 = two or more fail. NA when restructuring.method is none.
```

**Diff and notes:**

- CRITIC criteria: become stakes, lever, verifiable, open (interp adds internals), reshape and baseline, each with anchors. "parallel restructuring" becomes reshape and "measurable speedup against a baseline" becomes baseline, both reading the plan's restructuring record (baseline is NA when its method is none); lever (c) reads "the arms run on the same hardware and differ only in method" on a restructured plan; "verifiable correctness" becomes verifiable; "novelty against existing tools" and "novelty" become open; "model access" is dropped; "what internals reveal that outputs don't" becomes internals.
- stakes, verifiable, open, internals: criteria §8.2, verbatim.
- lever: criteria §8.2, with condition (c) reading "the arms run on the same hardware and differ only in method" when restructuring.method is not none.
- reshape and baseline: the sequential-structure change, verbatim. baseline allows NA when restructuring.method is none; no other criterion allows NA under the current args (no branch is exempt).

## Part 2. New prompts

### OVERLAP judge (S1b)

`P_OVERLAP(roots)` · role qt-bare, sonnet · new (substrate §10)

**Final:**

```text
Here are 5 questions, one per line as id: question. List every pair that shares a subject (the same field or the same object of study), naming the shared subject in at least three words. Decide only from the text below; do not use tools.
R1: [question 1]
R2: [question 2]
R3: [question 3]
R4: [question 4]
R5: [question 5]
```

**Diff and notes:**

- Substrate text, with "Here are five questions" replaced by the actual count (a generator can fail), the id: question line form, and "in a few words" replaced by "in at least three words" (the OVERLAP record requires three).

### DEDUP judge (S4)

`P_DEDUP(lines)` · role qt-bare, sonnet · new (substrate §10)

**Final:**

```text
Here are research options from several root questions, one per line as key: title. summary, where a key looks like R2:physical:W4. Group options that ask the same question of the same kind of system; every key goes in exactly one cluster, and a key that matches nothing is its own cluster. Name each cluster's topic in at least three words. Decide only from the text below; do not use tools.
[key]: [title]. [summary]
...
```

**Diff and notes:**

- Substrate text with the grouping rule from flow §2.10 / INTEGRATED §3 ("ask the same question of the same kind of system"), and the line form main builds (`key: title. summary`) with an example key, since keys contain colons.

### PRICE SHEET

`P_PRICE_SHEET()` · role qt-web, sonnet · new (cost §8.3, verbatim)

**Final:**

```text
Fetch https://lambda.ai/pricing and https://docs.lambda.ai/public-cloud/billing/. List every on-demand instance as {gpu, gpu_memory_gb, n_gpus, per_gpu_usd_h, page_text}, where page_text is the text that shows that price for that instance size; and the filesystem price with page_text and whether the page calls it an example. Decide only from these two pages.
```

### EXTRACT (producer fallback; replay)

`P_EXTRACT(producerPath, dir)` · role qt-extract, pinned sonnet · new (substrate §10 + cost §8.5)

**Final:**

```text
Read [producer path] and nothing else, except files under [dir] that it names as the output of a run. Transcribe the plan into the record in your output schema. Copy numbers exactly as written; where the file gives a number with no source or derivation, set its basis to GUESS and say what it rests on. Add no claims, sources or numbers that are not in the file. Hours the file calls an estimate are GUESS unless the file says a timer, cap or stop rule ends that phase; then they are DESIGN and the file's estimate of the work goes in need. A figure from a page about a different model, GPU, dataset, size or component is PROXY. Pessimistic or alternative figures go in scenarios or alternative lines, not in base values. Do not compute anything the file does not compute.
```

**Diff and notes:**

- Substrate text plus the cost §8.5 addition, verbatim, except that "Read [producer path] and nothing else" admits the run outputs producer.md names under [dir], so MEASURED numbers can carry their output line.

### REPAIR (cost expressions)

`P_REPAIR_EXPR(errors, record)` · role qt-bare, sonnet · new (substrate §10)

**Final:**

```text
These cost expressions failed a check:
[error 1]
[error 2]
Rewrite only those expressions, using the ids defined in the record (numbers, rates, lines) and budget_usd, with + - * / ^ ( ) and ceil, floor, min, max, pow; change no value or basis and add no numbers. Return each rewritten expression under its number or line id. Decide only from the record below; do not use tools.
Record: [record]
```

**Diff and notes:**

- Substrate text with "could not be evaluated" widened to "failed a check" (the repair also runs on gate_ref, quote and stated-total errors), "input ids" renamed to the record's ids (numbers, rates, lines) and budget_usd, the expression grammar listed, and the return form named.

### REPAIR (card fields)

`P_REPAIR_FIELDS(fields, caps, record)` · role qt-bare, sonnet · new (options-and-card §5.3)

**Final:**

```text
These record fields will be shown to a reader who has not seen the plan's files:
[field path] (at most [cap] words): [text]
Rewrite each in plain words within its word limit, replacing every label (such as W11, E2, C2, M*) with what it stands for, using only the record below. Keep every number exactly as written, and every [source id]. Add nothing. Return each rewritten field under its path. Decide only from the text below; do not use tools.
Record: [record]
```

**Diff and notes:**

- Report text with a word cap per field (fields have different caps), "and every [source id]" added so citations survive, and the return form named.

## Part 3. Role files

Written from `ROLE_FILES` to `/home/hal/stage/.claude/agents/<name>.md`.

### qt-bare

```markdown
---
name: qt-bare
description: Used only by the question-tree workflow, for steps that decide from the prompt text alone (root generators, judges, critics, writer, repairs). No tools.
tools: []
---

You read only what the prompt names. You return only the schema. Decide only from the text in the prompt. You have no tools.
```

### qt-research

```markdown
---
name: qt-research
description: Used only by the question-tree workflow, for the framer and branch agents, which research the web and write their own files.
tools: WebFetch, WebSearch, Bash, Read, Write, Edit
---

You read only the files the prompt names; fetch any web page you need. You return only the schema.
```

### qt-producer

```markdown
---
name: qt-producer
description: Used only by the question-tree workflow, for producers, which research, run small local pilots and write a plan.
tools: WebFetch, WebSearch, Bash, Read, Write, Edit
---

You read only what the prompt names. You return only the schema.
```

### qt-web

```markdown
---
name: qt-web
description: Used only by the question-tree workflow, for the dramaturg and the price sheet, which fetch pages and check quotes.
tools: WebFetch, Bash
---

You read only what the prompt names. You return only the schema.
```

### qt-extract

```markdown
---
name: qt-extract
description: Used only by the question-tree workflow, to transcribe a producer.md into its record. Reads the named file.
tools: Read
model: sonnet
---

You read only what the prompt names. You return only the schema.
```

`qt-bare` declares `tools: []`. Claude Code 2.1.301 parses an explicit empty list to no tools; an omitted `tools:` would inherit every tool. It refuses a zero-tool spawn only when a declared tool fails to resolve, which an empty list cannot trigger. Not verified by a live call: the Stage 1 probe must confirm a `qt-bare` agent still returns its schema. If it cannot, use `tools: Read` (CONTRACT §3); the body sentence does the rest.

## Part 4. `PROMPT_DIFF` (as the script carries it)

```text
Prompt version qt2-2 (2026-10-16). Originals are the ORIG_ constants.
Verbatim with a suffix appended: FRAMER (compute_signals); WIDENER (two definition sentences, then the branch suffix); DEEPENER (branch suffix); INTERP (interp quantity sentence, then the branch suffix); PRODUCER (option record, root question, bounded read, record and cost form, restructuring record, card fields, hang guard, price sheet). The branch suffix asks for root_link, compute_open, sequential (the step-after-step part of the work and whether it must run in order) and source URLs. PLAYWRIGHT and GUEST unchanged; on the S1b re-ask only, P_REASK is appended.
Changes in qt2-2: the branch suffix gains the sequential field; the WIDENER gains a second definition sentence (a problem whose steps run one after another counts, even where more hardware changes only how soon the answer arrives); the PRODUCER suffix gains the restructuring record and what the existing fields hold on a restructured plan, and its card-field list gains restructuring.sequential_part (18 words) and restructuring.method (22); the OPTION CRITIC passes each option's sequential field and its criteria gain reshape; the CRITIC criteria gain reshape and baseline, lever (c) reads "same hardware, method only" on a restructured plan, and the speedup sentence is deleted; the CRITIC body narrows the throughput exclusion of decides_by.
In-body edits:
- PRODUCER: removed the words "one machine, up to 8 GPUs, " and the colon before them (budget-only constraint), so it reads "up to $1,000 of GPU credit at Lambda's on-demand prices (https://lambda.ai/pricing)". A seed idea, which has no branch file, reads "in the option record below" in place of the branch path.
- OPTION CRITIC: the "cannot assess" choice is replaced by "There is no NA" with the none-scores-1 rule; a reason per score; verdict words ignored; SAME/ADJACENT/ELSEWHERE label with definitions and the root_link rule; "Do not add up the scores" replaces the returned total; "Decide only from the text below; do not use tools"; the root question is given; "Return JSON: [{id, scores, total}]" removed (the schema carries the form); each option line carries id, title, summary, root_link, compute_open and sequential.
- OPTION CRITIC criteria: the four semicolon criteria become stakes and open (interp adds internals), each with 5/3/1 anchors. "compute is the main limit" and "not already solved by existing tools" become open, scored within $1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours); "results checkable against a reference", "results checkable against known physics" and "model weights or activations are accessible" are dropped; "internals could reveal what outputs can't" becomes internals. Both branches add reshape: whether the option names a step-after-step chain one answer waits on and a checkable reason it need not run in order.
- CRITIC: reads inline text (root question, option record, card, plan fields) in place of [write-up path]; "quoting the sentence behind each score" becomes ref (card:<field> or plan:<field path>) plus a reason of at most 25 words; "cannot assess" becomes NA only where a criterion allows it; the compute payoff tier ($250, $500, $1,000, none) becomes decides_by, the earliest phase after which the decision rule applies, which the script prices; a phase that only reproduces a published number, or only measures throughput the question does not ask about, does not count; "Decide only from the text below; do not use tools".
- CRITIC criteria: become stakes, lever, verifiable, open (interp adds internals), reshape and baseline, each with anchors. "parallel restructuring" becomes reshape and "measurable speedup against a baseline" becomes baseline, both reading the plan's restructuring record (baseline is NA when its method is none); lever (c) reads "the arms run on the same hardware and differ only in method" on a restructured plan; "verifiable correctness" becomes verifiable; "novelty against existing tools" and "novelty" become open; "model access" is dropped; "what internals reveal that outputs don't" becomes internals.
- DRAMATURG: reads inline items in place of [write-up path]; one status per item (SUPPORTED, PARTIAL, UNSUPPORTED, CONTRADICTED, UNREACHABLE) with the page sentence, in place of PASS or REJECT; "A derived number passes only if every input is cited and the arithmetic is shown" and "Reject if any core claim is uncited, unsupported, or its source is unreachable" move to the script (it computes every derived number and applies the PASS rule to the statuses); an uncited factual claim in a card item is UNSUPPORTED; cost inputs are checked against the page for the stated setting only, with page_value on a mismatch.
- WRITER (side cell only; the card is rendered from the producer's fields): "Using only [producer path] and [branch path]" becomes "Using only the records below"; "Invent no terms" gains the no-labels clause; "Numbers are fine" gains the placeholder rule (computed numbers only as {menu id}; $1,000 may be written); "Put a source URL after every factual sentence" becomes a section and a basis per sentence; "Write to [path]" becomes "Return only the sentences".
New prompts: OVERLAP, DEDUP, PRICE_SHEET, EXTRACT, REPAIR_EXPR, REPAIR_FIELDS.
```
