// Generates PROMPTS.md from src/prompts.js so the document cannot drift from the code. Usage: node tools/genmd.js
const fs = require('fs'), vm = require('vm'), path = require('path')
const ROOT = path.join(__dirname, '..')
const ctx = {}; vm.createContext(ctx)
vm.runInContext(fs.readFileSync(path.join(ROOT, 'src/prompts.js'), 'utf8'), ctx)
const R = s => vm.runInContext(s, ctx)
const block = s => '```text\n' + s + '\n```'
const diffLine = key => R('PROMPT_DIFF').split('\n').filter(l => l.startsWith(`- ${key}`)).map(l => l.slice(2))
const out = []
const P = s => out.push(s)

P(`# question-tree v2 prompts

Generated from \`src/prompts.js\` (prompt version qt2-2, 2026-10-16); the code is the source of truth. Placeholders the script fills are in [brackets]. Role (\`agentType\`) and model per call are as \`CONTRACT.md\` §3 sets them; "session" means the session model.

How the user's prompts were treated (INTEGRATED §4, CONTRACT §0):
- Verbatim, with a suffix appended: PLAYWRIGHT and GUEST (re-ask sentence on S1b only), FRAMER, WIDENER, DEEPENER, INTERP, PRODUCER.
- The PRODUCER's verbatim text loses exactly the words "one machine, up to 8 GPUs, " and the colon before them (budget-only constraint); nothing else in it changes.
- Edited in body: OPTION CRITIC (and its criteria strings), CRITIC (and its criteria strings), DRAMATURG, WRITER (side cell only).
- New: OVERLAP, DEDUP, PRICE_SHEET, EXTRACT, REPAIR_EXPR, REPAIR_FIELDS.
- No generator prompt says which field values halt a pick or move a score (H1). No em-dashes.
`)

const sec = (title, fn, role, status, orig, final, notes) => {
  P(`### ${title}\n\n\`${fn}\` · ${role} · ${status}\n`)
  if (orig) P(`**Original (verbatim, CONTEXT.md):**\n\n${block(orig)}\n`)
  P(`**Final:**\n\n${block(final)}\n`)
  if (notes && notes.length) P(`**Diff and notes:**\n\n${notes.map(n => `- ${n}`).join('\n')}\n`)
}

P('## Part 1. The user\'s prompts\n')
sec('PLAYWRIGHT', 'P_PLAYWRIGHT(EX1, EX2)', 'role qt-bare, session model', 'verbatim, unchanged', R('ORIG_PLAYWRIGHT'), R('P_PLAYWRIGHT(EX1_TEXT, EX2_TEXT)'),
  ['EX1 and EX2 are the original script\'s texts (`EX1_TEXT`, `EX2_TEXT`), quoted as the original script quoted them. The function output equals the original script\'s prompt byte for byte.'])
sec('GUEST', 'P_GUEST(EX1, EX2)', 'role qt-bare, session model', 'verbatim, unchanged', R('ORIG_GUEST'), R('P_GUEST(EX1_TEXT, EX2_TEXT)'), [])
sec('Re-ask suffix (S1b only)', 'P_REASK(roots)', 'no role of its own: appended after a space to PLAYWRIGHT or GUEST', 'new suffix (substrate §10)', null,
  R('P_REASK(["[kept root 1]", "[kept root 2]", "[kept root 3]"])'), ['Each kept root is quoted, in the style of [EX1] [EX2]. Accepts `[{id, question}]` (what main passes) or `[question]`.'])
sec('FRAMER', 'P_FRAMER(question, path)', 'role qt-research, session model', 'verbatim + suffix', R('ORIG_FRAMER'), R('P_FRAMER("[question]", "[path]")'),
  ['Suffix (substrate §10, verbatim): the compute_signals sentence.'])
sec('WIDENER', 'P_WIDENER(framerPath, path)', 'role qt-research, session model', 'verbatim + suffix', R('ORIG_WIDENER'), R('P_WIDENER("[framer path]", "[path]")'),
  ['Suffix: the two WIDENER-only definition sentences (options-and-card §2.2, then the sequential-structure change; each reinterprets "compute constrained", consent given 2026-10-16), then the shared branch suffix.',
   'Shared branch suffix: options-and-card §2.2 text, with "model size" added to the quantity list and the URL of the reporting source asked for ("with that source\'s URL", "its source URL"), so it matches CONTRACT §2.2 `compute_open`; then the `sequential` sentence (CONTRACT §2.2), before "Return up to three source URLs."'])
sec('DEEPENER', 'P_DEEPENER(framerPath, path)', 'role qt-research, session model', 'verbatim + suffix', R('ORIG_DEEPENER'), R('P_DEEPENER("[framer path]", "[path]")'),
  ['Suffix: the shared branch suffix only (its own question already asks what massive parallelism would change).'])
sec('INTERP', 'P_INTERP(framerPath, path)', 'role qt-research, session model', 'verbatim + suffix', R('ORIG_INTERP'), R('P_INTERP("[framer path]", "[path]")'),
  ['Suffix: the INTERP-only quantity sentence (options-and-card §2.2, verbatim), then the shared branch suffix.'])
sec('OPTION CRITIC', 'P_OPTION_CRITIC(root, criteria, options)', 'role qt-bare, session model', 'edited in body', R('ORIG_OPTION_CRITIC'),
  R('P_OPTION_CRITIC("[root question]", "[criteria]", "[options: one JSON object per line with id, title, summary, root_link, compute_open, sequential]")'),
  [...diffLine('OPTION CRITIC:'),
   'Body text: criteria §8.1, plus the SAME/ADJACENT/ELSEWHERE definitions from substrate §5 inlined (criteria §8.1 points to them).',
   'Given an array, the function keeps only id, title, summary, root_link, compute_open and sequential of each option: no source_urls (options-and-card §2.2: it cannot check them), never scores or distance.'])
P(`#### OPTION CRITIC criteria\n\n\`CRIT_OPTION(branch)\` · names physical \`stakes, open, reshape\`; interp \`stakes, open, internals, reshape\`\n`)
P(`**Original, physical:**\n\n${block(R('ORIG_CRIT_OPTION_PHYSICAL'))}\n\n**Original, interp:**\n\n${block(R('ORIG_CRIT_OPTION_INTERP'))}\n`)
P(`**Final, physical:**\n\n${block(R('CRIT_OPTION("physical")'))}\n\n**Final, interp:**\n\n${block(R('CRIT_OPTION("interp")'))}\n`)
P(`**Diff and notes:**\n\n${[...diffLine('OPTION CRITIC criteria'),
  'stakes and internals: criteria §8.1, verbatim.',
  'open: criteria §8.1 (the version for branches held to the compute-lever test; both are, CONTRACT §0). Its reach clause "across the range one machine can run? One machine means up to 8 GPUs for $1,000: about 31 hours of an 8×H100 node at $31.92 per hour, or 250 H100-hours" and "within one machine\'s reach" / "everything one machine can reach" are replaced by "$1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours)" and "within that reach".',
  'open: the quantity list is per branch: physical keeps the criteria §8.1 list; interp names models, layers, features, prompts or seeds analysed (CONTRACT §2.2).',
  'reshape: the sequential-structure change, verbatim, the same for both branches. It reads the option\'s `sequential` field; the script floors it to 1 when `sequential` starts with "none", and it is not part of the total.'].map(n => `- ${n}`).join('\n')}\n`)
sec('PRODUCER', 'P_PRODUCER({idTitle, branchPath, path, dir, optionRecord, rootQuestion, framerPath, priceSheetText})', 'role qt-producer, session model', 'verbatim minus the words "one machine, up to 8 GPUs, " and the colon before them + suffix', R('ORIG_PRODUCER'),
  R('P_PRODUCER({idTitle: "[id] \\"[title]\\"", branchPath: "[branch path]", path: "[path]", dir: "[dir]", optionRecord: "[option record]", rootQuestion: "[root question]", framerPath: "[framer path]", priceSheetText: "[price sheet]"})'),
  [diffLine('PRODUCER')[0],
   'Seed idea (no branch file, framer or root): the first sentence reads `Read option [id] "[title]" in the option record below.`, the read list shrinks to `Read only pages you fetch and what you write under [dir]`, and the root question is `none`. Missing price sheet: `not available; read them from https://lambda.ai/pricing`.',
   'Suffix, in order: option record and root question (substrate §10); bounded read and record return (substrate §10, with "and what you write under [dir]" added so the producer may read its own pilot outputs); bases (cost §8.5, verbatim); cost form trimmed to the minimal-estimates decision (CONTRACT §0): time boxes are the default and need no work estimate, `need`, scenarios, optional lines, `instead_of` and yields are optional, GUESS only where a number drives the plan, every PROXY or GUESS the cost or result depends on names its measuring phase, and the price sheet\'s filesystem price is the GIVEN id fs_usd_gib_month, like budget_usd (CONTRACT §2.5); predictions and sources (substrate §10) with noise_rule, expected and scored_against (criteria §8.3); card fields (options-and-card §5.3) with the word caps of CONTRACT §2.5 in place of the report\'s "25 each (test_summary 45, limits 30)"; the hang guard (flow §2.4, as worded in the task); the price sheet (cost §8.5).',
   'predictions.expected is stated once (criteria §8.3 and options-and-card §5.3 both had it).',
   'Restructuring paragraph (the sequential-structure change, verbatim) after the sentence on sources: what `restructuring` holds, and what compute_axis, the predictions, anchor, test_summary and novelty.closest_prior hold on a restructured plan. The card-field list and caps gain restructuring.sequential_part 18 and restructuring.method 22.',
   'Not in the suffix: any word on which values halt, repair or score (H1).'])
sec('WRITER (side cell)', 'P_WRITER(root, option, planNoCost, menu)', 'role qt-bare, sonnet', 'edited in body', R('ORIG_WRITER'),
  R('P_WRITER("[root question]", "[option record]", "[plan record without cost]", "[menu: one line per entry as {id} name (value)]")'),
  [...diffLine('WRITER'),
   'Body text: substrate §10 with the cost §8.5 placeholder sentence in place of its "Numbers are fine, except ..." sentence. "GIVEN for the question\'s own budget and hardware" reads "budget and prices" (no hardware is given under the budget-only constraint). The return line names the one-line-per-sentence form, since the writer has no schema.'])
sec('DRAMATURG', 'P_DRAMATURG(items)', 'role qt-web, session model', 'edited in body', R('ORIG_DRAMATURG'), R('P_DRAMATURG("[items: one JSON object per line, each with its ref]")'),
  [...diffLine('DRAMATURG'),
   'Body text: substrate §10 and the first cost §8.5 sentence. Substrate\'s "A PLAN item passes if it restates the named record field" is replaced by the card-item sentence, because on the render path the card items are the plan\'s own fields (options-and-card §5.3). Cost §8.5\'s "For a sentence with computed numbers, check that it describes the menu quantity it uses" is left out: rendered cards carry no menu placeholders. The page_value sentence feeds the over-budget re-evaluation in `gate_decision` (CONTRACT §2.6).'])
sec('CRITIC', 'P_CRITIC(root, option, cardText, planFields, criteria)', 'role qt-bare, sonnet', 'edited in body', R('ORIG_CRITIC'),
  R('P_CRITIC("[root question]", "[option record]", "[card: one line per field as card:<field>: text]", "[plan fields]", "[criteria]")'),
  [...diffLine('CRITIC:'),
   'Body text: criteria §8.2, with ref in the CONTRACT §2.6 form (card:<field> or plan:<field path>) and the decides_by definition (criteria §8.2) in the body, so the criteria list names only scored criteria.',
   'The caller passes plan fields without cost, full_scale, files_read, compute_tested(_why), predictions.expected(_why), novelty.decides and novelty.searched (main\'s criticView), and never the option critic\'s output.'])
P(`#### CRITIC criteria\n\n\`CRIT_CARD(branch)\` · names physical \`stakes, lever, verifiable, open, reshape, baseline\`; interp adds \`internals\` after open\n`)
P(`**Original, physical:**\n\n${block(R('ORIG_CRIT_CARD_PHYSICAL'))}\n\n**Original, interp:**\n\n${block(R('ORIG_CRIT_CARD_INTERP'))}\n`)
P(`**Final, physical:**\n\n${block(R('CRIT_CARD("physical")'))}\n\n**Final, interp:**\n\n${block(R('CRIT_CARD("interp")'))}\n`)
P(`**Diff and notes:**\n\n${[...diffLine('CRITIC criteria'),
  'stakes, verifiable, open, internals: criteria §8.2, verbatim.',
  'lever: criteria §8.2, with condition (c) reading "the arms run on the same hardware and differ only in method" when restructuring.method is not none.',
  'reshape and baseline: the sequential-structure change, verbatim. baseline allows NA when restructuring.method is none; no other criterion allows NA under the current args (no branch is exempt).'].map(n => `- ${n}`).join('\n')}\n`)

P('## Part 2. New prompts\n')
sec('OVERLAP judge (S1b)', 'P_OVERLAP(roots)', 'role qt-bare, sonnet', 'new (substrate §10)', null,
  R('P_OVERLAP([1,2,3,4,5].map(i => ({id: `R${i}`, question: `[question ${i}]`})))'),
  ['Substrate text, with "Here are five questions" replaced by the actual count (a generator can fail), the id: question line form, and "in a few words" replaced by "in at least three words" (the OVERLAP record requires three).'])
sec('DEDUP judge (S4)', 'P_DEDUP(lines)', 'role qt-bare, sonnet', 'new (substrate §10)', null,
  R('P_DEDUP(["[key]: [title]. [summary]", "..."])'),
  ['Substrate text with the grouping rule from flow §2.10 / INTEGRATED §3 ("ask the same question of the same kind of system"), and the line form main builds (`key: title. summary`) with an example key, since keys contain colons.'])
sec('PRICE SHEET', 'P_PRICE_SHEET()', 'role qt-web, sonnet', 'new (cost §8.3, verbatim)', null, R('P_PRICE_SHEET()'), [])
sec('EXTRACT (producer fallback; replay)', 'P_EXTRACT(producerPath, dir)', 'role qt-extract, pinned sonnet', 'new (substrate §10 + cost §8.5)', null,
  R('P_EXTRACT("[producer path]", "[dir]")'),
  ['Substrate text plus the cost §8.5 addition, verbatim, except that "Read [producer path] and nothing else" admits the run outputs producer.md names under [dir], so MEASURED numbers can carry their output line.'])
sec('REPAIR (cost expressions)', 'P_REPAIR_EXPR(errors, record)', 'role qt-bare, sonnet', 'new (substrate §10)', null,
  R('P_REPAIR_EXPR(["[error 1]", "[error 2]"], "[record]")'),
  ['Substrate text with "could not be evaluated" widened to "failed a check" (the repair also runs on gate_ref, quote and stated-total errors), "input ids" renamed to the record\'s ids (numbers, rates, lines) and budget_usd, the expression grammar listed, and the return form named.'])
sec('REPAIR (card fields)', 'P_REPAIR_FIELDS(fields, caps, record)', 'role qt-bare, sonnet', 'new (options-and-card §5.3)', null,
  R('P_REPAIR_FIELDS({"[field path]": "[text]"}, {"[field path]": "[cap]"}, "[record]")'),
  ['Report text with a word cap per field (fields have different caps), "and every [source id]" added so citations survive, and the return form named.'])

P('## Part 3. Role files\n\nWritten from `ROLE_FILES` to `/home/hal/stage/.claude/agents/<name>.md`.\n')
for (const [name, md] of Object.entries(R('ROLE_FILES'))) P(`### ${name}\n\n\`\`\`markdown\n${md}\`\`\`\n`)
P('`qt-bare` declares `tools: []`. Claude Code 2.1.301 parses an explicit empty list to no tools; an omitted `tools:` would inherit every tool. It refuses a zero-tool spawn only when a declared tool fails to resolve, which an empty list cannot trigger. Not verified by a live call: the Stage 1 probe must confirm a `qt-bare` agent still returns its schema. If it cannot, use `tools: Read` (CONTRACT §3); the body sentence does the rest.\n')

P('## Part 4. `PROMPT_DIFF` (as the script carries it)\n\n' + block(R('PROMPT_DIFF')) + '\n')
const md = out.join('\n')
if (/[–—]/.test(md)) throw new Error('dash in PROMPTS.md')
fs.writeFileSync(path.join(ROOT, 'PROMPTS.md'), md)
console.log('PROMPTS.md', md.length, 'bytes', md.split('\n').length, 'lines')
