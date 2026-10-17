// prompts.test.js: prompt text, criteria strings, role files (CONTRACT §3 prompts.js).
// One block scope so these names cannot collide with other test files in the shared vm context.
{
  // the user's originals as CONTEXT.md gives them, and EX1/EX2 as the original script gives them (copied, no fixture)
  const WANT = {
    ORIG_PLAYWRIGHT: "Here are two questions someone asked. [EX1] [EX2] Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].",
    ORIG_GUEST: "You are Harry James Potter-Evans-Verres from Harry Potter and the Methods of Rationality. You test everything, look for exploits in how the world works, and light up when brute force becomes possible. Here are two questions someone asked. [EX1] [EX2] Write two new questions in the same voice, about subjects orthogonal to these and to each other. Return JSON: [{question}].",
    ORIG_FRAMER: "[question] Don't answer until you've defined and thought about the problem as thoroughly as possible without answering. Start by relaying your current understanding, making some predictions, and then proceed. Cite a URL for every factual claim. Write everything to [path]. End with one line, VERDICT: COMPUTE-BOUND or VERDICT: NOT COMPUTE-BOUND, and return JSON: {verdict}.",
    ORIG_WIDENER: "Read [framer path]. What sorts of related problems are compute constrained? Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].",
    ORIG_DEEPENER: "Read [framer path]. Go deeper on that: where does the compute go, and what would massive parallelism change? List the concrete options it opens up. Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].",
    ORIG_INTERP: "Read [framer path]. Are there mech interp (Goodfire style?) solutions to these sorts of problems? Cite a URL for every factual claim. Write to [path]. Return JSON: [{id, title, summary}].",
    ORIG_OPTION_CRITIC: "Score each option 1-5 on each criterion, or \"cannot assess\". Criteria: [criteria]. Options: [options]. Return JSON: [{id, scores, total}].",
    ORIG_CRIT_OPTION_PHYSICAL: "scientific stakes; compute is the main limit; results checkable against a reference; not already solved by existing tools",
    ORIG_CRIT_OPTION_INTERP: "scientific stakes; model weights or activations are accessible; internals could reveal what outputs can't; results checkable against known physics",
    ORIG_PRODUCER: "Read option [id] \"[title]\" in [branch path]. I'm thinking about running something on this with up to $1,000 of GPU credit: one machine, up to 8 GPUs, at Lambda's on-demand prices (https://lambda.ai/pricing). Make it concrete: what to build, the baseline, how to check it's right, and the cost. Cite a URL for every factual claim. Write to [path].",
    ORIG_WRITER: "Using only [producer path] and [branch path], write a 150-250 word explanation of this idea. Add no new claims. Invent no terms. Numbers are fine. Keep every sentence to 20 words or fewer. Put a source URL after every factual sentence. Write to [path].",
    ORIG_DRAMATURG: "Read [write-up path]. For every core claim, fetch the cited source and check it supports the claim. A derived number passes only if every input is cited and the arithmetic is shown. Reject if any core claim is uncited, unsupported, or its source is unreachable. Return JSON: {result: PASS or REJECT, reasons}.",
    ORIG_CRITIC: "Read [write-up path]. Score 1-5 on each criterion, quoting the sentence behind each score, or \"cannot assess\". Criteria: [criteria]. Also give compute payoff: the smallest budget that yields a reportable result at Lambda's on-demand prices (https://lambda.ai/pricing): $250, $500, $1,000, or none. Return JSON.",
    ORIG_CRIT_CARD_PHYSICAL: "scientific stakes; parallel restructuring; measurable speedup against a baseline; verifiable correctness; novelty against existing tools",
    ORIG_CRIT_CARD_INTERP: "scientific stakes; model access; what internals reveal that outputs don't; verifiable correctness; novelty",
    EX1_TEXT: "What limits the development of better crystal foundation models like for battery generation, is it a major blocker at some level, at could that be fixed with a shit ton of GPU parallelism?",
    EX2_TEXT: "Can scientific paper reviews (maybe specifically ML, DL, data-driven papers) be automated with highly scoped, small subagents following the AISLE model: many open-source models, since they have different blind spots, with tasks scoped to known failure modes like biases, factual reproduction errors, 'do these authors/papers exist' errors and overclaims, including building the suggested experiments and variations and running them on GPUs? Is compute a major blocker at some level, could a shit ton of GPU parallelism fix it?",
  }
  const REMOVED = 'one machine, up to 8 GPUs, '
  const fill = (s, m) => Object.entries(m).reduce((t, [k, v]) => t.split(k).join(v), s)
  // the build's forbidden constructs (build.js FORBIDDEN)
  const FORBIDDEN = [/\bimport\s/, /\bexport\s(?!const meta)/, /\brequire\(/, /module\.exports/, /Math\.random\(/, /Date\.now\(/, /new Date\(\s*\)/]
  // H1: words a generator must never see
  const H1 = /\b(halt\w*|reject\w*|scor(e|es|ed|ing)|eligib\w*)\b/i
  const labels = s => [...s.matchAll(/^([a-z_]+): /gm)].map(m => m[1])

  const A = {
    question: 'Does a wider sampling budget change the crystal ranking?', path: '/run/seed-9/R2/physical-widener.md',
    framerPath: '/run/seed-9/R2/framer.md', dir: '/run/seed-9/R2/physical/0badf00d', branchPath: '/run/seed-9/R2/physical-widener.md',
    producerPath: '/run/seed-9/R2/physical/0badf00d/producer.md', root: 'What limits crystal foundation models at scale?',
  }
  const OPTION = { id: 'W7', title: 'Ensemble width for phase stability', summary: 'Vary ensemble members and measure stability error.', root_link: 'bears on the scaling part', compute_open: 'ensemble members; reported up to 64 https://example.org/a; unknown above', sequential: 'each member steps through time in order; copies fill the GPU', source_urls: ['https://hidden.example.org/only-in-urls'] }
  const PLAN = { option_title: 'Ensemble width for phase stability', question: 'Does stability error keep falling past 64 members?', numbers: [{ id: 'box_h', basis: 'DESIGN', value: 20 }] }
  const SHEET = '{"read_at":"2026-10-16","instances":[{"gpu":"H100 SXM","n_gpus":8,"per_gpu_usd_h":3.99}]}'
  const PROD = { idTitle: `${OPTION.id} "${OPTION.title}"`, branchPath: A.branchPath, path: A.producerPath, dir: A.dir, optionRecord: OPTION, rootQuestion: A.root, framerPath: A.framerPath, priceSheetText: SHEET }
  const SEED = { idTitle: '1 "Sweep MD thermostat seeds"', branchPath: null, path: '/run/seed-9/seed/idea/1/producer.md', dir: '/run/seed-9/seed/idea/1', optionRecord: { id: '1', title: 'Sweep MD thermostat seeds' }, rootQuestion: null, framerPath: null, priceSheetText: null }
  const MENU = [{ id: 'planned_usd', name: 'planned spend', value: 557.2, tag: '=' }, { id: 'axis_span', name: 'compute axis span', value: 16, tag: '=' }]
  const ITEMS = [{ ref: 'card:question', text: PLAN.question, sources: [] }, { ref: 'num:tput', name: 'throughput', value: 5000, quote: '5,000 steps', url: 'https://example.org/t' }]
  const CARD = 'card:question: Does stability error keep falling past 64 members?\ncard:if_lever: Error falls 20% from 64 to 1,024 members.'

  // every prompt function with sample arguments, and the string arguments each output must contain
  const CALLS = {
    P_PLAYWRIGHT: [['crystal ex one', 'review ex two'], ['crystal ex one', 'review ex two']],
    P_GUEST: [['crystal ex one', 'review ex two'], ['crystal ex one', 'review ex two']],
    P_REASK: [[[{ id: 'R1', question: 'first kept root?' }, { id: 'R3', question: 'second kept root?' }]], ['first kept root?', 'second kept root?']],
    P_OVERLAP: [[[{ id: 'R1', question: 'root one?' }, { id: 'R2', question: 'root two?' }]], ['R1: root one?', 'R2: root two?']],
    P_FRAMER: [[A.question, A.path], [A.question, A.path]],
    P_WIDENER: [[A.framerPath, A.path], [A.framerPath, A.path]],
    P_DEEPENER: [[A.framerPath, A.path], [A.framerPath, A.path]],
    P_INTERP: [[A.framerPath, A.path], [A.framerPath, A.path]],
    P_DEDUP: [[['R1:physical:W1: Title one. Summary one.', 'R2:interp:I4: Title two. Summary two.']], ['R1:physical:W1: Title one. Summary one.', 'R2:interp:I4: Title two. Summary two.']],
    P_OPTION_CRITIC: [[A.root, 'stakes: s\nopen: o', [OPTION]], [A.root, 'stakes: s\nopen: o', OPTION.title, OPTION.summary, OPTION.root_link, OPTION.compute_open, OPTION.sequential]],
    P_PRODUCER: [[PROD], [PROD.idTitle, PROD.branchPath, PROD.path, PROD.dir, PROD.rootQuestion, PROD.framerPath, PROD.priceSheetText, OPTION.compute_open]],
    P_EXTRACT: [[A.producerPath, A.dir], [A.producerPath, A.dir]],
    P_REPAIR_EXPR: [[['parse at lines.l2.hours: unexpected )'], PLAN], ['parse at lines.l2.hours: unexpected )', PLAN.question]],
    P_REPAIR_FIELDS: [[{ 'predictions.if_lever': 'W7 error falls in E2' }, { 'predictions.if_lever': 22 }, PLAN], ['predictions.if_lever (at most 22 words): W7 error falls in E2', PLAN.question]],
    P_WRITER: [[A.root, OPTION, PLAN, MENU], [A.root, OPTION.title, PLAN.question, '{planned_usd} planned spend (557.2)']],
    P_DRAMATURG: [[ITEMS], ['card:question', 'num:tput', '5,000 steps']],
    P_CRITIC: [[A.root, OPTION, CARD, PLAN, 'stakes: s\nlever: l'], [A.root, OPTION.title, CARD, PLAN.question, 'stakes: s\nlever: l']],
    P_PRICE_SHEET: [[], ['https://lambda.ai/pricing', 'https://docs.lambda.ai/public-cloud/billing/']],
  }
  const OUT = Object.fromEntries(Object.entries(CALLS).map(([name, [args]]) => [name, globalThis[name] ? globalThis[name](...args) : undefined]))
  const GENERATORS = ['P_PLAYWRIGHT', 'P_GUEST', 'P_FRAMER', 'P_WIDENER', 'P_DEEPENER', 'P_INTERP', 'P_PRODUCER']
  const ORIG_NAMES = Object.keys(WANT).filter(k => k.startsWith('ORIG_'))
  const ORIGS = { ORIG_PLAYWRIGHT, ORIG_GUEST, ORIG_FRAMER, ORIG_WIDENER, ORIG_DEEPENER, ORIG_INTERP, ORIG_OPTION_CRITIC, ORIG_CRIT_OPTION_PHYSICAL, ORIG_CRIT_OPTION_INTERP, ORIG_PRODUCER, ORIG_WRITER, ORIG_DRAMATURG, ORIG_CRITIC, ORIG_CRIT_CARD_PHYSICAL, ORIG_CRIT_CARD_INTERP }
  const CRITS = [CRIT_OPTION('physical'), CRIT_OPTION('interp'), CRIT_CARD('physical'), CRIT_CARD('interp')]
  // every string the module produces or holds
  const ALL = [...Object.values(OUT), P_PRODUCER(SEED), P_GUEST(EX1_TEXT, EX2_TEXT) + ' ' + P_REASK(['x?']), ...CRITS, ...Object.values(ORIGS), EX1_TEXT, EX2_TEXT, PROMPT_DIFF, ...Object.values(ROLE_FILES)]

  test('prompts: every contract export exists with the right type', () => {
    for (const name of Object.keys(CALLS)) assert.equal(typeof globalThis[name], 'function', name)
    assert.equal(typeof CRIT_OPTION, 'function')
    assert.equal(typeof CRIT_CARD, 'function')
    for (const v of [PROMPT_DIFF, EX1_TEXT, EX2_TEXT, ...Object.values(ORIGS)]) assert.equal(typeof v, 'string')
    assert.equal(typeof ROLE_FILES, 'object')
    assert.deepEqual(ORIG_NAMES.sort(), Object.keys(ORIGS).sort())
  })

  test('prompts: each P_ returns one string containing each of its string arguments', () => {
    for (const [name, [, want]] of Object.entries(CALLS)) {
      assert.equal(typeof OUT[name], 'string', name)
      for (const w of want) assert.ok(OUT[name].includes(w), `${name} lacks ${JSON.stringify(w)}`)
      assert.ok(!/undefined|\[object Object\]/.test(OUT[name]), `${name} has undefined or [object Object]`)
    }
  })

  test('prompts: ORIG_ constants and EX texts equal CONTEXT.md and the original script byte for byte', () => {
    for (const k of ORIG_NAMES) assert.equal(ORIGS[k], WANT[k], k)
    assert.equal(EX1_TEXT, WANT.EX1_TEXT)
    assert.equal(EX2_TEXT, WANT.EX2_TEXT)
  })

  test('prompts: PLAYWRIGHT and GUEST are the originals exactly; the re-ask is only appended', () => {
    const ex = { '[EX1]': `"${EX1_TEXT}"`, '[EX2]': `"${EX2_TEXT}"` }
    assert.equal(P_PLAYWRIGHT(EX1_TEXT, EX2_TEXT), fill(ORIG_PLAYWRIGHT, ex))
    assert.equal(P_GUEST(EX1_TEXT, EX2_TEXT), fill(ORIG_GUEST, ex))
    assert.equal(P_REASK([{ id: 'R1', question: 'a?' }, 'b?']), 'Also make them orthogonal to these: "a?" "b?".')
  })

  test('prompts: FRAMER, WIDENER, DEEPENER, INTERP begin with the verbatim original and add a suffix', () => {
    const fp = { '[framer path]': A.framerPath, '[path]': A.path }
    assert.ok(OUT.P_FRAMER.startsWith(fill(ORIG_FRAMER, { '[question]': A.question, '[path]': A.path }) + ' '))
    assert.ok(OUT.P_WIDENER.startsWith(fill(ORIG_WIDENER, fp) + ' '))
    assert.ok(OUT.P_DEEPENER.startsWith(fill(ORIG_DEEPENER, fp) + ' '))
    assert.ok(OUT.P_INTERP.startsWith(fill(ORIG_INTERP, fp) + ' '))
    assert.ok(OUT.P_FRAMER.includes('compute_signals'))
    for (const n of ['P_WIDENER', 'P_DEEPENER', 'P_INTERP']) for (const f of ['root_link', 'compute_open', '"settled:"', 'heading label', 'Return sequential:', '"none:"']) assert.ok(OUT[n].includes(f), `${n} lacks ${f}`)
    // the sequential sentence sits after the compute_open sentence and before the source URLs
    for (const n of ['P_WIDENER', 'P_DEEPENER', 'P_INTERP']) assert.ok(/or "none"\. Return sequential: [^]*independent pieces\. Return up to three source URLs\./.test(OUT[n]), n)
    // both definition sentences are WIDENER-only, in order; the quantity sentence is INTERP-only
    const def = 'Count a related problem as compute constrained when it is still open'
    const def2 = 'Also count a problem whose answer takes long because its steps run one after another, even where more hardware would not change the answer, only how soon it arrives.'
    assert.ok(OUT.P_WIDENER.includes(def) && !OUT.P_DEEPENER.includes(def) && !OUT.P_INTERP.includes(def))
    assert.ok(OUT.P_WIDENER.includes(`mark the second kind settled in compute_open. ${def2} For each option`) && !OUT.P_DEEPENER.includes(def2) && !OUT.P_INTERP.includes(def2))
    const iq = 'models, layers, features, prompts or seeds analysed'
    assert.ok(OUT.P_INTERP.includes(iq) && !OUT.P_WIDENER.includes(iq) && !OUT.P_DEEPENER.includes(iq))
  })

  // integration fix 13c: the colon before the removed words goes too ("GPU credit at Lambda's"); 13b: the bounded read
  // admits what the producer writes under [dir]
  test('prompts: PRODUCER is the original minus exactly ": one machine, up to 8 GPUs,", then the suffix', () => {
    assert.equal(ORIG_PRODUCER.split(`: ${REMOVED}`).length, 2, 'the removed words occur once in the original, after a colon')
    const head = fill(ORIG_PRODUCER.replace(`: ${REMOVED}`, () => ' '), { '[id] "[title]"': PROD.idTitle, '[branch path]': PROD.branchPath, '[path]': PROD.path })
    assert.ok(OUT.P_PRODUCER.startsWith(head + ' '), 'verbatim head')
    for (const p of [OUT.P_PRODUCER, P_PRODUCER(SEED)]) {
      assert.ok(!p.includes('one machine') && !p.includes('8 GPUs'), 'no one-machine wording')
      assert.ok(!/(in|only|question:|run:) null\b|undefined/.test(p), 'no null or undefined fill-ins')
    }
    // bounded read, hang guard, card fields, price sheet
    for (const s of [
      `Read only ${A.branchPath}, ${A.framerPath}, pages you fetch and what you write under ${A.dir}; write only under ${A.dir}.`,
      "up to $1,000 of GPU credit at Lambda's on-demand prices (https://lambda.ai/pricing).",
      'Run every local command under timeout. Start no new local run 45 minutes after you begin; if a run you need is unfinished by then, give its inputs basis GUESS with measured_by naming the phase that measures it. Local runs share a 4-core machine with other producers.',
      'predictions.noise_rule', 'predictions.expected', 'scored_against', 'novelty.prior_max_level', 'novelty.searched', 'test_summary 45',
      'that you rely on. In restructuring, sequential_part is the part of this computation', 'nearest published parallel version of this computation. Write the record\'s card fields',
      'limits, restructuring.sequential_part, restructuring.method) for a reader', 'restructuring.sequential_part 18, restructuring.method 22)',
      `${A.dir}/pilot/`, `Lambda's prices as read at the start of this run: ${SHEET}.`,
    ]) assert.ok(OUT.P_PRODUCER.includes(s), `producer lacks ${s.slice(0, 50)}`)
    const seed = P_PRODUCER(SEED)
    assert.ok(seed.startsWith('Read option 1 "Sweep MD thermostat seeds" in the option record below.'))
    assert.ok(seed.includes('Read only pages you fetch and what you write under /run/seed-9/seed/idea/1; write only under /run/seed-9/seed/idea/1.'))
    assert.ok(seed.includes('read them from https://lambda.ai/pricing'))
  })

  test('prompts: no em-dash or en-dash in any string', () => {
    for (const s of ALL) assert.ok(!/[–—]/.test(s), `dash in: ${s.slice(0, 60)}`)
  })

  test('prompts: generator prompts never name halts, rejects, scores or eligibility (H1)', () => {
    for (const n of GENERATORS) assert.ok(!H1.test(OUT[n]), `${n}: ${(OUT[n].match(H1) || [])[0]}`)
    assert.ok(!H1.test(P_PRODUCER(SEED)))
    assert.ok(!H1.test(P_REASK([{ id: 'R1', question: 'a?' }])))
  })

  // changed contract: reshape joins both option criteria sets, and reshape and baseline the card sets
  test('prompts: option criteria name exactly stakes, open, reshape (interp adds internals before reshape), reach is budget-only', () => {
    assert.deepEqual(labels(CRIT_OPTION('physical')), ['stakes', 'open', 'reshape'])
    assert.deepEqual(labels(CRIT_OPTION('interp')), ['stakes', 'open', 'internals', 'reshape'])
    assert.equal(CRIT_OPTION('physical').split('\n')[2], CRIT_OPTION('interp').split('\n')[3], 'reshape is the same for both branches')
    for (const b of ['physical', 'interp']) {
      const c = CRIT_OPTION(b)
      assert.ok(c.includes('$1,000 of Lambda on-demand GPU time (for scale, about 250 H100-hours)'), b)
      assert.ok(!/one machine|8 GPUs|8×H100|node-hours/.test(c), b)
    }
  })

  test('prompts: card criteria name stakes, lever, verifiable, open, reshape, baseline (interp adds internals after open)', () => {
    assert.deepEqual(labels(CRIT_CARD('physical')), ['stakes', 'lever', 'verifiable', 'open', 'reshape', 'baseline'])
    assert.deepEqual(labels(CRIT_CARD('interp')), ['stakes', 'lever', 'verifiable', 'open', 'internals', 'reshape', 'baseline'])
    const c = CRIT_CARD('physical')
    assert.ok(c.includes('(c) the varied quantity is bought with compute, not with more data, labels or people (when restructuring.method is not none: the arms run on the same hardware and differ only in method);'))
    assert.ok(!/speedup|extends_range/.test(c), 'the speedup sentence is gone')
    assert.ok(c.endsWith('NA when restructuring.method is none.'))
    assert.ok(OUT.P_CRITIC.includes('A phase that only reproduces a published number, or only measures throughput the question does not ask about, does not count.'))
  })

  test('prompts: no prompt or criterion keeps the one-machine wording', () => {
    for (const s of [...Object.values(OUT), P_PRODUCER(SEED), ...CRITS]) assert.ok(!/one machine|up to 8 GPUs/.test(s), s.slice(0, 60))
  })

  test('prompts: judges see what the contract allows and decide from the text', () => {
    assert.ok(!OUT.P_OPTION_CRITIC.includes('hidden.example.org'), 'option critic gets no source_urls')
    assert.ok(OUT.P_OPTION_CRITIC.includes('SAME') && OUT.P_OPTION_CRITIC.includes('ELSEWHERE') && OUT.P_OPTION_CRITIC.includes('There is no NA'))
    for (const n of ['P_OPTION_CRITIC', 'P_CRITIC', 'P_WRITER', 'P_DEDUP', 'P_OVERLAP', 'P_REPAIR_EXPR', 'P_REPAIR_FIELDS']) assert.ok(/do not use tools/.test(OUT[n]), n)
    assert.ok(OUT.P_CRITIC.includes('decides_by') && !/\$250|compute payoff/.test(OUT.P_CRITIC))
    for (const st of ['SUPPORTED', 'PARTIAL', 'UNSUPPORTED', 'CONTRADICTED', 'UNREACHABLE', 'page_value']) assert.ok(OUT.P_DRAMATURG.includes(st), st)
    assert.ok(!/derived number passes|Reject if/.test(OUT.P_DRAMATURG), 'the arithmetic and PASS rules are the script\'s')
    assert.ok(OUT.P_WRITER.includes('{planned_usd}') && OUT.P_WRITER.includes('$1,000') && !OUT.P_WRITER.includes('Write to'))
  })

  test('prompts: ROLE_FILES has the five roles, each frontmatter plus a one-paragraph body', () => {
    assert.deepEqual(Object.keys(ROLE_FILES).sort(), ['qt-bare', 'qt-extract', 'qt-producer', 'qt-research', 'qt-web'])
    const TOOLS = { 'qt-bare': '[]', 'qt-research': 'WebFetch, WebSearch, Bash, Read, Write, Edit', 'qt-producer': 'WebFetch, WebSearch, Bash, Read, Write, Edit', 'qt-web': 'WebFetch, Bash', 'qt-extract': 'Read' }
    for (const [name, md] of Object.entries(ROLE_FILES)) {
      const m = md.match(/^---\n([\s\S]*?)\n---\n\n([^\n]+)\n$/)
      assert.ok(m, `${name} is not frontmatter + body`)
      const fm = Object.fromEntries(m[1].split('\n').map(l => { const i = l.indexOf(': '); assert.ok(i > 0, `${name}: bad line ${l}`); return [l.slice(0, i), l.slice(i + 2)] }))
      assert.deepEqual(Object.keys(fm), name === 'qt-extract' ? ['name', 'description', 'tools', 'model'] : ['name', 'description', 'tools'], name)
      assert.equal(fm.name, name)
      assert.ok(fm.description.length > 20 && !/: |#/.test(fm.description), `${name}: description must be a plain YAML scalar`)
      assert.equal(fm.tools, TOOLS[name], name)
      if (name === 'qt-extract') assert.equal(fm.model, 'sonnet')
      // integration fix 13a: qt-research reads the files the prompt names and fetches web pages
      assert.ok(m[2].startsWith(name === 'qt-research' ? 'You read only the files the prompt names; fetch any web page you need. You return only the schema.'
        : 'You read only what the prompt names. You return only the schema.'), name)
      assert.equal(m[2].includes('Decide only from the text in the prompt. You have no tools.'), name === 'qt-bare', name)
    }
  })

  test('prompts: no forbidden construct in any prompt function or string', () => {
    const fns = [...Object.keys(CALLS).map(n => globalThis[n]), CRIT_OPTION, CRIT_CARD, ROLE_md, P_str, P_lines, P_branchSuffix]
    for (const s of [...fns.map(f => f.toString()), ...ALL]) for (const re of FORBIDDEN) assert.ok(!re.test(s), `${re} in ${s.slice(0, 60)}`)
  })

  test('prompts: PROMPT_DIFF lists every in-body edit', () => {
    for (const n of ['PRODUCER', 'OPTION CRITIC:', 'OPTION CRITIC criteria', 'CRITIC:', 'CRITIC criteria', 'DRAMATURG', 'WRITER', REMOVED.trim(), 'qt2-2', 'sequential', 'restructuring', 'reshape', 'baseline']) assert.ok(PROMPT_DIFF.includes(n), n)
  })
}
