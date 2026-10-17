// ---------- prompts: every prompt the pipeline sends, the criteria strings, the role files, the user's originals ----------
// Rules (CONTRACT §0, §3; INTEGRATED §4): the user's prompts stay verbatim with a suffix appended (PLAYWRIGHT, GUEST,
// FRAMER, WIDENER, DEEPENER, INTERP, PRODUCER); the PRODUCER loses only the words "one machine, up to 8 GPUs, " and the colon before them.
// OPTION CRITIC, CRITIC, DRAMATURG and WRITER are edited in body; PROMPT_DIFF lists each edit.
// No generator prompt says which field values halt a pick or move a score (H1). No em-dashes in any prompt.

// ---------- the user's originals, verbatim from CONTEXT.md (brackets are the script's fill-ins) ----------
const ORIG_PLAYWRIGHT = `Here are two questions someone asked. [EX1] [EX2] Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].`
const ORIG_GUEST = `You are Harry James Potter-Evans-Verres from Harry Potter and the Methods of Rationality. You test everything, look for exploits in how the world works, and light up when brute force becomes possible. Here are two questions someone asked. [EX1] [EX2] Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].`
const ORIG_FRAMER = `[question] Don't answer until you've defined and thought about the problem as thoroughly as possible without answering. Start by relaying your current understanding, making some predictions, and then proceed. Cite a URL for every factual claim. Write everything to [path]. End with one line, VERDICT: COMPUTE-BOUND or VERDICT: NOT COMPUTE-BOUND, and return JSON: {verdict}.`
const ORIG_WIDENER = `Read [framer path]. What sorts of related problems are compute constrained? Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].`
const ORIG_DEEPENER = `Read [framer path]. Go deeper on that: where does the compute go, and what would massive parallelism change? List the concrete options it opens up. Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].`
const ORIG_INTERP = `Read [framer path]. Are there mech interp (Goodfire style?) solutions to these sorts of problems? Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].`
const ORIG_OPTION_CRITIC = `Score each option 1-5 on each criterion, or "cannot assess". Criteria: [criteria]. Options: [options]. Return JSON: [{id, scores, total}].`
const ORIG_CRIT_OPTION_PHYSICAL = `scientific stakes; compute is the main limit; results checkable against a reference; not already solved by existing tools`
const ORIG_CRIT_OPTION_INTERP = `scientific stakes; model weights or activations are accessible; internals could reveal what outputs can't; results checkable against known physics`
const ORIG_PRODUCER = `Read option [id] "[title]" in [branch path]. I'm thinking about running something on this with up to $1,000 of GPU credit: one machine, up to 8 GPUs, at Lambda's on-demand prices (https://lambda.ai/pricing). Make it concrete: what to build, the baseline, how to check it's right, and the cost. Cite a URL for every factual claim. Write to [path].`
const ORIG_WRITER = `Using only [producer path] and [branch path], write a 150-250 word explanation of this idea. Add no new claims. Invent no terms. Numbers are fine. Keep every sentence to 20 words or fewer. Put a source URL after every factual sentence. Write to [path].`
const ORIG_DRAMATURG = `Read [write-up path]. For every core claim, fetch the cited source and check it supports the claim. A derived number passes only if every input is cited and the arithmetic is shown. Reject if any core claim is uncited, unsupported, or its source is unreachable. Return JSON: {result: PASS or REJECT, reasons}.`
const ORIG_CRITIC = `Read [write-up path]. Score 1-5 on each criterion, quoting the sentence behind each score, or "cannot assess". Criteria: [criteria]. Also give compute payoff: the smallest budget that yields a reportable result at Lambda's on-demand prices (https://lambda.ai/pricing): $250, $500, $1,000, or none. Return JSON.`
const ORIG_CRIT_CARD_PHYSICAL = `scientific stakes; parallel restructuring; measurable speedup against a baseline; verifiable correctness; novelty against existing tools`
const ORIG_CRIT_CARD_INTERP = `scientific stakes; model access; what internals reveal that outputs don't; verifiable correctness; novelty`

// the two questions the generators imitate; R1 is EX2 (verbatim from the original script)
const EX1_TEXT = `What limits the development of better crystal foundation models like for battery generation, is it a major blocker at some level, at could that be fixed with a shit ton of GPU parallelism?`
const EX2_TEXT = `Can scientific paper reviews (maybe specifically ML, DL, data-driven papers) be automated with highly scoped, small subagents following the AISLE model: many open-source models, since they have different blind spots, with tasks scoped to known failure modes like biases, factual reproduction errors, 'do these authors/papers exist' errors and overclaims, including building the suggested experiments and variations and running them on GPUs? Is compute a major blocker at some level, could a shit ton of GPU parallelism fix it?`

// a value inlined in a prompt: text as written, records as JSON, absent as "none"
const P_str = v => (v == null ? 'none' : typeof v === 'string' ? v : JSON.stringify(v))
// a list inlined one item per line
const P_lines = xs => (Array.isArray(xs) ? xs.map(P_str).join('\n') : P_str(xs))

// ---------- S1 roots: generators verbatim; the re-ask sentence is appended (after a space) only on S1b ----------
function P_PLAYWRIGHT(EX1, EX2) {
  return `Here are two questions someone asked. "${EX1}" "${EX2}" Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].`
}
function P_GUEST(EX1, EX2) {
  return `You are Harry James Potter-Evans-Verres from Harry Potter and the Methods of Rationality. You test everything, look for exploits in how the world works, and light up when brute force becomes possible. Here are two questions someone asked. "${EX1}" "${EX2}" Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].`
}
// roots: [{id, question}] or [question]
function P_REASK(roots) {
  return `Also make them orthogonal to these: ${roots.map(r => `"${r.question ?? r}"`).join(' ')}.`
}
function P_OVERLAP(roots) {
  return `Here are ${roots.length} questions, one per line as id: question. List every pair that shares a subject (the same field or the same object of study), naming the shared subject in at least three words. Decide only from the text below; do not use tools.\n` +
    roots.map(r => `${r.id}: ${r.question}`).join('\n')
}

// ---------- S2 framer, S3 branches: verbatim + suffix ----------
function P_FRAMER(question, path) {
  return `${question} Don't answer until you've defined and thought about the problem as thoroughly as possible without answering. Start by relaying your current understanding, making some predictions, and then proceed. Cite a URL for every factual claim. Write everything to ${path}. End with one line, VERDICT: COMPUTE-BOUND or VERDICT: NOT COMPUTE-BOUND, and return JSON: {verdict}.` +
    ` Also return compute_signals: up to three parts of the problem where more parallel compute might change the answer, each as {subproblem, what_compute_buys}, or an empty list.`
}
// shared branch suffix (options-and-card §2.2; quantity list and the URL from CONTRACT §2.2)
const P_branchSuffix = framerPath => `For each option also return root_link: one sentence on which part of the question in ${framerPath} it bears on, or "none". Return compute_open: one sentence naming the quantity more parallel compute would buy for it (samples, ensemble members, resolution, model runs, model size, search width or seeds), the largest amount of it that any source you cite reports, with that source's URL, and what is still unknown about its effect on the answer above that amount; or "settled:" followed by what is known and its source URL; or "none". Return sequential: the part of the work that one answer waits on step after step (what each step waits for, and roughly how many steps one run takes), how many independent runs the answer needs, and how much of one GPU a single run keeps busy; then whether those steps must run in order, and if not, what change to the computation would let them run at the same time, what would have to be true of the system for that change to pay off, and the nearest source that has tried it, with its URL; or "none:" followed by why the work already splits into independent pieces. Return up to three source URLs. Use the option's heading label in your file as its id.`
function P_WIDENER(framerPath, path) {
  return `Read ${framerPath}. What sorts of related problems are compute constrained? Cite a URL for every factual claim. Write to ${path}. Return JSON: [{id, title, summary}].` +
    // reinterprets "compute constrained" (consent given 2026-10-16, both definition sentences)
    ` Count a related problem as compute constrained when it is still open whether more parallel compute would change its answer, not only when compute is already known to bind there. List both kinds, and mark the second kind settled in compute_open. Also count a problem whose answer takes long because its steps run one after another, even where more hardware would not change the answer, only how soon it arrives. ${P_branchSuffix(framerPath)}`
}
function P_DEEPENER(framerPath, path) {
  return `Read ${framerPath}. Go deeper on that: where does the compute go, and what would massive parallelism change? List the concrete options it opens up. Cite a URL for every factual claim. Write to ${path}. Return JSON: [{id, title, summary}]. ${P_branchSuffix(framerPath)}`
}
function P_INTERP(framerPath, path) {
  return `Read ${framerPath}. Are there mech interp (Goodfire style?) solutions to these sorts of problems? Cite a URL for every factual claim. Write to ${path}. Return JSON: [{id, title, summary}].` +
    ` For an interpretability option the quantity may be models, layers, features, prompts or seeds analysed; write none in compute_open if more of it would not change the answer. ${P_branchSuffix(framerPath)}`
}

// ---------- S4' option critic (in body, criteria §8.1 + substrate §5 distance labels) ----------
// The critic sees only the branch agent's text fields: no source_urls (it cannot check them), no scores.
function P_OPTION_CRITIC(root, criteria, options) {
  const opts = Array.isArray(options)
    ? options.map(o => JSON.stringify({ id: o.id, title: o.title, summary: o.summary, root_link: o.root_link, compute_open: o.compute_open, sequential: o.sequential })).join('\n')
    : P_str(options)
  return `Score each option 1-5 on each criterion. There is no NA: a field that says "none" or "none known" scores 1. Give each score a reason of at most 20 words. Score from the quantities, sources and gaps the option names; ignore verdict words such as COMPUTE-BOUND or NOT COMPUTE-BOUND. Also label each option SAME, ADJACENT or ELSEWHERE against the root question, with a reason: SAME if it asks the root question or a sub-question of it, ADJACENT if it has the root's subject but asks a different question, ELSEWHERE if its subject is different. Decide the subject from the title and summary; count root_link only if the summary itself describes the root question's object of study. Do not add up the scores. Decide only from the text below; do not use tools.\n` +
    `Root question: ${P_str(root)}\nCriteria:\n${criteria}\nOptions, one per line:\n${opts}`
}
// criteria §8.1; the open reach clause is budget-only (CONTRACT §0); interp names its own compute quantities
function CRIT_OPTION(branch) {
  const quantity = branch === 'interp' ? 'models, layers, features, prompts or seeds analysed' : 'samples, ensemble members, resolution, model runs, model size, search width'
  const lines = [
    `stakes: Suppose the question this option raises were answered, either way. 5 = a choice someone faces (what to buy, build, collect or scale next) turns on the answer, and either answer would move it; 3 = the answer would refine a belief but no choice turns on it, or one answer is already much more likely than the other; 1 = either answer is already expected, or nothing would change. Do not score how famous or important the field is, or how close it is to the root question.`,
    `open: Has published work already measured how the answer changes with the quantity compute buys here (${quantity}), across the range that $1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours) can reach? 5 = names the quantity and where published measurements stop (or that none exist), and the unmeasured range starts within that reach; 3 = the unmeasured range is reachable only through a smaller stand-in system, or published work already covers part of the reachable range; 1 = names no compute-bought quantity, or published work already covers everything within that reach, so the open range lies only beyond it.`,
  ]
  if (branch === 'interp') lines.push(`internals: Does the summary name specific information the model's internals could carry that its outputs do not, and say why outputs miss it? 5 = names the information and why outputs miss it; 3 = names a general kind (features, a representation, a direction) without what it adds over outputs; 1 = names none.`)
  lines.push(`reshape: Does the option name a part of the work that one answer waits on step after step, and a reason those steps might not have to run in order? 5 = names that chain and roughly how long it is; one answer leaves most of a GPU idle (a small state, or few runs needed, so copies side by side would not fill it); names what would have to be true of the system for the steps to be computed at the same time, in a form a cheap measurement could check; and no cited source already computes this chain in parallel for this system; 3 = names the chain and a way to restructure it, but one of these fails: the answer needs many independent runs, so copies side by side already fill the hardware; one run already fills a GPU; or no checkable condition is named; 1 = sequential says none, or the only parallelism is independent pieces (copies, a sweep, one job per GPU), or a cited source already computes this chain in parallel for this system. A method published for a different system does not lower this score. Do not score how famous the method or field is.`)
  return lines.join('\n')
}

// ---------- S4 dedup judge (substrate §10, grouping wording from flow §2.10) ----------
// lines: ["<key>: <title>. <summary>"]
function P_DEDUP(lines) {
  return `Here are research options from several root questions, one per line as key: title. summary, where a key looks like R2:physical:W4. Group options that ask the same question of the same kind of system; every key goes in exactly one cluster, and a key that matches nothing is its own cluster. Name each cluster's topic in at least three words. Decide only from the text below; do not use tools.\n${P_lines(lines)}`
}

// ---------- price sheet (cost §8.3), once per run ----------
function P_PRICE_SHEET() {
  return `Fetch https://lambda.ai/pricing and https://docs.lambda.ai/public-cloud/billing/. List every on-demand instance as {gpu, gpu_memory_gb, n_gpus, per_gpu_usd_h, page_text}, where page_text is the text that shows that price for that instance size; and the filesystem price with page_text and whether the page calls it an example. Decide only from these two pages.`
}

// ---------- S6 producer: verbatim minus ": one machine, up to 8 GPUs," + suffix ----------
// Suffix: substrate §10 (record, bounded read), cost §8.5 trimmed to minimal estimates, criteria §8.3,
// options-and-card §5.3 (card fields, caps from CONTRACT §2.5), flow §2.4 hang guard.
// A seed idea has no branch or framer file and no root: its record is the option and the read list shrinks.
function P_PRODUCER({ idTitle, branchPath, path, dir, optionRecord, rootQuestion, framerPath, priceSheetText }) {
  const reads = [branchPath, framerPath].filter(Boolean)
  return `Read option ${idTitle} in ${branchPath || 'the option record below'}. I'm thinking about running something on this with up to $1,000 of GPU credit at Lambda's on-demand prices (https://lambda.ai/pricing). Make it concrete: what to build, the baseline, how to check it's right, and the cost. Cite a URL for every factual claim. Write to ${path}.` +
    ` Option record: ${P_str(optionRecord)}. Root question: ${P_str(rootQuestion)}.` +
    ` Read only ${[...reads, 'pages you fetch'].join(', ')} and what you write under ${dir}; write only under ${dir}. When the plan is written, return it as the record in your output schema; producer.md stays your working file.` +
    ` In the record, put every number the cost or the size of the test depends on in numbers, each with a basis: CITED (a page states this number for this same setting; give the page text that shows it), PROXY (a page states it for a different model, GPU, dataset, size or component; give the page text and say what differs), MEASURED (you ran code: save the script and its output under ${dir}/pilot/ and give the output line and the machine), DERIVED (an expression over other ids), DESIGN (your choice), or GUESS (no source; say what it rests on).` +
    ` Give each rate as the per-GPU price and the GPU count, and each line's hours as an expression. The default line is a time box: DESIGN hours at a rate from the prices below, ended by a timer or stop rule; it needs no estimate of the work inside it, but if you have one, put it in need. Use GUESS only where a number drives the plan. For each PROXY or GUESS the cost or result depends on, name the phase that measures it in measured_by, and give that phase's threshold as gate if your plan changes on it. Optional: scenarios (pessimistic or sensitivity cases, as values for the inputs they change), optional lines for stretch work, instead_of for fallbacks, and yields (the number ids that say what the money buys: cases, samples, primes). Refer to the budget as budget_usd and to the price sheet's filesystem price as fs_usd_gib_month. List human time and money outside Lambda in outside_budget.` +
    ` predictions.if_lever and predictions.if_not are the outcomes you expect, on the same measured quantity, if more compute does or does not change the answer. predictions.noise_rule says how you will tell a real difference from run-to-run noise. predictions.expected is the outcome you expect, if_lever, if_not or unsure, with one sentence why. scored_against says what the measured outcome is compared with to decide it is correct. Each source carries the exact sentence from the page that you rely on.` +
    ` In restructuring, sequential_part is the part of this computation that one answer waits on step after step, and how many steps; method is why those steps need not run in order and how your plan computes them at the same time instead, or "none" if the plan only runs independent work side by side or splits each step across GPUs. If method is not none, also give condition, what must be true of this system for the method to pay off and the cheap measurement that checks it; condition_phase, the id of the phase that makes that measurement before the main spend; baseline_sequential, the fastest sequential implementation you will time and how it is tuned; and baseline_copies, independent copies run side by side on the same GPUs, which you will also time. Then compute_axis is the length of the chain or the number of runs the answer needs; predictions.if_lever and predictions.if_not say where on that axis, as numbers, the parallel version does or does not reach the same answer sooner than each baseline, and if_not says how you expect it to fail if it does; anchor checks the parallel result against the sequential one within a stated tolerance; test_summary names both baselines; and novelty.closest_prior is the nearest published parallel version of this computation.` +
    ` Write the record's card fields (question, hypothesis, predictions.if_lever, predictions.if_not, test_summary, novelty.closest_prior, novelty.left_open, anchor.what, limits, restructuring.sequential_part, restructuring.method) for a reader who has not seen your files: plain words, at most 25 words each (hypothesis and predictions.if_lever 22, anchor.what 24, novelty.closest_prior, novelty.left_open and limits 30, test_summary 45, restructuring.sequential_part 18, restructuring.method 22), no labels from your files or from the branch and framer files (write what C2 or E2 stands for, not the label), and keep every number the decision depends on. You may cite a source in any card field as [source id]. novelty.closest_prior is the published result that comes nearest to deciding between if_lever and if_not: what it measured and the largest amount of the compute quantity it used. novelty.prior_max_level is that amount in compute_axis.unit, or null if it is not on the same axis. novelty.decides says whether closest_prior already decides the outcome at your compute levels: no, partly or yes. novelty.searched says whether web search returned results while you planned.` +
    ` Run every local command under timeout. Start no new local run 45 minutes after you begin; if a run you need is unfinished by then, give its inputs basis GUESS with measured_by naming the phase that measures it. Local runs share a 4-core machine with other producers.` +
    ` Lambda's prices as read at the start of this run: ${priceSheetText || 'not available; read them from https://lambda.ai/pricing'}.`
}

// ---------- S6 fallback and repairs (new prompts) ----------
// substrate §10 extract + cost §8.5 addition; dir lets it read the run outputs producer.md names
function P_EXTRACT(producerPath, dir) {
  return `Read ${producerPath} and nothing else, except files under ${dir} that it names as the output of a run. Transcribe the plan into the record in your output schema. Copy numbers exactly as written; where the file gives a number with no source or derivation, set its basis to GUESS and say what it rests on. Add no claims, sources or numbers that are not in the file. Hours the file calls an estimate are GUESS unless the file says a timer, cap or stop rule ends that phase; then they are DESIGN and the file's estimate of the work goes in need. A figure from a page about a different model, GPU, dataset, size or component is PROXY. Pessimistic or alternative figures go in scenarios or alternative lines, not in base values. Do not compute anything the file does not compute.`
}
// errors: [str]; record: the PLAN
function P_REPAIR_EXPR(errors, record) {
  return `These cost expressions failed a check:\n${P_lines(errors)}\nRewrite only those expressions, using the ids defined in the record (numbers, rates, lines) and budget_usd, with + - * / ^ ( ) and ceil, floor, min, max, pow; change no value or basis and add no numbers. Return each rewritten expression under its number or line id. Decide only from the record below; do not use tools.\nRecord: ${P_str(record)}`
}
// fields: {path: text}; caps: {path: words}; record: the PLAN (options-and-card §5.3)
function P_REPAIR_FIELDS(fields, caps, record) {
  const list = Object.entries(fields).map(([f, t]) => `${f} (at most ${caps[f]} words): ${t}`).join('\n')
  return `These record fields will be shown to a reader who has not seen the plan's files:\n${list}\nRewrite each in plain words within its word limit, replacing every label (such as W11, E2, C2, M*) with what it stands for, using only the record below. Keep every number exactly as written, and every [source id]. Add nothing. Return each rewritten field under its path. Decide only from the text below; do not use tools.\nRecord: ${P_str(record)}`
}

// ---------- S7 writer side cell (in body: substrate §10 + cost §8.5 placeholder sentence) ----------
// menu: [{id, name, value}] from cost_menu; the script fills {id} placeholders afterwards
function P_WRITER(root, option, planNoCost, menu) {
  const items = Array.isArray(menu) ? menu.map(m => `{${m.id}} ${m.name} (${m.value})`).join('\n') : P_str(menu)
  return `Using only the records below, write a 150-250 word explanation of this idea. Add no new claims. Invent no terms, and use no labels from the records as words (option ids like W11, phase ids like P0, criterion labels like C2): say what the thing is. Numbers are fine, but write every cost, hour count, multiple or other computed number as a placeholder from the menu below, like {planned_usd}; never type such a number yourself. You may write the $1,000 budget. Keep every sentence to 20 words or fewer. Give every sentence a section and a basis: SOURCE with a source id from the record, PLAN with the record field it restates, or GIVEN for the question's own budget and prices. Write at least one sentence for each of QUESTION, HYPOTHESIS, TEST, IF_LEVER, IF_NOT and LIMITS. Decide only from the text below; do not use tools. Return only the sentences, one per line, each starting with its section and basis in brackets, like [TEST, PLAN arms].\n` +
    `Root question: ${P_str(root)}\nOption record: ${P_str(option)}\nPlan record: ${P_str(planNoCost)}\nMenu:\n${items}`
}

// ---------- S8 dramaturg (in body: substrate §10 + cost §8.5; the PASS/REJECT rule is the script's) ----------
// items: [{ref, ...}] as main builds them (card fields with their sources, src:, num:, rate:)
function P_DRAMATURG(items) {
  return `For each item below, fetch its source and check that the recorded quote appears on the page and supports the item. A card item is a field of the plan in the producer's words, with the sources it cites: check each factual claim in it against those sources, and any value it carries against the page; what the plan will build, measure or predict needs no source, but a factual claim with no source is UNSUPPORTED. For a cost input, check that the page states the number for the setting given; whether it applies to this plan is not yours to judge. When the page states a different number for a num or rate item, give it as page_value. Decide only from the pages you fetch and the text below; do not read files. Return one status per item, under its ref: SUPPORTED, PARTIAL, UNSUPPORTED, CONTRADICTED or UNREACHABLE, with the page sentence you relied on.\nItems, one per line:\n${P_lines(items)}`
}

// ---------- S9 critic (in body: criteria §8.2; decides_by replaces the payoff tier, the script prices it) ----------
// planFields: the plan without cost, full_scale, files_read and the producer's self-grades (main's criticView)
function P_CRITIC(root, option, cardText, planFields, criteria) {
  return `Score the card 1-5 on each criterion. For each score give ref, the card line (card:<field>) that decides it, or plan:<field path> when no card line carries it, and a reason of at most 25 words. Use NA only where a criterion allows it. Then name decides_by: the id of the earliest phase after which decision_rule can be applied whichever outcome occurs, or "none". A phase that only reproduces a published number, or only measures throughput the question does not ask about, does not count. Give decides_by_reason in at most 25 words. Decide only from the text below; do not use tools.\n` +
    `Root question: ${P_str(root)}\nOption record: ${P_str(option)}\nCard:\n${cardText}\nPlan fields: ${P_str(planFields)}\nCriteria:\n${criteria}`
}
// criteria §8.2; lever (c) reads "same hardware, method only" on a restructured plan; reshape and baseline read restructuring
function CRIT_CARD(branch) {
  const lines = [
    `stakes: Take the two outcomes this test predicts, as measured here and within the limits in scope_gap. 5 = whichever occurs, a choice someone faces (what to buy, build, collect or scale next) changes, and the test measures the quantity that choice depends on; 3 = the outcomes bear on that choice only through a step this test does not check (a stand-in system, simulation to reality, a single model), or one outcome is already much more likely than the other; 1 = neither outcome would change anything. Do not score how famous the field is or how close it is to the root question.`,
    `lever: Could the result tell if_lever from if_not, with compute the only thing that changed? Check four conditions: (a) the predicted difference between if_lever and if_not is larger than what noise_rule says run-to-run noise can produce; (b) compute_axis spans at least 10×; (c) the varied quantity is bought with compute, not with more data, labels or people (when restructuring.method is not none: the arms run on the same hardware and differ only in method); (d) inputs that could also explain the difference are in held_fixed. 5 = all four hold; 3 = one fails or cannot be told from the plan; 1 = two or more fail, or the measured quantity is not the one the question asks about.`,
    `verifiable: What is the measured outcome scored against? 5 = an exact or planted truth that does not come from the method under test (a simulation's hidden true run, an exact success flag, a formal checker, planted items), and the setup first reproduces a published number within a stated tolerance; 3 = labels from a model or human rater with an agreement check, or exact truth with no reproduction step; 1 = nothing independent of the method's own output.`,
    `open: Does the closest published result already answer this question over this range? 5 = the quoted prior stops short of this range or asks a different question, and the plan states the gap; 3 = the prior answers part of it (a narrower range, a related system), or no prior is named; 1 = the quoted prior already answers it. Reusing published tools, models or benchmarks does not lower this score.`,
  ]
  if (branch === 'interp') lines.push(`internals: Does the test compare the internals readout with the strongest outputs-only method named in the plan or the option, on the same items, with a numeric margin in decision_rule? 5 = yes; 3 = compares only with a weaker outputs-only method than one named, or gives no margin; 1 = no outputs-only comparison.`)
  lines.push(
    `reshape: Does the plan remove a step-after-step dependency that one answer waits on, rather than run independent work side by side? 5 = restructuring names the dependency, why it need not run in order and how the plan computes it at the same time; condition says what must hold for that to pay off; condition_phase measures it before the main spend; and the closest prior does not already do this for this system; 3 = it removes a dependency, but condition is missing or is not measured before the main spend; 2 = it parallelises only within each step (splitting a large state across GPUs) or regroups and rebalances independent work (batching unfinished runs, load balancing, lower precision), leaving the chain in order; 1 = independent copies side by side, or one job per GPU, is the only parallelism, or the plan rebuilds a parallel version the closest prior already reports for this system. Reusing a method published for a different system does not lower this score.`,
    `baseline: Is the gain timed against the strongest ways to get the same answer without the plan's method? Check four conditions: (a) baseline_sequential is tuned (compiled, vectorised or multithreaded code, or a published optimised code), not a plain interpreted loop; (b) baseline_copies is timed on the same GPUs; (c) anchor checks the parallel result against the sequential one within a stated tolerance; (d) a named phase times every arm as time or dollars to one answer, so the gain is measured, not only modelled. 5 = all four hold; 3 = one fails or cannot be told from the plan; 1 = two or more fail. NA when restructuring.method is none.`)
  return lines.join('\n')
}

// ---------- every in-body edit, for the run header and PROMPTS.md ----------
const PROMPT_DIFF = [
  'Prompt version qt2-2 (2026-10-16). Originals are the ORIG_ constants.',
  'Verbatim with a suffix appended: FRAMER (compute_signals); WIDENER (two definition sentences, then the branch suffix); DEEPENER (branch suffix); INTERP (interp quantity sentence, then the branch suffix); PRODUCER (option record, root question, bounded read, record and cost form, restructuring record, card fields, hang guard, price sheet). The branch suffix asks for root_link, compute_open, sequential (the step-after-step part of the work and whether it must run in order) and source URLs. PLAYWRIGHT and GUEST unchanged; on the S1b re-ask only, P_REASK is appended.',
  'Changes in qt2-2: the branch suffix gains the sequential field; the WIDENER gains a second definition sentence (a problem whose steps run one after another counts, even where more hardware changes only how soon the answer arrives); the PRODUCER suffix gains the restructuring record and what the existing fields hold on a restructured plan, and its card-field list gains restructuring.sequential_part (18 words) and restructuring.method (22); the OPTION CRITIC passes each option\'s sequential field and its criteria gain reshape; the CRITIC criteria gain reshape and baseline, lever (c) reads "same hardware, method only" on a restructured plan, and the speedup sentence is deleted; the CRITIC body narrows the throughput exclusion of decides_by.',
  'In-body edits:',
  '- PRODUCER: removed the words "one machine, up to 8 GPUs, " and the colon before them (budget-only constraint), so it reads "up to $1,000 of GPU credit at Lambda\'s on-demand prices (https://lambda.ai/pricing)". A seed idea, which has no branch file, reads "in the option record below" in place of the branch path.',
  '- OPTION CRITIC: the "cannot assess" choice is replaced by "There is no NA" with the none-scores-1 rule; a reason per score; verdict words ignored; SAME/ADJACENT/ELSEWHERE label with definitions and the root_link rule; "Do not add up the scores" replaces the returned total; "Decide only from the text below; do not use tools"; the root question is given; "Return JSON: [{id, scores, total}]" removed (the schema carries the form); each option line carries id, title, summary, root_link, compute_open and sequential.',
  '- OPTION CRITIC criteria: the four semicolon criteria become stakes and open (interp adds internals), each with 5/3/1 anchors. "compute is the main limit" and "not already solved by existing tools" become open, scored within $1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours); "results checkable against a reference", "results checkable against known physics" and "model weights or activations are accessible" are dropped; "internals could reveal what outputs can\'t" becomes internals. Both branches add reshape: whether the option names a step-after-step chain one answer waits on and a checkable reason it need not run in order.',
  '- CRITIC: reads inline text (root question, option record, card, plan fields) in place of [write-up path]; "quoting the sentence behind each score" becomes ref (card:<field> or plan:<field path>) plus a reason of at most 25 words; "cannot assess" becomes NA only where a criterion allows it; the compute payoff tier ($250, $500, $1,000, none) becomes decides_by, the earliest phase after which the decision rule applies, which the script prices; a phase that only reproduces a published number, or only measures throughput the question does not ask about, does not count; "Decide only from the text below; do not use tools".',
  '- CRITIC criteria: become stakes, lever, verifiable, open (interp adds internals), reshape and baseline, each with anchors. "parallel restructuring" becomes reshape and "measurable speedup against a baseline" becomes baseline, both reading the plan\'s restructuring record (baseline is NA when its method is none); lever (c) reads "the arms run on the same hardware and differ only in method" on a restructured plan; "verifiable correctness" becomes verifiable; "novelty against existing tools" and "novelty" become open; "model access" is dropped; "what internals reveal that outputs don\'t" becomes internals.',
  '- DRAMATURG: reads inline items in place of [write-up path]; one status per item (SUPPORTED, PARTIAL, UNSUPPORTED, CONTRADICTED, UNREACHABLE) with the page sentence, in place of PASS or REJECT; "A derived number passes only if every input is cited and the arithmetic is shown" and "Reject if any core claim is uncited, unsupported, or its source is unreachable" move to the script (it computes every derived number and applies the PASS rule to the statuses); an uncited factual claim in a card item is UNSUPPORTED; cost inputs are checked against the page for the stated setting only, with page_value on a mismatch.',
  '- WRITER (side cell only; the card is rendered from the producer\'s fields): "Using only [producer path] and [branch path]" becomes "Using only the records below"; "Invent no terms" gains the no-labels clause; "Numbers are fine" gains the placeholder rule (computed numbers only as {menu id}; $1,000 may be written); "Put a source URL after every factual sentence" becomes a section and a basis per sentence; "Write to [path]" becomes "Return only the sentences".',
  'New prompts: OVERLAP, DEDUP, PRICE_SHEET, EXTRACT, REPAIR_EXPR, REPAIR_FIELDS.',
].join('\n')

// ---------- role files (/home/hal/stage/.claude/agents/<name>.md) ----------
// qt-bare declares an explicit empty list: Claude Code 2.1.301 parses `tools: []` to no tools (an omitted
// `tools:` would inherit every tool), and only refuses a spawn when a declared tool fails to resolve.
function ROLE_md(name, description, tools, model, body) {
  return `---\nname: ${name}\ndescription: ${description}\ntools: ${tools}\n${model ? `model: ${model}\n` : ''}---\n\n${body}\n`
}
const ROLE_BODY = 'You read only what the prompt names. You return only the schema.'
const ROLE_FILES = {
  'qt-bare': ROLE_md('qt-bare', 'Used only by the question-tree workflow, for steps that decide from the prompt text alone (root generators, judges, critics, writer, repairs). No tools.', '[]', null, `${ROLE_BODY} Decide only from the text in the prompt. You have no tools.`),
  'qt-research': ROLE_md('qt-research', 'Used only by the question-tree workflow, for the framer and branch agents, which research the web and write their own files.', 'WebFetch, WebSearch, Bash, Read, Write, Edit', null, 'You read only the files the prompt names; fetch any web page you need. You return only the schema.'),
  'qt-producer': ROLE_md('qt-producer', 'Used only by the question-tree workflow, for producers, which research, run small local pilots and write a plan.', 'WebFetch, WebSearch, Bash, Read, Write, Edit', null, ROLE_BODY),
  'qt-web': ROLE_md('qt-web', 'Used only by the question-tree workflow, for the dramaturg and the price sheet, which fetch pages and check quotes.', 'WebFetch, Bash', null, ROLE_BODY),
  'qt-extract': ROLE_md('qt-extract', 'Used only by the question-tree workflow, to transcribe a producer.md into its record. Reads the named file.', 'Read', 'sonnet', ROLE_BODY),
}
