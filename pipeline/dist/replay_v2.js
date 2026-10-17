export const meta = {
  name: 'question-tree-v2-replay',
  description: 'Stage-2 replay bound to the last run\'s stored outputs (no research re-run). Phase A: price sheet, qt-extract on each stored producer.md, G-plan, one repair, card, writer side cell. Phase B: dramaturg on every card and the planted set, critic, option critic x3 per branch, dedup and overlap judges, pick rules',
  phases: [
    { title: 'Price', detail: 'Lambda price sheet, unless args.price_sheet is given (A)' },
    { title: 'Extract', detail: 'qt-extract on each stored producer.md, G-plan, one cost repair (A)' },
    { title: 'Card', detail: 'card fields with one repair, cost block, menu, card; WRITER side cell on 10 picks (A)' },
    { title: 'Check', detail: 'DRAMATURG on every card and the planted cards; CRITIC on every card (B)' },
    { title: 'Options', detail: 'OPTION CRITIC x3 per stored branch; dedup and overlap judges; pick rules (B)' },
  ],
}
// ---- src/text.js ----
// ---------- text helpers (shared; pure) ----------
// Every helper takes any value and treats null/undefined as ''.

// Words: whitespace-separated tokens holding a letter or digit (a lone dash or symbol is not a word).
function txt_words(s) {
  return String(s ?? '').split(/\s+/).filter(w => /[\p{L}\p{N}]/u.test(w)).length
}

// Sentences. A terminator ends a sentence only when followed by whitespace (so decimals never split),
// and a period does not end one after a known abbreviation or before a lowercase letter.
const txt_ABBREV = new Set(['e.g', 'i.e', 'etc', 'vs', 'cf', 'al', 'approx', 'ca', 'fig', 'eq'])
function txt_sentences(s) {
  s = String(s ?? '')
  const out = []
  const re = /[.!?]+["'\u2019\u201d)\]]*(?=\s|$)/g
  let start = 0, m
  while ((m = re.exec(s))) {
    const end = m.index + m[0].length
    const before = s.slice(start, m.index).split(/\s+/).pop().toLowerCase()
    const next = s.slice(end).trimStart()[0]
    if (m[0][0] === '.' && (txt_ABBREV.has(before) || (next && /\p{Ll}/u.test(next)))) continue
    const sent = s.slice(start, end).trim()
    if (sent) out.push(sent)
    start = end
  }
  const rest = s.slice(start).trim()
  if (rest) out.push(rest)
  return out
}

// Titles compared for identity: lowercase, punctuation and quotes become spaces, spaces collapsed.
function txt_normalize_title(s) {
  return String(s ?? '').toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, ' ').replace(/\s+/g, ' ').trim()
}

// Title tokens for Jaccard, ported from the tokeniser the 0.4 threshold was calibrated with
// (flow.md M7, flow-work/strdedup.py): words of 3+ letters (hyphens kept), stopwords dropped, light suffix stemming.
const txt_STOP = new Set('a an the of and or for to in on by with from at as is are be into its it this that their them than vs per via using use based before after over under real large new'.split(' '))
function txt_tokens(s) {
  const out = new Set()
  for (const raw of String(s ?? '').match(/[A-Za-z][A-Za-z-]+/g) || []) {
    if (raw.length <= 2 || txt_STOP.has(raw.toLowerCase())) continue
    let w = raw.toLowerCase().replace(/kilometre/g, 'kilometer')
    const suf = w.length > 5 && ['ations', 'ation', 'ings', 'ing', 'ies', 'es', 's'].find(x => w.endsWith(x))
    if (suf) w = w.slice(0, -suf.length)
    out.add(w)
  }
  return out
}
function txt_jaccard(a, b) {
  const A = txt_tokens(a), B = txt_tokens(b)
  let inter = 0
  for (const t of A) if (B.has(t)) inter++
  return inter / Math.max(1, A.size + B.size - inter)
}

// Codes the pipeline coined (W11, E2, C2): one or two capitals then one or two digits, as whole tokens.
// Hardware names are whitelisted; text inside URLs is ignored. Returns every occurrence, in order.
const txt_HARDWARE = new Set(['A10', 'A100', 'H100', 'H200', 'B200', 'V100', 'L4', 'L40'])
function txt_coined_codes(s) {
  const t = String(s ?? '').replace(/(https?|file):\/\/[^\s)>\]]+/g, ' ').replace(/\bwww\.[^\s)>\]]+/g, ' ')
  return (t.match(/\b[A-Z]{1,2}\d{1,2}\b/g) || []).filter(c => !txt_HARDWARE.has(c))
}

// Numeric tokens, normalised by txt_norm_number. Digits inside codes (H100, E2) are not numbers;
// a leading minus counts only when it is not a range dash (10-20 gives 10 and 20).
function txt_numbers(s) {
  const re = /(?<![\p{L}\p{N}_.])[-\u2212]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?(?:[kKM](?![\p{L}\p{N}_]))?/gu
  return (String(s ?? '').match(re) || []).map(txt_norm_number)
}

function txt_has_digit(s) {
  return /\d/.test(String(s ?? ''))
}

// Record ids that occur in s as whole tokens (case-sensitive; letters, digits and _ bound a token).
function txt_contains_record_id(s, ids) {
  const t = String(s ?? '')
  const esc = x => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return [...new Set(ids)].filter(id => id && new RegExp(`(?<![A-Za-z0-9_])${esc(String(id))}(?![A-Za-z0-9_])`).test(t))
}

// One number as a canonical string: commas dropped, unicode minus, k = thousand, M = million, trailing zeros dropped.
// "1,979" -> "1979"; "20k" -> "20000"; "5.0" -> "5". Anything unparseable comes back trimmed.
function txt_norm_number(s) {
  const t = String(s ?? '').trim()
  const m = t.replace(/,/g, '').replace(/\u2212/g, '-').match(/^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)([kKM])?$/)
  if (!m) return t
  const n = Number(m[2] ? `${m[1]}e${m[2] === 'M' ? 6 : 3}` : m[1])
  return Number.isFinite(n) ? String(n) : t
}


// ---- src/schemas.js ----
// ---------- schemas (harness `schema` option: JSON Schema, root type object, required within properties) ----------
// Arrays of records are wrapped as {items: [...]}. Shallow everywhere except PLAN.

const SCHEMA_QUESTIONS = {
  type: 'object',
  properties: { items: { type: 'array', items: { type: 'object', properties: { question: { type: 'string' } }, required: ['question'] } } },
  required: ['items'],
}

const SCHEMA_OVERLAP = {
  type: 'object',
  properties: {
    pairs: {
      type: 'array',
      description: 'Pairs of root questions that share a subject. Empty if none do.',
      items: {
        type: 'object',
        properties: {
          a: { type: 'string', description: 'Root id.' },
          b: { type: 'string', description: 'Root id.' },
          shared_subject: { type: 'string', description: 'The subject both questions are about, in at least 3 words.' },
        },
        required: ['a', 'b', 'shared_subject'],
      },
    },
  },
  required: ['pairs'],
}

const SCHEMA_VERDICT = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['COMPUTE-BOUND', 'NOT COMPUTE-BOUND'] },
    compute_signals: {
      type: 'array',
      description: 'Zero to three subproblems where more parallel compute would change the answer.',
      items: {
        type: 'object',
        properties: { subproblem: { type: 'string' }, what_compute_buys: { type: 'string' } },
        required: ['subproblem', 'what_compute_buys'],
      },
    },
  },
  required: ['verdict', 'compute_signals'],
}

const SCHEMA_OPTIONS = {
  type: 'object',
  properties: {
    items: {
      type: 'array',
      description: 'One entry per concrete option named in the file. No notes, summaries, verdicts, or status items.',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'The heading label used for this option in the file.' },
          title: { type: 'string' },
          summary: { type: 'string' },
          root_link: { type: 'string', description: 'One sentence: which part of the root question this bears on, or "none".' },
          compute_open: {
            type: 'string',
            description: 'One sentence: the quantity more parallel compute would increase here (samples, ensemble members, resolution, model runs, model size, search width; for interpretability: models, layers, features, prompts, seeds analysed), where published measurements of its effect stop, with a source URL, and what is unknown above that. Or "settled: <what is known> <URL>". Or "none".',
          },
          sequential: {
            type: 'string',
            description: 'One or two sentences: the chain one answer waits on (what each step waits for, roughly how many steps), how many independent runs the answer needs, how much of one GPU one run keeps busy; whether the steps must run in order, and if not, what change would let them run at the same time, what must be true of the system for that to pay off, and the nearest source that tried it, with its URL. Or "none: <why the work already splits into independent pieces>".',
          },
          source_urls: { type: 'array', items: { type: 'string' }, description: 'At most 3.' },
        },
        required: ['id', 'title', 'summary', 'root_link', 'compute_open', 'sequential', 'source_urls'],
      },
    },
  },
  required: ['items'],
}

const SCHEMA_OPTION_SCORES = {
  type: 'object',
  properties: {
    items: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          distance: { type: 'string', enum: ['SAME', 'ADJACENT', 'ELSEWHERE'] },
          distance_reason: { type: 'string' },
          scores: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                criterion: { type: 'string' },
                value: { type: 'integer', minimum: 1, maximum: 5 },
                reason: { type: 'string' },
              },
              required: ['criterion', 'value', 'reason'],
            },
          },
        },
        required: ['id', 'distance', 'distance_reason', 'scores'],
      },
    },
  },
  required: ['items'],
}

const SCHEMA_DEDUP = {
  type: 'object',
  properties: {
    clusters: {
      type: 'array',
      description: 'Every option key in exactly one cluster; an option with no duplicate is a cluster of one.',
      items: {
        type: 'object',
        properties: {
          topic: { type: 'string', description: 'What the members ask, in at least 3 words.' },
          members: { type: 'array', items: { type: 'string' }, description: 'Option keys.' },
        },
        required: ['topic', 'members'],
      },
    },
  },
  required: ['clusters'],
}

const SCHEMA_PRICE_SHEET = {
  type: 'object',
  properties: {
    read_at: { type: 'string', description: 'The date the pages were fetched, ISO format.' },
    instances: {
      type: 'array',
      description: 'Every on-demand instance size listed.',
      items: {
        type: 'object',
        properties: {
          gpu: { type: 'string' },
          gpu_memory_gb: { type: 'number' },
          n_gpus: { type: 'integer' },
          per_gpu_usd_h: { type: 'number', description: 'US dollars per GPU per hour.' },
          page_text: { type: 'string', description: 'The text on the page that shows this price for this instance size.' },
        },
        required: ['gpu', 'gpu_memory_gb', 'n_gpus', 'per_gpu_usd_h', 'page_text'],
      },
    },
    filesystem: {
      type: 'object',
      properties: {
        usd_gib_month: { type: 'number', description: 'US dollars per GiB per month.' },
        page_text: { type: 'string' },
        example: { type: 'boolean', description: 'True if the page presents this price as an example.' },
      },
      required: ['usd_gib_month', 'page_text', 'example'],
    },
  },
  required: ['read_at', 'instances', 'filesystem'],
}

// PLAN: the producer's record (also the EXTRACT output). Card fields are read by people who have not seen the plan's files.
const SCHEMA_PLAN = (() => {
  const str = description => (description ? { type: 'string', description } : { type: 'string' })
  const strs = description => (description ? { type: 'array', items: { type: 'string' }, description } : { type: 'array', items: { type: 'string' } })
  const obj = (properties, required, description) => (description ? { type: 'object', properties, required, description } : { type: 'object', properties, required })
  const arr = (items, description) => (description ? { type: 'array', items, description } : { type: 'array', items })
  const card = words => `Card field: plain words for a reader who has not seen your files, at most ${words} words, no labels from your files; may cite a source as [source id].`
  // an expression is usually a string; a bare number is accepted too (cost_parse reads it through String())
  const expr = description => ({ anyOf: [{ type: 'string' }, { type: 'number' }], description: `${description} An expression: numbers, ids of numbers, rates and lines, budget_usd, fs_usd_gib_month (the price sheet's filesystem price per GiB-month), + - * / ^ ( ), ceil floor min max pow.` })
  const num = { type: 'number' }
  return obj({
    option_title: str('The picked option\'s title, copied as given.'),
    question: str(`One sentence. ${card(25)}`),
    hypothesis: str(`One sentence: the claim and its reason. ${card(22)}`),
    compute_axis: obj({
      quantity: str('The quantity this test varies that more parallel compute buys. If restructuring.method is not none: the chain length or the number of runs the answer needs.'),
      unit: str(),
      levels: arr(num, 'The values tested, in unit.'),
    }, ['quantity', 'unit', 'levels']),
    held_fixed: strs('Inputs kept the same across levels.'),
    predictions: obj({
      if_lever: str(`The measured outcome if compute is the lever. ${card(22)}`),
      if_not: str(`The measured outcome if it is not. ${card(25)}`),
      decision_rule: str('How the measured result decides between if_lever and if_not, with its threshold as a number.'),
      noise_rule: str('How a real difference is told from run-to-run noise (seeds, a confidence interval, paired evaluation).'),
      expected: { type: 'string', enum: ['if_lever', 'if_not', 'unsure'], description: 'The outcome you expect.' },
      expected_why: str('One sentence.'),
    }, ['if_lever', 'if_not', 'decision_rule', 'noise_rule', 'expected', 'expected_why']),
    compute_tested: { type: 'string', enum: ['yes', 'partly', 'no'], description: 'Does the test vary a quantity that more parallel compute buys?' },
    compute_tested_why: str(),
    scored_against: str('What the measured outcome is compared with to decide it is correct.'),
    arms: arr(obj({ id: str(), what: str() }, ['id', 'what'])),
    baseline: obj({ what: str(), value: { type: ['number', 'string'] }, source_id: str() }, ['what']),
    anchor: {
      description: 'A published number or an independent code the setup reproduces first, with its tolerance; or why there is none.',
      anyOf: [
        obj({
          what: str(card(24)),
          published_value: { type: ['number', 'string'] },
          tolerance: str(),
          source_id: str(),
          independent_code: str('An independent code the result is checked against, if any.'),
        }, ['what', 'tolerance']),
        obj({ absent_reason: str() }, ['absent_reason']),
      ],
    },
    checks: strs(),
    phases: arr(obj({
      id: str(),
      what: str(),
      stop_rule: str(),
      gate: obj({
        on: str('A number id.'),
        op: { type: 'string', enum: ['>=', '<='] },
        value: num,
        else: str('What happens if the condition fails.'),
      }, ['on', 'op', 'value', 'else'], 'Continue only if the measured number `on` satisfies `op value`.'),
    }, ['id', 'what']), 'In execution order.'),
    numbers: arr(obj({
      id: str('Lowercase letters, digits and _, starting with a letter, at most 31 characters. budget_usd and fs_usd_gib_month are reserved.'),
      name: str(),
      unit: str(),
      basis: {
        type: 'string',
        enum: ['CITED', 'PROXY', 'MEASURED', 'DERIVED', 'DESIGN', 'GUESS'],
        description: 'CITED: a source states it for this setting. PROXY: a source states it for a different setting. MEASURED: you ran it. DERIVED: computed by expr. DESIGN: a choice of this plan. GUESS: an estimate.',
      },
      value: { type: 'number', description: 'Required unless DERIVED.' },
      expr: expr('DERIVED only.'),
      source_id: str('CITED, PROXY.'),
      quote: str('CITED, PROXY: the exact source text that shows the value.'),
      page_setting: str('CITED, PROXY: the setting the source\'s number is for.'),
      differs_in: strs('PROXY (required), MEASURED (optional): how the source\'s or the pilot\'s setting differs from this plan\'s.'),
      command: str('MEASURED: the command run.'),
      output: str('MEASURED: the output file, under <dir>/pilot/.'),
      output_line: str('MEASURED: the output line that holds the value.'),
      machine: str('MEASURED: where it ran.'),
      rests_on: str('GUESS: what the guess is based on, in words; no URLs or source ids.'),
      measured_by: str('The id of the phase that measures this number.'),
    }, ['id', 'name', 'unit', 'basis'])),
    cost: obj({
      rates: arr(obj({
        id: str(), gpu: str(), gpu_memory_gb: num, n_gpus: { type: 'integer' },
        per_gpu_usd_h: { type: 'number', description: 'From the price sheet.' },
      }, ['id', 'gpu', 'n_gpus', 'per_gpu_usd_h'])),
      lines: arr(obj({
        id: str(),
        phase: str('A phase id.'),
        what: str(),
        kind: { type: 'string', enum: ['work', 'allotment', 'storage'], description: 'work: hours on a rate. allotment: time or dollars set aside for a stated purpose. storage: dollars.' },
        rate: str('A rate id (work, allotment).'),
        hours: expr('Hours on the rate (work, allotment); a time box when need is given.'),
        need: expr('The estimated work in hours when hours is a time box.'),
        usd: expr('Dollars (storage, or an allotment given in dollars).'),
        optional: { type: 'boolean' },
        instead_of: strs('Line ids this line is an alternative to.'),
        condition: str('When this line runs.'),
      }, ['id', 'phase', 'what', 'kind'])),
      scenarios: arr(obj({
        id: str(), what: str(),
        set: { type: 'object', additionalProperties: num, description: 'Number id to the value it takes in this scenario.' },
      }, ['id', 'what', 'set'])),
      yields: strs('Ids of numbers that say what the money buys.'),
      spend_cap_usd: { type: 'number', description: 'Your hard stop in dollars.' },
      total_stated: { type: 'number', description: 'Your own total in dollars.' },
    }, ['rates', 'lines', 'total_stated']),
    full_scale: arr(obj({
      id: str(), what: str(),
      usd: expr('Dollars.'),
      ratio_to: str('A number id to compare this run with.'),
    }, ['id', 'what', 'usd']), 'Runs the budget cannot buy.'),
    outside_budget: arr(obj({ what: str(), qty: num, unit: str() }, ['what', 'qty', 'unit']), 'Resources used that the budget does not pay for.'),
    restructuring: obj({
      sequential_part: str(`What one answer waits on step after step, and how many steps. ${card(18)}`),
      method: str(`Why those steps need not run in order and how the plan computes them at the same time; or "none". ${card(22)}`),
      condition: str('What must hold about this system for the method to pay off, and the cheap measurement that checks it.'),
      condition_phase: str('The id of the phase that makes that measurement before the main spend.'),
      baseline_sequential: str('The fastest sequential implementation the plan times, and how it is tuned.'),
      baseline_copies: str('Independent copies run side by side on the same GPUs, which the plan also times.'),
    }, ['sequential_part', 'method']),
    scope_gap: strs('What the budget cannot test about the option\'s claim.'),
    novelty: obj({
      closest_prior: str(`The published result that comes nearest to deciding between if_lever and if_not: what it measured and the largest amount of the compute quantity it used. ${card(30)}`),
      closest_source_id: str(),
      prior_max_level: { type: ['number', 'null'], description: 'That largest amount in compute_axis.unit, or null if it is not on the same axis.' },
      left_open: str(card(30)),
      decides: { type: 'string', enum: ['no', 'partly', 'yes'], description: 'Does closest_prior already decide the outcome at your compute levels?' },
      searched: { type: 'boolean', description: 'Did web search return results while you planned?' },
    }, ['closest_prior', 'left_open', 'decides', 'searched']),
    limits: strs(`What the result would not show. Card field: plain words, at most 30 words in all, no labels from your files.`),
    test_summary: str(card(45)),
    sources: arr(obj({
      id: str(), url: str(),
      quote: str('The exact sentence relied on.'),
      supports: str('What it supports in this plan.'),
    }, ['id', 'url', 'quote', 'supports'])),
    files_read: strs(),
  }, [
    'option_title', 'question', 'hypothesis', 'compute_axis', 'held_fixed', 'predictions', 'compute_tested', 'compute_tested_why',
    'scored_against', 'arms', 'baseline', 'anchor', 'checks', 'phases', 'numbers', 'cost', 'full_scale', 'outside_budget',
    'restructuring', 'scope_gap', 'novelty', 'limits', 'test_summary', 'sources', 'files_read',
  ])
})()

const SCHEMA_FINDINGS = {
  type: 'object',
  properties: {
    items: {
      type: 'array',
      description: 'One entry per item sent, with its ref unchanged.',
      items: {
        type: 'object',
        properties: {
          ref: { type: 'string', description: '"card:<field>", "src:<source id>", "num:<number id>" or "rate:<rate id>", as sent.' },
          status: { type: 'string', enum: ['SUPPORTED', 'PARTIAL', 'UNSUPPORTED', 'CONTRADICTED', 'UNREACHABLE'] },
          page_quote: { type: 'string', description: 'The text on the page this status rests on.' },
          note: { type: 'string' },
          page_value: { type: 'number', description: 'num and rate items: the value the page states.' },
        },
        required: ['ref', 'status', 'page_quote', 'note'],
      },
    },
  },
  required: ['items'],
}

const SCHEMA_CRITIQUE = {
  type: 'object',
  properties: {
    scores: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          criterion: { type: 'string' },
          value: { anyOf: [{ type: 'integer', minimum: 1, maximum: 5 }, { type: 'string', enum: ['NA'] }] },
          ref: { type: 'string', description: '"card:<field>" for the card field that decides the score, or "plan:<field path>" when no card field carries it.' },
          reason: { type: 'string' },
        },
        required: ['criterion', 'value', 'ref', 'reason'],
      },
    },
    decides_by: { type: 'string', description: 'A phase id, or "none".' },
    decides_by_reason: { type: 'string' },
  },
  required: ['scores', 'decides_by', 'decides_by_reason'],
}

const SCHEMA_REPAIR_FIELDS = {
  type: 'object',
  properties: {
    fields: { type: 'object', additionalProperties: { type: 'string' }, description: 'Field path to its rewritten text.' },
  },
  required: ['fields'],
}

const SCHEMA_REPAIR_EXPR = {
  type: 'object',
  properties: {
    numbers: {
      type: 'array',
      items: { type: 'object', properties: { id: { type: 'string' }, expr: { type: 'string' } }, required: ['id', 'expr'] },
    },
    lines: {
      type: 'array',
      items: {
        type: 'object',
        properties: { id: { type: 'string' }, hours: { type: 'string' }, usd: { type: 'string' }, need: { type: 'string' } },
        required: ['id'],
      },
    },
  },
  required: ['numbers', 'lines'],
}


// ---- src/cost.js ----
// ---------- cost: PLAN.numbers / cost / full_scale -> computed spend, headroom, gates, block, menu ----------
// Pure functions; the script computes every cost figure, the producer only supplies typed inputs.
// Reference behaviour: the design round's cost-sim/gplan.js and its six encodings (tests/fixtures/cost/).

const cost_LITERALS = [0, 0.5, 1, 2, 3, 4, 7, 8, 10, 12, 24, 30, 60, 100, 1000, 1024, 3600, 1e3, 1e6, 1e9, 1e12]
const cost_ARITY = { ceil: [1, 1], floor: [1, 1], min: [1, 99], max: [1, 99], pow: [2, 2] }
const cost_TAG = { CITED: 'c', PROXY: 'p', MEASURED: 'm', DERIVED: '=', DESIGN: 'd', GUESS: 'g' }
const cost_PREC = { '+': 1, '-': 1, '*': 2, '/': 2, neg: 3, '^': 4 }
const cost_OP = { '>=': '≥', '<=': '≤' }
// GIVEN ids, set by the question: a plan refers to them and may not define them (both tagged [q])
const cost_GIVEN = ['budget_usd', 'fs_usd_gib_month']
const cost_LEGEND = 'Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan\'s choice [g] guess [=] computed'
// a number in quoted page text: not inside a word ("H100", "v4"), optional k/K/M/B/T multiplier ("20k steps")
const cost_NUM_IN_TEXT = /(?<![A-Za-z0-9_.])[-−]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?(?:\s?[kKMBT](?![A-Za-z0-9]))?/g
const cost_SUFFIX = { k: 1e3, K: 1e3, M: 1e6, B: 1e9, T: 1e12 }

// ---------- expressions ----------
// Grammar: numbers; ids; + - * / ^ ( ); ceil floor min max pow. ^ is right-associative; unary minus binds looser than ^.
function cost_parse(src) {
  const s = String(src == null ? '' : src)
  const fail = (msg) => { throw { kind: 'parse', msg: `${msg} in "${s}"` } }
  if (!s.trim()) fail('empty expression')
  const re = /\s*(?:(\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)|([A-Za-z_][A-Za-z0-9_]*)|([-+*/^(),]))\s*/y
  const t = []
  while (re.lastIndex < s.length) {
    const at = re.lastIndex, m = re.exec(s)
    if (!m) fail(`unexpected "${s.slice(at).trim()[0]}"`)
    t.push(m[1] !== undefined ? { num: m[1] } : m[2] !== undefined ? { id: m[2] } : { op: m[3] })
  }
  let i = 0
  const peek = () => t[i] && t[i].op
  const expect = (op) => { if (peek() !== op) fail(`expected "${op}"`); i++ }
  const show = (x) => x.op || x.id || x.num
  function add() { let a = mul(); while (peek() === '+' || peek() === '-') { const op = t[i++].op; a = { op, a, b: mul() } } return a }
  function mul() { let a = unary(); while (peek() === '*' || peek() === '/') { const op = t[i++].op; a = { op, a, b: unary() } } return a }
  function unary() { if (peek() === '-') { i++; return { op: 'neg', a: unary() } } return power() }
  function power() { const a = atom(); if (peek() === '^') { i++; return { op: '^', a, b: unary() } } return a }
  function atom() {
    const x = t[i++]
    if (!x) fail('unexpected end')
    if (x.num !== undefined) return { num: Number(x.num), lit: x.num }
    if (x.op === '(') { const e = add(); expect(')'); return e }
    if (x.id === undefined) fail(`unexpected "${x.op}"`)
    if (peek() !== '(') return { id: x.id }
    if (!Object.prototype.hasOwnProperty.call(cost_ARITY, x.id)) fail(`unknown function "${x.id}"`)
    i++
    const args = [add()]
    while (peek() === ',') { i++; args.push(add()) }
    expect(')')
    const [lo, hi] = cost_ARITY[x.id]
    if (args.length < lo || args.length > hi) fail(`${x.id} takes ${lo === hi ? lo : `at least ${lo}`} argument(s)`)
    return { fn: x.id, args }
  }
  const e = add()
  if (i < t.length) fail(`unexpected "${show(t[i])}"`)
  return e
}

function cost_ev(a, val) {
  if (a.num !== undefined) return a.num
  if (a.id !== undefined) return val(a.id)
  if (a.fn) return Math[a.fn](...a.args.map((x) => cost_ev(x, val)))
  if (a.op === 'neg') return -cost_ev(a.a, val)
  const x = cost_ev(a.a, val), y = cost_ev(a.b, val)
  return a.op === '+' ? x + y : a.op === '-' ? x - y : a.op === '*' ? x * y : a.op === '/' ? x / y : Math.pow(x, y)
}

function cost_walk(a, f) { f(a); if (a.a) cost_walk(a.a, f); if (a.b) cost_walk(a.b, f); if (a.args) a.args.forEach((x) => cost_walk(x, f)) }
function cost_ids(a) { const s = new Set(); if (a) cost_walk(a, (n) => { if (n.id !== undefined) s.add(n.id) }); return s }

// Print an AST, substituting ids through sub(id); parentheses only where precedence needs them.
function cost_ast_str(a, sub, parentOp, right) {
  if (a.num !== undefined) return a.lit
  if (a.id !== undefined) return sub(a.id)
  if (a.fn) return `${a.fn}(${a.args.map((x) => cost_ast_str(x, sub)).join(', ')})`
  const p = cost_PREC[a.op]
  const s = a.op === 'neg' ? `-${cost_ast_str(a.a, sub, 'neg', true)}` : `${cost_ast_str(a.a, sub, a.op, false)} ${a.op} ${cost_ast_str(a.b, sub, a.op, true)}`
  const q = parentOp ? cost_PREC[parentOp] : 0
  const wrap = p < q || (p === q && parentOp !== 'neg' && (right ? parentOp !== '^' : parentOp === '^'))
  return wrap ? `(${s})` : s
}

// ---------- record index ----------
// Index ids, parse every expression once, and collect structural errors. Maps are prototype-free so any id string is safe.
function cost_prepare(plan) {
  const errors = [], log = []
  const err = (kind, where, msg) => errors.push({ kind, where, msg })
  const c = plan.cost || {}
  const N = Object.create(null), R = Object.create(null), L = Object.create(null), kinds = Object.create(null), ast = Object.create(null)
  const lists = [[plan.numbers || [], N, 'numbers'], [c.rates || [], R, 'rates'], [c.lines || [], L, 'lines']]
  for (const [list, map, what] of lists) for (const x of list) {
    if (cost_GIVEN.includes(x.id)) err('reserved', `${what}.${x.id}`, `${x.id} is set by the question; refer to it, do not define it`)
    else if (x.id in kinds) err('reserved', `${what}.${x.id}`, `id "${x.id}" is already used in ${kinds[x.id]}`)
    else { map[x.id] = x; kinds[x.id] = what }
  }
  const parse = (where, src) => {
    let a
    try { a = cost_parse(src) } catch (e) { if (e && e.kind === 'parse') return err('parse', where, e.msg); throw e }
    ast[where] = a
    cost_walk(a, (n) => {
      if (n.num !== undefined && !cost_LITERALS.includes(n.num)) log.push(`unlabelled constant ${n.lit} in ${where}`)
      if (n.id !== undefined && !cost_GIVEN.includes(n.id) && !(n.id in kinds)) err('undefined', where, `"${n.id}" is not a number, rate or line id`)
    })
  }
  const given = (x) => x !== undefined && x !== null && x !== ''
  for (const n of plan.numbers || []) {
    if (n.basis === 'DERIVED') parse(`numbers.${n.id}.expr`, n.expr)
    else if (typeof n.value !== 'number' || !Number.isFinite(n.value)) err('undefined', `numbers.${n.id}.value`, `${n.basis} number has no numeric value`)
  }
  for (const l of c.lines || []) {
    for (const k of ['hours', 'need', 'usd']) if (given(l[k])) parse(`lines.${l.id}.${k}`, l[k])
    if (l.rate) {
      if (!(l.rate in R)) err('undefined', `lines.${l.id}.rate`, `rate "${l.rate}" is not defined`)
      if (!given(l.hours)) err('undefined', `lines.${l.id}.hours`, 'a line with a rate needs hours')
    } else if (!given(l.usd)) err('undefined', `lines.${l.id}`, 'a line needs a rate and hours, or usd')
    for (const x of l.instead_of || []) if (!(x in L)) err('undefined', `lines.${l.id}.instead_of`, `line "${x}" is not defined`)
  }
  for (const f of plan.full_scale || []) {
    parse(`full_scale.${f.id}.usd`, f.usd)
    if (f.ratio_to && !(f.ratio_to in N)) err('undefined', `full_scale.${f.id}.ratio_to`, `"${f.ratio_to}" is not a number id`)
  }
  for (const s of c.scenarios || []) for (const k of Object.keys(s.set || {})) if (!(k in N)) err('undefined', `scenarios.${s.id}.set`, `"${k}" is not a number id`)
  for (const y of c.yields || []) if (!(y in N)) err('undefined', 'cost.yields', `"${y}" is not a number id`)
  for (const p of plan.phases || []) if (p.gate && !(p.gate.on in N)) err('gate_ref', `phases.${p.id}.gate.on`, `"${p.gate.on}" is not a number id`)
  // cycles through DERIVED numbers and line expressions
  const deps = (id) => [...cost_ids(ast[`numbers.${id}.expr`]), ...['hours', 'need', 'usd'].flatMap((k) => [...cost_ids(ast[`lines.${id}.${k}`])])]
  const state = Object.create(null)
  const visit = (id, path) => {
    if (state[id] === 2) return
    if (state[id] === 1) return err('cycle', id, `cycle: ${path.slice(path.indexOf(id)).concat(id).join(' -> ')}`)
    state[id] = 1
    for (const d of deps(id)) visit(d, path.concat(id))
    state[id] = 2
  }
  Object.keys(kinds).forEach((id) => visit(id, []))
  const P = { N, R, L, ast, lines: c.lines || [], phases: (plan.phases || []).map((p) => p.id) }
  return { P, errors, log }
}

// Ids reachable from roots through DERIVED expressions and line expressions (roots included).
function cost_ancestors(P, roots) {
  const seen = new Set(), todo = [...roots]
  while (todo.length) {
    const x = todo.pop()
    if (seen.has(x)) continue
    seen.add(x)
    for (const k of [`numbers.${x}.expr`, `lines.${x}.hours`, `lines.${x}.need`, `lines.${x}.usd`]) cost_ids(P.ast[k]).forEach((y) => todo.push(y))
  }
  return seen
}

const cost_is_alt = (l) => !!(l.instead_of && l.instead_of.length)
const cost_counts = (l, storageOut) => !cost_is_alt(l) && !l.optional && !(storageOut && l.kind === 'storage')
const cost_uncertain_basis = (n) => n.basis === 'GUESS' || n.basis === 'PROXY' || (n.basis === 'MEASURED' && (n.differs_in || []).length > 0)

function cost_load_bearing(plan) {
  const { P } = cost_prepare(plan)
  const c = plan.cost || {}
  const roots = P.lines.filter((l) => !cost_is_alt(l) && !l.optional).map((l) => l.id)
    .concat(c.yields || [], (plan.phases || []).filter((p) => p.gate).map((p) => p.gate.on))
  const anc = cost_ancestors(P, roots)
  const nums = (plan.numbers || []).filter((n) => anc.has(n.id))
  return { ids: nums.map((n) => n.id), uncertain: nums.filter(cost_uncertain_basis).map((n) => n.id) }
}

// ---------- prices ----------
const cost_gpu_norm = (s) => String(s || '').toLowerCase().replace(/nvidia/g, '').replace(/[^a-z0-9]/g, '')
const cost_rate_label = (r) => `${r.n_gpus}x ${r.gpu}${r.gpu_memory_gb ? ` ${r.gpu_memory_gb}GB` : ''}`

// 'ok' (stated price is on the sheet), 'corrected' (one sheet entry, other price), 'off' (no or ambiguous entry), 'unchecked' (no sheet)
function cost_sheet_match(r, sheet) {
  if (!sheet || !sheet.instances) return { status: 'unchecked', per: r.per_gpu_usd_h }
  const cands = sheet.instances.filter((x) => cost_gpu_norm(x.gpu) === cost_gpu_norm(r.gpu) && x.n_gpus === r.n_gpus &&
    (!r.gpu_memory_gb || x.gpu_memory_gb === r.gpu_memory_gb))
  if (cands.some((x) => Math.abs(x.per_gpu_usd_h - r.per_gpu_usd_h) < 0.005)) return { status: 'ok', per: r.per_gpu_usd_h }
  if (cands.length === 1) return { status: 'corrected', per: cands[0].per_gpu_usd_h }
  return { status: 'off', per: r.per_gpu_usd_h, n: cands.length }
}

// ---------- evaluation ----------
// One evaluation context: overrides (number id -> value) and whether time boxes stretch to their need.
function cost_ctx(P, ov, stretch) {
  const memo = Object.create(null), lm = Object.create(null)
  const ex = (l, k) => (`lines.${l.id}.${k}` in P.ast ? cost_ev(P.ast[`lines.${l.id}.${k}`], val) : null)
  const line = (l) => {
    if (l.id in lm) return lm[l.id]
    const box = ex(l, 'hours'), need = ex(l, 'need')
    const hours = stretch && box !== null && need !== null ? Math.max(box, need) : box
    const usd = l.rate ? hours * val(l.rate) : ex(l, 'usd')
    return (lm[l.id] = { box, need, hours, usd })
  }
  function val(id) {
    if (id in memo) return memo[id]
    let v
    if (id in ov) v = ov[id]
    else if (id === 'budget_usd') v = P.budget
    else if (id === 'fs_usd_gib_month') v = P.fs_rate
    else if (id in P.N) v = P.N[id].basis === 'DERIVED' ? cost_ev(P.ast[`numbers.${id}.expr`], val) : P.N[id].value
    else if (id in P.R) v = P.rate_usd[id]
    else v = line(P.L[id]).usd
    return (memo[id] = v)
  }
  return { val, line }
}

function cost_run(P, ov, stretch) {
  const c = cost_ctx(P, ov, stretch)
  const rows = P.lines.map((l) => ({ l, ...c.line(l) }))
  const planned = rows.filter((r) => cost_counts(r.l, P.storage_out)).reduce((s, r) => s + r.usd, 0)
  return { c, rows, planned }
}

// Smallest k in [1, 1000] with hit(k), by bisection in log space; null if hit(1000) is false.
function cost_bisect(hit) {
  if (!hit(1000)) return null
  if (hit(1)) return 1
  let lo = 1, hi = 1000
  for (let i = 0; i < 60; i++) { const m = Math.sqrt(lo * hi); if (hit(m)) hi = m; else lo = m }
  return hi
}

function cost_eval_plan(plan, given, opts) {
  opts = opts || {}
  const c = plan.cost || {}
  const { P, errors, log } = cost_prepare(plan)
  const flags = []
  const budget = given.budget_usd
  const name = (id) => { const n = P.N[id]; return n && n.name ? n.name : id }
  const label = (n) => `${n.name || n.id} [${cost_TAG[n.basis] || '?'}]`
  // rates, checked against the price sheet
  const rates = {}, rate_corrections = []
  if (!given.price_sheet) log.push('no price sheet given; rates not checked')
  for (const r of c.rates || []) {
    const m = cost_sheet_match(r, given.price_sheet)
    if (m.status === 'corrected') {
      rate_corrections.push({ id: r.id, stated: r.per_gpu_usd_h, sheet: m.per })
      flags.push(`rate ${cost_rate_label(r)}: plan says $${r.per_gpu_usd_h}/GPU-h, price sheet $${m.per}/GPU-h; sheet price used`)
    }
    if (m.status === 'off') flags.push(`rate ${cost_rate_label(r)} at $${r.per_gpu_usd_h}/GPU-h is not on the price sheet${m.n ? ` (${m.n} entries at other prices)` : ''}; kept as a guess`)
    rates[r.id] = r.n_gpus * m.per
  }
  for (const q of cost_check_quotes(plan)) {
    if (!q.ok) errors.push({ kind: 'quote', where: `numbers.${q.id}.quote`, msg: q.msg })
    else if (q.msg) log.push(`${q.id}: ${q.msg}`)
  }
  // fs_usd_gib_month is the price sheet's filesystem rate; without a sheet a plan that uses it cannot evaluate
  const fsRate = given.price_sheet && given.price_sheet.filesystem ? given.price_sheet.filesystem.usd_gib_month : undefined
  const fsUsed = Object.keys(P.ast).filter((w) => cost_ids(P.ast[w]).has('fs_usd_gib_month'))
  if (typeof fsRate !== 'number') for (const w of fsUsed) errors.push({ kind: 'undefined', where: w, msg: '"fs_usd_gib_month" is read from the price sheet, and none was given' })
  const ov = Object.assign(Object.create(null), opts.overrides || {})
  for (const k of Object.keys(ov)) if (!(k in P.N)) errors.push({ kind: 'undefined', where: 'opts.overrides', msg: `"${k}" is not a number id` })
  if (opts.scenario) {
    const s = (c.scenarios || []).find((x) => x.id === opts.scenario)
    if (s) Object.assign(ov, s.set)
    else errors.push({ kind: 'undefined', where: 'opts.scenario', msg: `scenario "${opts.scenario}" is not defined` })
  }
  // Under overrides or a scenario the plan is evaluated as a scenario is: time boxes stretch to their need.
  const stretch = !!opts.scenario || Object.keys(ov).length > 0
  const out = {
    ok: false, errors, numbers: {}, rates, rate_corrections, lines: [], planned: null, planned_with_options: null,
    alternatives: [], unallocated: null, scenarios: [], yields: [], gates: [], uncertain: [], full_scale: [], flags, log,
  }
  if (errors.some((e) => e.kind !== 'quote' && e.kind !== 'gate_ref')) return out
  Object.assign(P, { rate_usd: rates, budget, fs_rate: fsRate, storage_out: given.budget_covers_storage === false })

  const base = cost_run(P, ov, stretch)
  const counted = base.rows.filter((r) => cost_counts(r.l, P.storage_out))
  for (const n of plan.numbers || []) out.numbers[n.id] = base.c.val(n.id)
  if (fsUsed.length) out.numbers.fs_usd_gib_month = fsRate
  out.lines = base.rows.map((r) => ({
    id: r.l.id, phase: r.l.phase, kind: r.l.kind || 'work', hours: r.hours, usd: r.usd, optional: !!r.l.optional,
    instead_of: r.l.instead_of || [], time_box: !!r.l.rate && (r.need !== null || cost_ids(P.ast[`lines.${r.l.id}.hours`]).size === 0),
    need_h: r.need, margin: r.need ? r.box / r.need : null,
  }))
  out.planned = base.planned
  out.planned_with_options = base.rows.filter((r) => !cost_is_alt(r.l) && !(P.storage_out && r.l.kind === 'storage')).reduce((s, r) => s + r.usd, 0)
  out.alternatives = base.rows.filter((r) => cost_is_alt(r.l)).map((r) => ({
    line_id: r.l.id,
    total: base.planned - counted.filter((x) => r.l.instead_of.includes(x.l.id)).reduce((s, x) => s + x.usd, 0) + r.usd,
  }))
  out.unallocated = budget - base.planned
  const limit = Math.min(c.spend_cap_usd ?? Infinity, budget)
  const withOv = (set) => Object.assign(Object.create(null), ov, set)

  out.scenarios = (c.scenarios || []).map((s) => ({ id: s.id, what: s.what, total: cost_run(P, withOv(s.set), true).planned }))
  out.yields = (c.yields || []).map((y) => ({
    id: y, base: base.c.val(y),
    by_scenario: Object.fromEntries((c.scenarios || []).map((s) => [s.id, cost_ctx(P, withOv(s.set), true).val(y)])),
  }))

  for (const p of plan.phases || []) {
    const g = p.gate
    if (!g || !(g.on in P.N)) continue
    const base_value = base.c.val(g.on)
    const passes = g.op === '<=' ? base_value <= g.value : base_value >= g.value
    const uncut = cost_run(P, withOv({ [g.on]: g.value }), true).planned
    out.gates.push({ phase: p.id, on: g.on, op: g.op, value: g.value, base_value, passes, uncut_total_at_threshold: uncut, else: g.else })
    if (!passes) flags.push(`gate in ${p.id} fails at the plan's own value: ${name(g.on)} is ${cost_fmt_num(base_value)}, needs ${cost_OP[g.op]} ${cost_fmt_num(g.value)}; expected path: ${g.else || 'not stated'}`)
    if (uncut > budget) flags.push(`uncut plan at the ${p.id} gate threshold costs ${cost_fmt_usd(uncut)}, over budget; the plan relies on: ${g.else || 'not stated'}`)
  }

  // uncertain load-bearing inputs: measuring phase, spend so far, headroom
  const order = P.phases, idx = (ph) => order.indexOf(ph)
  const cum = (ph) => (idx(ph) < 0 ? null : counted.filter((r) => idx(r.l.phase) >= 0 && idx(r.l.phase) <= idx(ph)).reduce((s, r) => s + r.usd, 0))
  const anc = (l, k) => cost_ancestors(P, cost_ids(P.ast[`lines.${l.id}.${k}`]))
  const lb = new Set(cost_load_bearing(plan).uncertain)
  for (const n of (plan.numbers || []).filter((x) => lb.has(x.id))) {
    const v0 = base.c.val(n.id)
    const at = (k, d) => withOv({ [n.id]: d > 0 ? v0 * k : v0 / k })
    const spend = (k, d) => cost_run(P, at(k, d), true).planned
    const needSum = (k, d) => cost_run(P, at(k, d), false).rows.reduce((s, r) => s + (r.need || 0), 0)
    const up = spend(10, 1), dn = spend(10, -1)
    const dir = up > dn || (up === dn && needSum(10, 1) >= needSum(10, -1)) ? 1 : -1
    const k_budget = cost_bisect((k) => spend(k, dir) >= limit)
    const boxed = counted.filter((r) => r.need !== null && anc(r.l, 'need').has(n.id)).map((r) => r.l.id)
    const k_box = boxed.length ? cost_bisect((k) => cost_run(P, at(k, dir), false).rows.some((r) => boxed.includes(r.l.id) && r.need > r.box + 1e-9)) : null
    out.uncertain.push({
      id: n.id, basis: n.basis, value: v0, differs_in: n.differs_in || [], measured_by: n.measured_by || null,
      cum_spend_through_measured_by: n.measured_by ? cum(n.measured_by) : null, k_budget, k_box, dir: dir > 0 ? 'higher' : 'lower',
    })
    const dependent = counted.filter((r) => ['hours', 'usd', 'need'].some((k) => anc(r.l, k).has(n.id)) && idx(r.l.phase) >= 0)
    const first = dependent.reduce((m, r) => Math.min(m, idx(r.l.phase)), Infinity)
    if (!n.measured_by) flags.push(`${label(n)} is load-bearing and no phase measures it`)
    else if (idx(n.measured_by) < 0) flags.push(`${label(n)}: measuring phase ${n.measured_by} is not in the plan`)
    else if (idx(n.measured_by) > first) flags.push(`${label(n)} is measured in ${n.measured_by}, after spend that depends on it starts in ${order[first]}`)
    if (k_budget !== null && k_budget < 1.5) flags.push(`thin headroom: the budget is reached if ${name(n.id)} is ${cost_fmt_k(k_budget)}× ${dir > 0 ? 'higher' : 'lower'}`)
  }

  const stated = c.total_stated
  if (typeof stated === 'number') {
    const d = Math.min(Math.abs(base.planned - stated), Math.abs(out.planned_with_options - stated))
    if (d > Math.max(1, 0.02 * stated)) flags.push(`stated total ${cost_fmt_usd(stated)} differs from computed ${cost_fmt_usd(base.planned)}${Math.abs(out.planned_with_options - base.planned) > 0.005 ? ` (with options ${cost_fmt_usd(out.planned_with_options)})` : ''}`)
  }
  if (base.planned > budget) flags.push(`planned spend ${cost_fmt_usd(base.planned)} is over the ${cost_fmt_usd(budget)} budget (stated ${typeof stated === 'number' ? cost_fmt_usd(stated) : 'none'})`)
  // Constant-hours boxes are the default encoding (minimal estimates), so a big box without `need` is logged, not flagged.
  for (const r of counted) {
    const l = r.l, ph = (plan.phases || []).find((p) => p.id === l.phase)
    if (l.rate && r.need === null && cost_ids(P.ast[`lines.${l.id}.hours`]).size === 0 && !(ph && ph.stop_rule) && r.usd >= 0.1 * base.planned) {
      log.push(`time box ${l.id} (${cost_fmt_num(r.hours)} h, ${Math.round(100 * r.usd / base.planned)}% of plan): work not estimated`)
    }
  }

  out.full_scale = (plan.full_scale || []).map((f) => {
    const usd = cost_ev(P.ast[`full_scale.${f.id}.usd`], base.c.val)
    return { id: f.id, what: f.what, usd, multiple_of_budget: usd / budget, ratio_to_value: f.ratio_to ? usd / base.c.val(f.ratio_to) : null }
  })
  out.ok = errors.length === 0
  return out
}

// A CITED/PROXY value must appear as printed in its quote (commas, minus sign and k/M/B multipliers normalised).
// A missing quote is allowed by the schema; it is reported as not checked.
function cost_check_quotes(plan) {
  const out = []
  for (const n of plan.numbers || []) {
    if (n.basis !== 'CITED' && n.basis !== 'PROXY') continue
    if (!n.quote) { out.push({ id: n.id, ok: true, msg: 'no quote given; value not checked against page text' }); continue }
    const found = (String(n.quote).match(cost_NUM_IN_TEXT) || []).map((tok) => {
      const m = /^(.*?)\s?([kKMBT])$/.exec(tok)
      return Number(txt_norm_number(m ? m[1] : tok)) * (m ? cost_SUFFIX[m[2]] : 1)
    })
    const ok = found.some((x) => Math.abs(x - n.value) <= 1e-9 * Math.max(1, Math.abs(n.value)))
    out.push(ok ? { id: n.id, ok, msg: '' } : { id: n.id, ok, msg: `${n.value} does not appear in the quote "${n.quote}"; a value transformed from the page belongs in a DERIVED number` })
  }
  return out
}

// ---------- formatting ----------
function cost_commas(s) { const [i, f] = s.split('.'); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (f !== undefined ? `.${f}` : '') }
// 3 significant figures; commas below a million, M/B/T above
function cost_fmt_num(x) {
  if (typeof x !== 'number' || !Number.isFinite(x)) return String(x)
  const a = Math.abs(x), sign = x < 0 ? '-' : ''
  for (const [d, s] of [[1e12, 'T'], [1e9, 'B'], [1e6, 'M']]) if (a >= d) return `${sign}${Number((a / d).toPrecision(3))}${s}`
  const r = Number(a.toPrecision(3))
  return sign + (r >= 1000 ? cost_commas(String(r)) : String(r))
}
// dollars to cents below $10,000 (whole dollars without ".00"), 3 significant figures above
function cost_fmt_usd(x) {
  if (typeof x !== 'number' || !Number.isFinite(x)) return '$?'
  const a = Math.abs(x), sign = x < 0 ? '-' : ''
  return `${sign}$${a < 1e4 ? cost_commas(a.toFixed(2)).replace(/\.00$/, '') : cost_fmt_num(a)}`
}
// headroom factors to 2 significant figures
function cost_fmt_k(k) { return k < 10 ? k.toFixed(1) : k < 100 ? k.toFixed(0) : String(Number(k.toPrecision(2))) }
// 6 significant figures for shown working; exponent form from 1e7
function cost_fmt_exact(x) {
  if (typeof x !== 'number' || !Number.isFinite(x)) return String(x)
  const r = Number(x.toPrecision(6))
  return Math.abs(r) >= 1e7 ? r.toExponential().replace('+', '') : String(r)
}
const cost_index = (list) => Object.fromEntries((list || []).map((x) => [x.id, x]))
const cost_words = (s) => s.split(/\s+/).filter(Boolean).length

// The uncertain input whose measurement prices the plan: measured somewhere, tightest headroom first.
function cost_main_guess(ev) {
  const key = (u) => (u.k_budget === null ? Infinity : u.k_budget)
  return ev.uncertain.filter((u) => u.measured_by).reduce((m, u) => (!m || key(u) < key(m) ? u : m), null)
}
const cost_machine_hours = (ev, plan) => {
  const L = cost_index((plan.cost || {}).lines)
  return ev.lines.filter((r) => L[r.id].rate && !r.optional && !r.instead_of.length).reduce((s, r) => s + r.hours, 0)
}

// ---------- rendering ----------
function cost_render_block(ev, plan, given) {
  const c = plan.cost || {}, N = cost_index(plan.numbers), R = cost_index(c.rates), L = cost_index(c.lines), PH = cost_index(plan.phases)
  const usd = cost_fmt_usd, num = cost_fmt_num, budget = given.budget_usd
  const out = ['COST: computed by the pipeline from the plan\'s inputs', cost_LEGEND]
  const sec = (label, items) => (items.length ? items : ['none']).forEach((s, i) => out.push((i ? '' : label).padEnd(11) + s))
  const sheet = given.price_sheet
  const fs = ev.numbers.fs_usd_gib_month !== undefined ? ` · filesystem ${usd(ev.numbers.fs_usd_gib_month)}/GiB-month [q]` : ''
  sec('Budget', [`[q] ${usd(budget)} Lambda on-demand credit · storage ${given.budget_covers_storage === false ? 'not covered' : 'covered'} · tax ${given.budget_covers_tax ? 'covered' : 'not covered'} · ${sheet ? `prices read ${sheet.read_at}` : 'no price sheet'}${fs}`])
  if (ev.planned === null) { sec('Errors', ev.errors.map((e) => `${e.kind} at ${e.where}: ${e.msg}`)); return out.join('\n') }
  const { P } = cost_prepare(plan)
  const exprTag = (src) => (cost_ids(cost_parse(src)).size ? '=' : 'd')
  const rateTxt = (rid) => {
    const r = R[rid], m = cost_sheet_match(r, sheet), per = ev.rates[rid] / r.n_gpus
    return `${cost_rate_label(r)} ${r.n_gpus > 1 ? `${r.n_gpus}×${usd(per)}=` : ''}${usd(ev.rates[rid])}/h${m.status === 'off' ? ' [g]' : ''}`
  }
  const storageOut = given.budget_covers_storage === false
  const lineItem = (r) => {
    const l = L[r.id], what = l.what || (PH[l.phase] && PH[l.phase].what) || ''
    const notes = []
    if (r.need_h !== null) notes.push(`time box; need ${num(r.need_h)} h (margin ${r.margin.toFixed(2)}×)`)
    if (r.optional) notes.push('optional')
    if (storageOut && l.kind === 'storage') notes.push('outside the budget')
    const cost = l.rate ? `${rateTxt(l.rate)}  ${num(r.hours)} h [${exprTag(l.hours)}]` : `[${exprTag(l.usd)}]`
    return [l.phase, what, cost, usd(r.usd)].concat(notes).join('  ')
  }
  // Spend: one row per line, or per phase when the plan has more than 6 lines
  const spend = []
  const main = ev.lines.filter((r) => !r.instead_of.length)
  if (ev.lines.length <= 6) main.forEach((r) => spend.push(lineItem(r)))
  else {
    const counted = main.filter((r) => !r.optional && !(storageOut && L[r.id].kind === 'storage'))
    const phaseIds = [...new Set([...(plan.phases || []).map((p) => p.id), ...counted.map((r) => r.phase)])]
    for (const ph of phaseIds) {
      const rows = counted.filter((r) => r.phase === ph)
      if (!rows.length) continue
      const machines = [...new Set(rows.filter((r) => L[r.id].rate).map((r) => rateTxt(L[r.id].rate)))]
      const h = rows.filter((r) => L[r.id].rate).reduce((s, r) => s + r.hours, 0)
      const boxes = rows.filter((r) => r.need_h !== null).map((r) => `${r.id} need ${num(r.need_h)} h in a ${num(r.hours)} h box`)
      spend.push([ph, (PH[ph] && PH[ph].what) || '', machines.join('; '), h ? `${num(h)} h` : '', usd(rows.reduce((s, r) => s + r.usd, 0)), ...boxes].filter(Boolean).join('  '))
    }
    main.filter((r) => r.optional || (storageOut && L[r.id].kind === 'storage')).forEach((r) => spend.push(lineItem(r)))
  }
  const withOpt = Math.abs(ev.planned_with_options - ev.planned) > 0.005 ? ` · with options ${usd(ev.planned_with_options)}` : ''
  spend.push(`Planned ${usd(ev.planned)} · unallocated ${usd(ev.unallocated)}${withOpt}${c.spend_cap_usd != null ? ` · cap ${usd(c.spend_cap_usd)}` : ''}`)
  for (const a of ev.alternatives) {
    const l = L[a.line_id], r = ev.lines.find((x) => x.id === a.line_id)
    spend.push(`Instead of ${l.instead_of.join(', ')}: ${l.what || a.line_id}, ${l.rate ? `${rateTxt(l.rate)}, ${num(r.hours)} h, ` : ''}${usd(r.usd)} → plan ${usd(a.total)}`)
  }
  sec('Spend', spend)
  // Rests on: at most 4 uncertain inputs, tightest headroom first; each gate goes with the input it depends on
  const key = (u) => (u.k_budget === null ? 1e9 : u.k_budget)
  const unc = ev.uncertain.slice().sort((a, b) => key(a) - key(b))
  const shown = unc.slice(0, 4), gateAnc = ev.gates.map((g) => cost_ancestors(P, [g.on]))
  const gateTxt = (g) => `gate ${N[g.on].name || g.on} ${cost_OP[g.op]} ${num(g.value)} in ${g.phase} (now ${num(g.base_value)}, ${g.passes ? 'passes' : 'fails'}; uncut plan at it ${usd(g.uncut_total_at_threshold)})${g.else ? `, else ${g.else}` : ''}`
  const used = new Set()
  const rests = shown.map((u) => {
    const n = N[u.id]
    const parts = [`${n.name || u.id} ${num(u.value)}${n.unit && n.unit !== '1' ? ` ${n.unit}` : ''} [${cost_TAG[n.basis]}]${n.quote ? ` "${n.quote}"` : n.rests_on ? ` rests on: ${n.rests_on}` : ''}`]
    if (u.differs_in.length) parts.push(`differs: ${u.differs_in.join(', ')}`)
    parts.push(u.measured_by ? `measured in ${u.measured_by}${u.cum_spend_through_measured_by !== null ? ` (${usd(u.cum_spend_through_measured_by)} spent by then)` : ''}` : 'no phase measures it')
    ev.gates.forEach((g, i) => { if (!used.has(i) && gateAnc[i].has(u.id)) { used.add(i); parts.push(gateTxt(g)) } })
    const atK = u.dir === 'higher' ? u.value * u.k_budget : u.value / u.k_budget
    parts.push(u.k_budget !== null ? `budget reached at ${num(atK)} (${cost_fmt_k(u.k_budget)}× ${u.dir})` : 'budget not reached within 1000×')
    if (u.k_box !== null) parts.push(`box overflows at ${cost_fmt_k(u.k_box)}×`)
    return parts.join(' · ')
  })
  ev.gates.forEach((g, i) => { if (!used.has(i)) rests.push(gateTxt(g)) })
  if (unc.length > shown.length) rests.push(`+${unc.length - shown.length} more: ${unc.slice(4).map((u) => N[u.id].name || u.id).join(', ')}`)
  sec('Rests on', rests)
  sec('Scenarios', ev.scenarios.length ? [ev.scenarios.map((s) => `${s.what || s.id} → ${usd(s.total)}${s.total > budget ? ' (over budget)' : ''}`).join(' · ')] : [])
  const S = cost_index(c.scenarios)
  sec('Buys', ev.yields.map((y) => `${N[y.id].name || y.id}: ${num(y.base)} [${cost_TAG[N[y.id].basis]}]${Object.entries(y.by_scenario).map(([sid, v]) => ` · ${S[sid].what || sid}: ${num(v)}`).join('')}`))
  sec('Flags', ev.errors.map((e) => `error (${e.kind}) at ${e.where}: ${e.msg}`).concat(ev.flags))
  const F = cost_index(plan.full_scale)
  sec('Full scale', ev.full_scale.map((f) => {
    const leaves = [...cost_ancestors(P, cost_ids(P.ast[`full_scale.${f.id}.usd`]))].filter((id) => N[id] && N[id].basis !== 'DERIVED').map((id) => N[id])
    const tags = Object.entries(leaves.reduce((m, n) => ({ ...m, [cost_TAG[n.basis]]: (m[cost_TAG[n.basis]] || 0) + 1 }), {})).map(([t, k]) => `${k} ${t}`)
    const unsure = leaves.filter((n) => n.basis === 'GUESS' || n.basis === 'PROXY').map((n) => `[${cost_TAG[n.basis]}] ${n.name || n.id}`)
    const ratio = f.ratio_to_value !== null ? ` = ${num(f.ratio_to_value)}× ${N[F[f.id].ratio_to].name || F[f.id].ratio_to}` : ''
    return `${f.what}: ${usd(f.usd)} = ${num(f.multiple_of_budget)}× budget${ratio}${tags.length ? ` · inputs ${tags.join(', ')}` : ''}${unsure.length ? ` (${unsure.join('; ')})` : ''}`
  }))
  sec('Outside', (plan.outside_budget || []).length ? [plan.outside_budget.map((o) => `${o.what}: ${o.qty} ${o.unit}`).join(' · ')] : [])
  return out.join('\n')
}

// Card body line, at most 45 words: sentences are added in priority order while they fit.
function cost_render_short(ev, plan) {
  if (ev.planned === null) return `The cost record did not evaluate (${ev.errors.length} error${ev.errors.length === 1 ? '' : 's'}); see the cost block.`
  const N = cost_index(plan.numbers), usd = cost_fmt_usd, budget = ev.planned + ev.unallocated, h = cost_machine_hours(ev, plan)
  const s = [ev.planned > budget
    ? `Over budget: plans ${usd(ev.planned)} against the ${usd(budget)} budget.`
    : `Plans ${usd(ev.planned)} of the ${usd(budget)} budget${h ? ` over ${cost_fmt_num(h)} machine-hours` : ''}, leaving ${usd(ev.unallocated)}.`]
  const m = cost_main_guess(ev)
  if (m) {
    const n = N[m.id]
    s.push(`Main guess: ${n.name || m.id} [${cost_TAG[n.basis]}], measured${m.cum_spend_through_measured_by !== null ? ` after ${usd(m.cum_spend_through_measured_by)} of spend` : ' first'}${m.k_budget !== null ? `; the budget is reached if it is ${cost_fmt_k(m.k_budget)}× ${m.dir}` : ''}.`)
  }
  const big = ev.full_scale.reduce((b, f) => (!b || f.multiple_of_budget > b.multiple_of_budget ? f : b), null)
  if (big) s.push(`Full scale: ${big.what}, ${usd(big.usd)}, ${cost_fmt_num(big.multiple_of_budget)}× the budget.`)
  const g = ev.gates[0]
  if (g) s.push(`Pilot gate: ${N[g.on].name || g.on} ${cost_OP[g.op]} ${cost_fmt_num(g.value)}${g.passes ? '' : ' (fails at the plan\'s own value)'}${g.else ? `, else ${g.else}` : ''}.`)
  if (ev.flags.length) s.push(`${ev.flags.length} cost flag${ev.flags.length === 1 ? '' : 's'} in the block.`)
  const out = []
  let w = 0
  for (const x of s) { const k = cost_words(x); if (w + k <= 45) { out.push(x); w += k } }
  return out.join(' ')
}

// Appendix: every DERIVED number, id-bearing line expression and full-scale figure with values substituted.
function cost_render_derivations(ev, plan) {
  if (ev.planned === null) return 'Derivations: the cost record did not evaluate.'
  const lineById = cost_index(ev.lines)
  const value = (id) => (id === 'budget_usd' ? ev.planned + ev.unallocated : id in ev.numbers ? ev.numbers[id] : id in ev.rates ? ev.rates[id] : lineById[id].usd)
  const show = (src, v, unit) => {
    const a = cost_parse(src), subst = cost_ids(a).size ? ` = ${cost_ast_str(a, (id) => cost_fmt_exact(value(id)))}` : ''
    return `${src}${subst} = ${cost_fmt_exact(v)}${unit ? ` ${unit}` : ''}`
  }
  const out = ['Derivations: each computed number with its inputs substituted']
  for (const n of plan.numbers || []) if (n.basis === 'DERIVED') out.push(`${n.id} = ${show(n.expr, ev.numbers[n.id], n.unit)}`)
  for (const l of (plan.cost || {}).lines || []) {
    const r = lineById[l.id]
    for (const [k, v, unit] of [['hours', r.hours, 'h'], ['need', r.need_h, 'h'], ['usd', r.usd, 'usd']]) {
      if (l[k] !== undefined && l[k] !== null && l[k] !== '' && cost_ids(cost_parse(l[k])).size) out.push(`${l.id}.${k} = ${show(l[k], v, unit)}`)
    }
  }
  for (const f of ev.full_scale) out.push(`${f.id} = ${show(cost_index(plan.full_scale)[f.id].usd, f.usd, 'usd')}`)
  return out.join('\n')
}

// Placeholder menu for the writer side cell: rendered values only, so prose never retypes a computed number.
function cost_menu(ev, plan) {
  if (ev.planned === null) return []
  const N = cost_index(plan.numbers), usd = cost_fmt_usd, num = cost_fmt_num, out = []
  const add = (id, name, value, tag) => { if (!out.some((x) => x.id === id)) out.push({ id, name, value, tag }) }
  add('planned_usd', 'planned spend', usd(ev.planned), '=')
  add('planned_h', 'planned machine-hours', num(cost_machine_hours(ev, plan)), '=')
  add('unallocated_usd', 'budget left unallocated', usd(ev.unallocated), '=')
  if (Math.abs(ev.planned_with_options - ev.planned) > 0.005) add('planned_with_options_usd', 'planned spend including optional lines', usd(ev.planned_with_options), '=')
  const m = cost_main_guess(ev)
  if (m && m.cum_spend_through_measured_by !== null) add('pilot_cum_usd', `spend through the phase that measures ${N[m.id].name || m.id}`, usd(m.cum_spend_through_measured_by), '=')
  if (m && m.k_budget !== null) add('headroom', `how many times ${m.dir} ${N[m.id].name || m.id} can be before the budget is reached`, cost_fmt_k(m.k_budget), '=')
  ev.gates.forEach((g, i) => add(i ? `gate_value_${i + 1}` : 'gate_value', `pilot gate threshold on ${N[g.on].name || g.on}`, num(g.value), 'd'))
  for (const f of ev.full_scale) {
    const id = f.id.startsWith('fs_') ? f.id : `fs_${f.id}`, F = cost_index(plan.full_scale)[f.id]
    add(id, f.what, usd(f.usd), '=')
    add(`${id}_x`, `${f.what}, as a multiple of the budget`, num(f.multiple_of_budget), '=')
    if (f.ratio_to_value !== null) add(`${id}_ratio`, `${f.what}, as a multiple of ${N[F.ratio_to].name || F.ratio_to}`, num(f.ratio_to_value), '=')
  }
  const ax = plan.compute_axis
  if (ax && (ax.levels || []).length >= 2 && Math.min(...ax.levels) > 0) add('axis_span', `span of the compute axis (${ax.quantity}), largest level over smallest`, num(Math.max(...ax.levels) / Math.min(...ax.levels)), 'd')
  for (const y of ev.yields) add(y.id, `${N[y.id].name || y.id}${N[y.id].unit ? ` (${N[y.id].unit})` : ''}`, num(y.base), cost_TAG[N[y.id].basis])
  for (const n of plan.numbers || []) if (n.basis === 'DERIVED') add(n.id, `${n.name || n.id}${n.unit ? ` (${n.unit})` : ''}`, num(ev.numbers[n.id]), '=')
  return out
}

// ---------- S0 self-test: planted cases (cost.md §8.2 plus the contract's cases) ----------
function cost_selftest() {
  const failures = []
  const near = (x, y, tol) => typeof x === 'number' && Math.abs(x - y) <= tol
  const given = {
    budget_usd: 1000, budget_covers_storage: true, budget_covers_tax: false,
    price_sheet: {
      read_at: 'selftest', filesystem: { usd_gib_month: 0.2, page_text: 'selftest', example: true },
      instances: [
        { gpu: 'A100 SXM', gpu_memory_gb: 40, n_gpus: 8, per_gpu_usd_h: 1.99, page_text: 'selftest' },
        { gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 1, per_gpu_usd_h: 4.29, page_text: 'selftest' },
        { gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99, page_text: 'selftest' },
      ],
    },
  }
  const r1 = { id: 'r1', gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 1, per_gpu_usd_h: 4.29 }
  const r8 = { id: 'r8', gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99 }
  const ra = { id: 'ra', gpu: 'A100 SXM', gpu_memory_gb: 40, n_gpus: 8, per_gpu_usd_h: 1.99 }
  const plan = (numbers, rates, lines, total, phases, scenarios) => ({
    phases: phases || [{ id: 'P0', what: 'pilot' }, { id: 'P1', what: 'main runs' }], numbers,
    cost: { rates, lines, scenarios: scenarios || [], total_stated: total }, full_scale: [], outside_budget: [],
  })
  const work = (id, phase, hours, extra) => ({ id, phase, what: id, kind: 'work', rate: 'r1', hours, ...extra })
  const cases = {
    // pick 6 (W13): scenarios $676.60 / $761.89 / $875.60; budget reached at 1.93x slower training
    p06: [plan([
      { id: 'lr_steps', name: 'steps in LeRobot SmolVLA timing', unit: 'steps', basis: 'PROXY', value: 20000, source_id: 's_lerobot', quote: '20k steps will roughly take ~4 hrs on a single A100 GPU', page_setting: 'SmolVLA fine-tune, 1x A100', differs_in: ['dataset'], measured_by: 'P0' },
      { id: 'lr_hours', name: 'hours for those steps', unit: 'h', basis: 'PROXY', value: 4, source_id: 's_lerobot', page_setting: 'same', differs_in: ['dataset'], measured_by: 'P0' },
      { id: 'sph', name: 'training steps per A100-hour', unit: 'steps/GPU-h', basis: 'DERIVED', expr: 'lr_steps / lr_hours' },
      { id: 's_a', name: 'steps, arm A', unit: 'steps', basis: 'DESIGN', value: 200000 },
      { id: 's_c', name: 'step-equivalents, arm C', unit: 'steps', basis: 'DERIVED', expr: '2 * 50000 * c_full' },
      { id: 'c_full', name: 'full fine-tune step cost vs expert-only', unit: 'x', basis: 'GUESS', value: 2, rests_on: 'producer assumption', measured_by: 'P0' },
      { id: 's_b50', name: 'steps, arm B 50k', unit: 'steps', basis: 'DESIGN', value: 200000 },
      { id: 's_bp', name: "steps, arm B'", unit: 'steps', basis: 'DESIGN', value: 200000 },
      { id: 's_w2', name: 'steps in wave 2', unit: 'steps', basis: 'DESIGN', value: 250000 },
      { id: 'gpus_w1', name: 'GPUs in wave 1', unit: 'GPUs', basis: 'DESIGN', value: 8 },
      { id: 'gpus_w2', name: 'GPUs in wave 2', unit: 'GPUs', basis: 'DESIGN', value: 5 },
      { id: 'gpuh_w1', name: 'A100-hours, wave 1', unit: 'GPU-h', basis: 'DERIVED', expr: '(s_a + s_c + s_b50 + s_bp) / sph' },
      { id: 'gpuh_w2', name: 'A100-hours, wave 2', unit: 'GPU-h', basis: 'DERIVED', expr: 's_w2 / sph' },
    ], [ra], [
      { id: 'pilot', phase: 'P0', what: 'pilot', kind: 'work', rate: 'ra', hours: '2' },
      { id: 'wave1', phase: 'W1', what: 'wave 1', kind: 'work', rate: 'ra', hours: 'gpuh_w1 / gpus_w1' },
      { id: 'wave2', phase: 'W2', what: 'wave 2', kind: 'work', rate: 'ra', hours: 'gpuh_w2 / gpus_w2' },
      { id: 'evtail', phase: 'EV', what: 'evaluation tail', kind: 'work', rate: 'ra', hours: '3' },
    ], 557, [{ id: 'P0', what: 'pilot' }, { id: 'W1', what: 'wave 1' }, { id: 'W2', what: 'wave 2' }, { id: 'EV', what: 'evaluation' }],
    [{ id: 's4000', what: '4,000 steps/A100-h', set: { sph: 4000 } }, { id: 's3500', what: '3,500', set: { sph: 3500 } }, { id: 's3000', what: '3,000', set: { sph: 3000 } }]), (ev) => {
      const t = ev.scenarios.map((s) => s.total), u = ev.uncertain.find((x) => x.id === 'lr_steps')
      return near(ev.planned, 557.2, 0.005) && near(t[0], 676.6, 0.005) && near(t[1], 761.89, 0.005) && near(t[2], 875.6, 0.005) && u && near(u.k_budget, 1.93, 0.005)
    }],
    // a GUESS reachable only through a time box's need must be load-bearing, and flagged when nothing measures it
    need_only: [plan([
      { id: 'tok', name: 'tokens to generate', unit: 'tokens', basis: 'DESIGN', value: 2e6 },
      { id: 'tps', name: 'generation speed', unit: 'tok/s', basis: 'GUESS', value: 100, rests_on: 'producer estimate' },
    ], [r1], [work('a', 'P0', '2'), work('b', 'P1', '8', { need: 'tok / tps / 3600' })], 42.9), (ev, p) =>
      cost_load_bearing(p).uncertain.includes('tps') && ev.uncertain.some((u) => u.id === 'tps' && u.k_box !== null) &&
      ev.flags.some((f) => f.startsWith('generation speed [g] is load-bearing and no phase measures it'))],
    // a pilot gate the plan's own value fails (pick 18's shape)
    gate_fails: [{ ...plan([{ id: 'thr', name: 'pilot throughput', unit: 'samples/s', basis: 'GUESS', value: 5, rests_on: 'estimate', measured_by: 'P0' }],
      [r1], [work('a', 'P0', '2'), work('b', 'P1', '10')], 51.48), phases: [{ id: 'P0', what: 'pilot', gate: { on: 'thr', op: '>=', value: 13, else: 'config B' } }, { id: 'P1', what: 'main' }] },
    (ev) => ev.gates.length === 1 && ev.gates[0].passes === false && ev.flags.some((f) => f.startsWith('gate in P0 fails'))],
    // a GUESS with 1.02x headroom: 61.58 h x $15.92 = $980.35, budget reached at 1.02x
    thin: [plan([
      { id: 'steps', name: 'steps', unit: 'steps', basis: 'DESIGN', value: 61580 },
      { id: 'sph', name: 'steps per hour', unit: 'steps/h', basis: 'GUESS', value: 1000, rests_on: 'estimate', measured_by: 'P1' },
    ], [ra], [{ id: 'run', phase: 'P1', what: 'run', kind: 'work', rate: 'ra', hours: 'steps / sph' }], 980.35), (ev) =>
      ev.uncertain.some((u) => u.id === 'sph' && near(u.k_budget, 1.02, 0.001)) && ev.flags.some((f) => f.startsWith('thin headroom'))],
    // computed $1,040 with $1,040 stated: the halt condition must be visible as planned > budget
    over: [plan([], [r8], [{ id: 'a', phase: 'P1', what: 'runs', kind: 'work', rate: 'r8', hours: '30' }, { id: 'b', phase: 'P1', what: 'reruns', kind: 'allotment', usd: '82.4' }], 1040),
      (ev, p) => near(ev.planned, 1040, 0.005) && ev.planned > 1000 && p.cost.total_stated > 1000 && ev.flags.some((f) => f.startsWith('planned spend $1,040 is over'))],
    undefined_id: [plan([{ id: 'steps', name: 'steps', unit: 'steps', basis: 'DESIGN', value: 100 }], [r1], [work('a', 'P1', 'steps / speed')], 10),
      (ev) => !ev.ok && ev.errors.some((e) => e.kind === 'undefined' && e.where === 'lines.a.hours')],
    quote: [plan([{ id: 'bw', name: 'HBM bandwidth', unit: 'TB/s', basis: 'CITED', value: 3.35, source_id: 's1', quote: 'up to 4.8TB/s of memory bandwidth' }], [r1], [work('a', 'P1', '2')], 8.58),
      (ev) => !ev.ok && ev.errors.some((e) => e.kind === 'quote' && e.where === 'numbers.bw.quote')],
    // the default minimal encoding: two lines, constant hours, one rate, a total; nothing to flag
    minimal: [plan([], [r1], [work('a', 'P0', '2'), work('b', 'P1', '10')], 51.48),
      (ev) => ev.ok && near(ev.planned, 51.48, 0.005) && ev.flags.length === 0],
  }
  for (const [name, [p, check]] of Object.entries(cases)) {
    try { if (!check(cost_eval_plan(p, given), p)) failures.push(`cost selftest ${name}: check failed`) }
    catch (e) { failures.push(`cost selftest ${name}: threw ${e && e.msg ? e.msg : e}`) }
  }
  return { ok: failures.length === 0, failures }
}


// ---- src/pick.js ----
// ---------- pick.js: seeded draws and the pick rule (S5) ----------

// Ported unchanged from the first script (keyed, so async completion order cannot change draws).
function pick_hashStr(s) {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) }
  return h >>> 0
}
function pick_mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const pick_u = (seed, key) => pick_mulberry32(pick_hashStr(`${seed}:${key}`))()
// The old pickIndex(key, n), with SEED passed in. Used only to replay the first run.
const pick_legacy_index = (seed, key, n) => Math.floor(pick_u(seed, key) * n)

// The first run's rule, for the replay: top = first listed among the highest totals (strict >);
// random = an index draw over every other option in list order.
function pick_run_legacy(input) {
  const picks = []
  for (const b of input.branches) {
    if (!b.options.length) continue
    let top = b.options[0]
    for (const o of b.options) if (o.total > top.total) top = o
    const rest = b.options.filter(o => o.id !== top.id)
    const row = (o, kind) => ({ key: o.key, root: b.root, branch: b.branch, kind, id: o.id, title: o.title, total: o.total })
    picks.push(row(top, 'top'))
    if (rest.length) picks.push(row(rest[pick_legacy_index(input.seed, `${b.root}:${b.branch}:random`, rest.length)], 'random'))
  }
  return { picks }
}

const pick_DIST = { SAME: 0, ADJACENT: 1, ELSEWHERE: 2 }
// Tie order after total (criteria §8.4); the seeded order u_k breaks what is left.
const pick_TIE = { physical: ['open', 'stakes'], interp: ['open', 'internals', 'stakes'] }
// Reshape route: tie order after reshape + stakes.
const pick_RESHAPE_TIE = { physical: ['reshape', 'stakes', 'open'], interp: ['reshape', 'stakes', 'internals', 'open'] }

// The rule (flow §2.10 step 7, criteria §8.4). Each option's place in the seeded order depends only on its own key,
// so removing or excluding one option never re-rolls the draw for the others.
function pick_run(input) {
  const { seed, args, branches } = input
  const clusters = input.clusters || [], seedIdeas = input.seed_ideas || []
  const log = []
  const topic = {}, cid = {}
  clusters.forEach((c, i) => c.members.forEach(k => { topic[k] = c.topic; cid[k] = i }))
  const clusterOf = k => (k in cid ? cid[k] : k) // an option no cluster names is its own cluster
  const all = branches.flatMap(b => b.options.map(o => ({ ...o, root: b.root, branch: b.branch, u: pick_u(seed, `order:${o.key}`) })))
  const inBranch = (root, branch) => all.filter(o => o.root === root && o.branch === branch)
  const closed = o => o.compute_open_status === 'settled' || o.compute_open_status === 'none'
  // The floors (open: settled/none -> 1; reshape: sequential none -> 1) are applied here too, so the scores agree with
  // main's whatever the caller passed. A missing reshape score counts 0 (a run scored without the criterion).
  const val = (o, c) => (c === 'open' && closed(o) ? 1 : c === 'reshape' ? (o.sequential_status === 'none' ? 1 : o.scores.reshape ?? 0) : o.scores[c])
  // Gated only when both questions are closed: no open compute quantity and no step-after-step chain named.
  const gated = o => !!args.require_compute_lever[o.branch] && closed(o) && o.sequential_status === 'none'
  const eligible = o => o.distance !== 'ELSEWHERE' && !gated(o)
  const byU = (a, b) => a.u - b.u
  const byTotal = (a, b) => b.total - a.total || pick_TIE[a.branch].reduce((d, c) => d || val(b, c) - val(a, c), 0) || a.u - b.u
  const reshapeSum = o => val(o, 'reshape') + val(o, 'stakes')
  const byReshape = (a, b) => reshapeSum(b) - reshapeSum(a) || pick_RESHAPE_TIE[a.branch].reduce((d, c) => d || val(b, c) - val(a, c), 0) || a.u - b.u
  const routes = o => val(o, 'reshape') >= 4

  // Top: the reshape route first (reshape >= 4 and stakes >= 3, highest reshape + stakes); else the open route
  // (highest total among options with open >= 3; if none qualifies, highest total). Each route is logged.
  const chooseTop = (cands, tag) => {
    if (!cands.length) return null
    const rs = cands.filter(o => routes(o) && val(o, 'stakes') >= 3)
    let qual, why, sum, order, ties
    if (rs.length) { qual = rs; why = 'reshape route: highest reshape + stakes'; sum = reshapeSum; order = byReshape; ties = pick_RESHAPE_TIE; log.push(`${tag}: reshape route`) }
    else {
      log.push(`${tag}: no reshape option`)
      qual = cands.filter(o => val(o, 'open') >= 3); why = 'highest total with open >= 3'; sum = o => o.total; order = byTotal; ties = pick_TIE
      if (!qual.length) { qual = cands; why = 'no open option; highest total'; log.push(`${tag}: no open option; top taken by total`) }
    }
    const top = qual.slice().sort(order)[0]
    let tied = qual.filter(o => sum(o) === sum(top)), note = ''
    const n = tied.length
    if (n > 1) {
      note = `tie of ${n} broken by seeded order`
      for (const c of ties[top.branch]) {
        tied = tied.filter(o => val(o, c) === val(top, c))
        if (tied.length === 1) { note = `tie of ${n} broken by ${c}`; break }
      }
    }
    return { opt: top, note, why: note ? `${why}, ${note}` : why }
  }
  const choose = (kind, cands, tag) => (kind === 'top' ? chooseTop(cands, tag)
    : cands.length ? { opt: cands.slice().sort(byU)[0], note: '', why: 'next eligible in seeded order' } : null)

  // Provisional picks per branch: top, then the first picks_per_branch - 1 other eligible options in u-order.
  const slots = []
  for (const b of branches) {
    const tag = `${b.root}:${b.branch}`
    const el = inBranch(b.root, b.branch).filter(eligible)
    if (el.length < args.picks_per_branch) log.push(`${tag}: ${el.length} eligible option(s); picking ${el.length}`)
    const top = chooseTop(el, tag)
    if (!top) continue
    slots.push({ kind: 'top', ...top, replaced: [] })
    for (const o of el.filter(o => o !== top.opt).sort(byU).slice(0, args.picks_per_branch - 1))
      slots.push({ kind: 'random', opt: o, note: '', why: 'next eligible in seeded order', replaced: [] })
  }

  // Collisions: picks in different roots that share a cluster. Keep the better distance, then top before random,
  // then lower u_k; never totals, which come from different criteria sets (flow §2.8 item 4). The loser takes the
  // next eligible option in its branch whose cluster has no pick, so a replacement never collides again.
  const better = (a, b) => pick_DIST[a.opt.distance] - pick_DIST[b.opt.distance]
    || (a.kind === 'top' ? 0 : 1) - (b.kind === 'top' ? 0 : 1) || a.opt.u - b.opt.u
  const lost = {}
  for (;;) {
    const hit = slots.map(s => slots.filter(t => clusterOf(t.opt.key) === clusterOf(s.opt.key)))
      .find(g => new Set(g.map(t => t.opt.root)).size > 1)
    if (!hit) break
    const win = hit.slice().sort(better)[0]
    for (const s of hit) {
      if (s.opt.root === win.opt.root) continue
      const reason = `collided with ${win.opt.key} in ${topic[win.opt.key]}`
      const tag = `${s.opt.root}:${s.opt.branch}:${s.kind}`
      const taken = new Set(slots.map(t => clusterOf(t.opt.key)))
      const next = choose(s.kind, inBranch(s.opt.root, s.opt.branch).filter(o => eligible(o) && !taken.has(clusterOf(o.key))), tag)
      lost[s.opt.key] = reason
      log.push(`${tag}: ${s.opt.key} ${reason}; ${next ? `replaced by ${next.opt.key}` : 'no replacement'}`)
      if (next) { s.replaced.push({ key: s.opt.key, reason }); Object.assign(s, next) }
      else slots.splice(slots.indexOf(s), 1)
    }
  }

  // Pool: ELSEWHERE options whose cluster has no pick, one per cluster (lowest u_k); those with reshape >= 4 first, then
  // the rest, each in u-order; the first pool_k. Drawn, not taken by total: the top ELSEWHERE total was the same famous
  // field in every seed (flow §2.8 item 2). The compute-lever gate applies here too.
  const taken = new Set(slots.map(s => clusterOf(s.opt.key)))
  const rep = new Map()
  for (const o of all.slice().sort(byU))
    if (o.distance === 'ELSEWHERE' && !gated(o) && !taken.has(clusterOf(o.key)) && !rep.has(clusterOf(o.key))) rep.set(clusterOf(o.key), o)
  const pool = [...rep.values()].sort((a, b) => routes(b) - routes(a) || a.u - b.u).slice(0, args.pool_k)
  log.push(`pool: ${rep.size} candidate cluster(s); picked ${pool.length}`)

  const rank = {}
  for (const b of branches) inBranch(b.root, b.branch).sort(byTotal).forEach((o, i) => { rank[o.key] = i + 1 })
  const row = (o, kind, note, replaced) => ({ key: o.key, root: o.root, branch: o.branch, kind, rank: rank[o.key], total: o.total, tie_note: note, replaced })
  const picks = [
    ...slots.map(s => row(s.opt, s.kind, s.note, s.replaced)),
    ...pool.map(o => row(o, 'pool', '', [])),
    ...seedIdeas.map(s => ({ key: s.key, root: null, branch: null, kind: 'seed', rank: null, total: null, tie_note: '', replaced: [] })),
  ]

  const picked = {}
  for (const s of slots) picked[s.opt.key] = { status: `picked_${s.kind}`, reason: s.why + (s.replaced.length ? `; replaced ${s.replaced.map(r => r.key).join(', ')}` : '') }
  for (const o of pool) picked[o.key] = { status: 'picked_pool', reason: 'ELSEWHERE; drawn for the pool' }
  const inventory = all.map(o => {
    const c = clusterOf(o.key)
    const { status, reason } = picked[o.key]
      || (lost[o.key] && { status: 'collided', reason: lost[o.key] })
      || (gated(o) && { status: 'not_eligible', reason: `compute_open ${o.compute_open_status}, sequential none` })
      || (o.distance === 'ELSEWHERE' && { status: 'not_eligible', reason: taken.has(c) ? 'ELSEWHERE; its cluster has a pick'
        : rep.get(c) !== o ? `ELSEWHERE; its cluster is represented by ${rep.get(c).key}` : 'ELSEWHERE; not drawn for the pool' })
      || { status: 'not_picked', reason: 'not drawn' }
    return { key: o.key, root: o.root, branch: o.branch, title: o.title, distance: o.distance, cluster_topic: topic[o.key] || null, total: o.total, status, reason }
  })

  // Frontier: high-stakes options whose open range lies beyond the budget, not picked; listed for the human, not produced here.
  const frontier = all.filter(o => !picked[o.key] && val(o, 'open') <= 2 && o.compute_open_status !== 'none' && o.scores.stakes >= 4)
    .map(o => ({ root: o.root, key: o.key, title: o.title, compute_open: o.compute_open, distance: o.distance }))

  return { picks, frontier, inventory, log }
}

// Planted cases: flow P18 (i)-(iv), criteria §8.4 cases 15-16, reshape cases 19-23, determinism. Seed 7 gives these seeded orders:
// R1:physical f < e < a < d < c < b; R2:physical d < x < c; R2:physical:d < R1:physical:b; R1:physical q < p; R1:interp q < r < p;
// R4:physical k < j; R5:physical n < m.
// In each collision case the winner has the lower total, and the key under test is the only one that favours it.
// Options default to sequential_status none with no reshape score, which is the rule before the reshape route.
function pick_selftest() {
  const failures = []
  const check = (name, ok) => { if (!ok) failures.push(name) }
  const args = { pool_k: 3, picks_per_branch: 2, require_compute_lever: { physical: true, interp: true } }
  const o = (key, scores, distance = 'SAME', status = 'open', seq = 'none') => ({ key, id: key.split(':')[2], title: key, scores, distance,
    total: Object.entries(scores).reduce((a, [c, v]) => a + (c === 'reshape' ? 0 : v), 0), compute_open_status: status, compute_open: status, sequential_status: seq })
  const input = (opts, clusters = []) => {
    const branches = []
    for (const x of opts) {
      const [root, branch] = x.key.split(':')
      let b = branches.find(b => b.root === root && b.branch === branch)
      if (!b) branches.push(b = { root, branch, options: [] })
      b.options.push(x)
    }
    return { seed: 7, args, branches, clusters, seed_ideas: [] }
  }
  const run = (opts, clusters) => pick_run(input(opts, clusters))
  const picks = r => r.picks.map(p => `${p.kind} ${p.key}`).join(', ')
  const status = (r, key) => r.inventory.find(x => x.key === key).status

  // P18 (i), (ii): top b by total; random f, the first other eligible option in seeded order.
  const six = [o('R1:physical:a', { open: 3, stakes: 3 }), o('R1:physical:b', { open: 4, stakes: 5 }), o('R1:physical:c', { open: 3, stakes: 4 }),
    o('R1:physical:d', { open: 2, stakes: 2 }), o('R1:physical:e', { open: 3, stakes: 2 }), o('R1:physical:f', { open: 1, stakes: 3 })]
  const base = 'top R1:physical:b, random R1:physical:f'
  check('six options: top b, random f', picks(run(six)) === base)
  for (const id of ['a', 'c', 'd', 'e'])
    check(`P18(i): removing non-picked ${id} leaves both picks unchanged`, picks(run(six.filter(x => x.id !== id))) === base)
  check('P18(ii): excluding the random pick f yields e, the next in seeded order',
    picks(run(six.map(x => (x.id === 'f' ? { ...x, compute_open_status: 'none' } : x)))) === 'top R1:physical:b, random R1:physical:e')

  // P18 (iii): collisions resolve by distance, then kind, then order; never by total.
  let r = run([o('R1:physical:a', { open: 5, stakes: 5 }, 'ADJACENT'), o('R1:physical:b', { open: 3, stakes: 1 }), o('R1:physical:e', { open: 1, stakes: 1 }),
    o('R2:physical:c', { open: 3, stakes: 3 }), o('R2:physical:d', { open: 3, stakes: 1 }), o('R2:physical:x', { open: 3, stakes: 2 })],
  [{ topic: 'shared topic one', members: ['R1:physical:a', 'R2:physical:c'] }])
  check('P18(iii) distance: SAME c (total 6, later u) beats ADJACENT a (total 10); R1 top takes b',
    picks(r) === 'top R1:physical:b, random R1:physical:e, top R2:physical:c, random R2:physical:d'
    && JSON.stringify(r.picks[0].replaced) === JSON.stringify([{ key: 'R1:physical:a', reason: 'collided with R2:physical:c in shared topic one' }])
    && status(r, 'R1:physical:a') === 'collided')
  r = run([o('R1:physical:a', { open: 1, stakes: 1 }), o('R1:physical:b', { open: 3, stakes: 2 }),
    o('R2:physical:c', { open: 4, stakes: 5 }), o('R2:physical:d', { open: 4, stakes: 4 }), o('R2:physical:x', { open: 3, stakes: 2 })],
  [{ topic: 'shared topic two', members: ['R1:physical:b', 'R2:physical:d'] }])
  check('P18(iii) kind: top b (total 5, later u) beats random d (total 8); R2 random takes x',
    picks(r) === 'top R1:physical:b, random R1:physical:a, top R2:physical:c, random R2:physical:x' && status(r, 'R2:physical:d') === 'collided')
  const twoRoots = [o('R1:physical:a', { open: 3, stakes: 2 }), o('R1:physical:b', { open: 1, stakes: 1 }),
    o('R2:physical:c', { open: 4, stakes: 5 }), o('R2:physical:d', { open: 3, stakes: 1 }), o('R2:physical:x', { open: 3, stakes: 2 })]
  r = run(twoRoots, [{ topic: 'shared topic three', members: ['R1:physical:a', 'R2:physical:c'] }])
  check('P18(iii) order: top a (total 5, lower u) beats top c (total 9); R2 top takes x',
    picks(r) === 'top R1:physical:a, random R1:physical:b, top R2:physical:x, random R2:physical:d' && status(r, 'R2:physical:c') === 'collided')

  // P18 (iv): a cluster picked in one root only (a in R1; x is not picked in R2) excludes nothing.
  r = run(twoRoots, [{ topic: 'shared topic four', members: ['R1:physical:a', 'R2:physical:x'] }])
  check('P18(iv): a cluster picked in one root excludes nothing',
    picks(r) === picks(run(twoRoots)) && picks(r) === 'top R1:physical:a, random R1:physical:b, top R2:physical:c, random R2:physical:d'
    && status(r, 'R2:physical:x') === 'not_picked')

  // §8.4 case 15: ties by open (interp: open, internals, stakes) before the seeded order, which favours q.
  r = run([o('R1:physical:p', { open: 4, stakes: 3 }), o('R1:physical:q', { open: 3, stakes: 4 }),
    o('R1:interp:p', { open: 4, internals: 3, stakes: 2 }), o('R1:interp:q', { open: 4, internals: 2, stakes: 3 }), o('R1:interp:r', { open: 3, internals: 3, stakes: 3 })])
  const tops = r.picks.filter(p => p.kind === 'top')
  check('§8.4(15): a tie broken by open', tops[0].key === 'R1:physical:p' && tops[0].tie_note === 'tie of 2 broken by open')
  check('§8.4(15): interp tie of 3 broken by internals', tops[1].key === 'R1:interp:p' && tops[1].tie_note === 'tie of 3 broken by internals')

  // §8.4 case 16: open <= 2 cannot be top while an open option exists; with none, highest total and a log line.
  r = run([o('R1:physical:a', { open: 2, stakes: 5 }), o('R1:physical:b', { open: 3, stakes: 2 })])
  check('§8.4(16): open <= 2 is not top', r.picks[0].key === 'R1:physical:b' && !r.log.some(l => l.includes('no open option')))
  r = run([o('R1:physical:a', { open: 2, stakes: 5 }), o('R1:physical:b', { open: 1, stakes: 4 })])
  check('§8.4(16): fallback when no option is open', r.picks[0].key === 'R1:physical:a' && r.log.includes('R1:physical: no open option; top taken by total'))

  // 19: a reshape-route top (reshape 4, stakes 3, total 6) beats a higher total (10) on the open route; reshape 5 with stakes 2 does not route.
  const N = 'named'
  r = run([o('R1:physical:a', { open: 3, stakes: 3, reshape: 4 }, 'SAME', 'open', N), o('R1:physical:b', { open: 5, stakes: 5, reshape: 2 }, 'SAME', 'open', N),
    o('R1:physical:c', { open: 3, stakes: 2, reshape: 5 }, 'SAME', 'open', N)])
  check('19: the reshape route beats a higher total on the open route', picks(r) === 'top R1:physical:a, random R1:physical:c'
    && r.log.includes('R1:physical: reshape route') && r.inventory[0].reason === 'reshape route: highest reshape + stakes')
  // 20: compute_open none with a named chain is eligible (its open is still floored, so e is top); both none is not.
  r = run([o('R1:physical:a', { open: 3, stakes: 3 }, 'SAME', 'none', N), o('R1:physical:b', { open: 3, stakes: 5 }, 'SAME', 'none'), o('R1:physical:e', { open: 3, stakes: 2 })])
  check('20: compute_open none with sequential named is eligible; both none is not_eligible', picks(r) === 'top R1:physical:e, random R1:physical:a'
    && status(r, 'R1:physical:b') === 'not_eligible' && r.inventory.find(x => x.key === 'R1:physical:b').reason === 'compute_open none, sequential none')
  // 21: pool_k 1 takes j (reshape 4) over k (lower u, no reshape score); without the score, k.
  const pool1 = opts => pick_run({ ...input(opts), args: { ...args, pool_k: 1 } }).picks.map(p => `${p.kind} ${p.key}`).join(', ')
  check('21: the pool takes reshape >= 4 first, then u-order', pool1([o('R4:physical:k', { open: 3, stakes: 3 }, 'ELSEWHERE', 'open', N),
    o('R4:physical:j', { open: 3, stakes: 3, reshape: 4 }, 'ELSEWHERE', 'open', N)]) === 'pool R4:physical:j'
    && pool1([o('R4:physical:k', { open: 3, stakes: 3 }, 'ELSEWHERE', 'open', N), o('R4:physical:j', { open: 3, stakes: 3 }, 'ELSEWHERE', 'open', N)]) === 'pool R4:physical:k')
  // 22: sequential "none: independent runs" (status none, as main derives it) floors reshape 5 to 1: m leaves the
  // reshape route and n wins on the open route.
  r = run([o('R5:physical:m', { open: 3, stakes: 3, reshape: 5 }), o('R5:physical:n', { open: 4, stakes: 4, reshape: 2 }, 'SAME', 'open', N)])
  check('22: sequential none floors reshape to 1', r.picks[0].key === 'R5:physical:n' && r.log.includes('R5:physical: no reshape option') && !r.log.some(l => l.includes('reshape route')))
  // 23: no option at reshape >= 4 reproduces the open-route picks of P18.
  check('23: a branch with no option at reshape >= 4 keeps the current top pick',
    picks(run(six.map(x => ({ ...x, scores: { ...x.scores, reshape: 3 }, sequential_status: N })))) === base)

  // Same seed, same input: identical output, input untouched. R3 m and n tie on every score (m is first in seeded order).
  const inp = input([...twoRoots, o('R3:physical:n', { open: 3, stakes: 3 }), o('R3:physical:m', { open: 3, stakes: 3 }),
    o('R3:interp:z', { open: 4, internals: 4, stakes: 4 }, 'ELSEWHERE')], [{ topic: 'shared topic three', members: ['R1:physical:a', 'R2:physical:c'] }])
  inp.seed_ideas = [{ key: 'seed:1', title: 'an idea', text: 'an idea from the human' }]
  const before = JSON.stringify(inp), once = pick_run(inp)
  check('a full tie goes to the seeded order', once.picks.some(p => p.key === 'R3:physical:m' && p.kind === 'top' && p.tie_note === 'tie of 2 broken by seeded order'))
  check('determinism: same seed gives identical output, input unchanged', JSON.stringify(once) === JSON.stringify(pick_run(inp)) && JSON.stringify(inp) === before)

  return { ok: failures.length === 0, failures }
}


// ---- src/gates.js ----
// ---------- gates (deterministic checks on returned records; S0 runs gate_selftest) ----------
// Record arguments are the arrays inside {items} / {clusters} / {pairs}; whole records otherwise.

// Plan field lookup: "predictions.if_lever", "phases.0.id", "phases[0].id", or an array element by id ("phases.P1").
function gate_get(obj, path) {
  let cur = obj
  for (const k of String(path).replace(/\[([^\]]+)\]/g, '.$1').split('.').filter(Boolean)) {
    if (cur === null || cur === undefined) return undefined
    cur = Array.isArray(cur) && !/^\d+$/.test(k) ? cur.find(x => x && x.id === k) : cur[k]
  }
  return cur
}
const gate_text = (plan, path) => {
  const v = gate_get(plan, path)
  return Array.isArray(v) ? v.join(' ') : String(v ?? '')
}

// Card fields: plan path -> word cap (CONTRACT §2.5). limits is capped joined. The restructuring fields are card
// fields only on a restructured plan (the card shows them only there).
const gate_card_caps = {
  question: 25, hypothesis: 22, 'predictions.if_lever': 22, 'predictions.if_not': 25, test_summary: 45,
  'novelty.closest_prior': 30, 'novelty.left_open': 30, 'anchor.what': 24, limits: 30,
  'restructuring.sequential_part': 18, 'restructuring.method': 22,
}
// Core card fields (the dramaturg's blocking set): ref name -> plan path.
const gate_CORE = {
  question: 'question', hypothesis: 'hypothesis', test_summary: 'test_summary', if_lever: 'predictions.if_lever',
  if_not: 'predictions.if_not', anchor: 'anchor.what', closest_prior: 'novelty.closest_prior',
}
const gate_STATUS = ['SUPPORTED', 'PARTIAL', 'UNSUPPORTED', 'CONTRADICTED', 'UNREACHABLE']
// A plan is restructured when restructuring.method, trimmed and lowercased, is not "none". A missing restructuring
// (a record from before the field existed) or an empty method counts as none.
const gate_restructured = plan => !['', 'none'].includes(String(((plan && plan.restructuring) || {}).method ?? '').trim().toLowerCase())
const gate_restructuring_field = path => String(path).startsWith('restructuring.')

// Source ids cited in a card field as [s1] or [s1, s3]; bracketed text with spaces is not a citation.
function gate_cited_ids(s) {
  const out = []
  for (const m of String(s ?? '').matchAll(/\[([^[\]]+)\]/g))
    for (const id of m[1].split(/[,;]/).map(x => x.trim())) if (/^[\w.:-]+$/.test(id)) out.push(id)
  return out
}

// Required fields that are absent (undefined or null), by walking the schema; anyOf passes if one branch does.
function gate_missing(schema, v, path) {
  if (schema.anyOf) {
    const tries = schema.anyOf.map(s => gate_missing(s, v, path))
    return tries.find(t => !t.length) || tries[0]
  }
  if (schema.type === 'array' && Array.isArray(v)) return v.flatMap((x, i) => gate_missing(schema.items, x, `${path}${i}.`))
  if (schema.type !== 'object' || v === null || typeof v !== 'object') return []
  const out = (schema.required || []).filter(k => v[k] === undefined || v[k] === null).map(k => path + k)
  for (const [k, s] of Object.entries(schema.properties || {}))
    if (v[k] !== undefined && v[k] !== null) out.push(...gate_missing(s, v[k], `${path}${k}.`))
  return out
}

// Cost figures belong to the script's cost line, which computes them: a dollar figure (the budget "$1,000" excepted),
// a multiple of the budget, compute-hours (substrate G-card regexes; cost.md §5).
function gate_cost_text(s) {
  const t = String(s ?? '').replace(/\$\s?1,000(?![\d,.])/g, '')
  if (/\$\s?\d/.test(t)) return 'dollar figure'
  if (/\d[\d,.]*\s*(\u00d7|x|times)\s+(the|this|a|our)?\s*budget/i.test(t)) return 'multiple of the budget'
  if (/\d[\d,.]*\s*(GPU|machine|node|instance)[- ]?hours?/i.test(t)) return 'compute-hours'
  return ''
}

function gate_opt(options) {
  const errors = []
  if (options.length < 3 || options.length > 25) errors.push(`${options.length} options (want 3 to 25)`)
  const seen = new Set()
  for (const o of options) {
    if (seen.has(o.id)) errors.push(`duplicate id ${o.id}`)
    seen.add(o.id)
    for (const f of ['id', 'title', 'summary', 'root_link', 'compute_open', 'sequential']) if (!String(o[f] ?? '').trim()) errors.push(`${o.id}: empty ${f}`)
  }
  return { ok: !errors.length, errors }
}

// Option critic. No NA (criteria.md §6). A reason under 15 characters or equal to the criterion name is degenerate
// (latent_skeptic's rule: schema-valid but content-free); degenerate makes ok false so the caller can resample.
function gate_oc(scores, options, criteria) {
  const errors = [], degenerate = new Set(), seen = new Set()
  const ids = new Set(options.map(o => o.id))
  for (const it of scores) {
    if (!ids.has(it.id)) errors.push(`unknown id ${it.id}`)
    if (seen.has(it.id)) errors.push(`duplicate id ${it.id}`)
    seen.add(it.id)
    if (!['SAME', 'ADJACENT', 'ELSEWHERE'].includes(it.distance)) errors.push(`${it.id}: distance ${it.distance}`)
    for (const c of criteria) {
      const s = (it.scores || []).find(x => x.criterion === c)
      if (!s) { errors.push(`${it.id}: missing ${c}`); continue }
      if (!Number.isInteger(s.value) || s.value < 1 || s.value > 5) errors.push(`${it.id}: ${c} = ${JSON.stringify(s.value)}`)
      const r = String(s.reason ?? '').trim()
      if (r.length < 15 || r.toLowerCase() === c.toLowerCase()) degenerate.add(it.id)
    }
  }
  for (const id of ids) if (!seen.has(id)) errors.push(`missing id ${id}`)
  return { ok: !errors.length && !degenerate.size, errors, degenerate: [...degenerate] }
}

// Totals = sum over the branch's criteria; `open` counts 1 when compute_open is settled or none. `reshape` routes the
// top pick and the pool and is left out, so the open route and the legacy reproduction keep their totals.
function gate_totals(scores, criteria, statusById) {
  const out = {}
  for (const it of scores) {
    const floor = ['settled', 'none'].includes(statusById[it.id])
    out[it.id] = criteria.filter(c => c !== 'reshape').reduce((t, c) => t + (c === 'open' && floor ? 1 : Number((it.scores.find(x => x.criterion === c) || {}).value)), 0)
  }
  return out
}

// ok covers the partition only (every key in exactly one cluster, no unknown key); a topic under 3 words is a soft
// fault: it triggers the resample with the Jaccard check but never costs the run a valid partition.
function gate_dedup(clusters, keys) {
  const errors = [], soft = []
  const count = new Map(keys.map(k => [k, 0]))
  for (const c of clusters) {
    if (txt_words(c.topic) < 3) soft.push(`topic "${c.topic}" has fewer than 3 words`)
    for (const m of c.members) {
      if (count.has(m)) count.set(m, count.get(m) + 1)
      else errors.push(`unknown key ${m}`)
    }
  }
  for (const [k, n] of count) if (n !== 1) errors.push(`${k} is in ${n} clusters`)
  return { ok: !errors.length, errors, soft }
}

// The dedup judge sees short handles, root:branch:K<n> (n = position in its branch), not option ids: long ids such as
// "A. Inference-time steering of VLA internals" came back shortened to keys that did not exist (run F, both samples).
function dedup_handles(options) {
  const seen = new Map(), toKey = new Map()
  const lines = options.map(o => {
    const rb = String(o.key).split(':').slice(0, 2).join(':')
    const n = (seen.get(rb) || 0) + 1
    seen.set(rb, n)
    const handle = `${rb}:K${n}`
    toKey.set(handle, o.key)
    return { handle, option: o }
  })
  return { lines, toKey }
}

// Maps a judge's clusters back to option keys; an unknown handle passes through, so gate_dedup reports it.
function dedup_unhandle(clusters, toKey) {
  return (Array.isArray(clusters) ? clusters : []).map(c => ({ ...c, members: (c.members || []).map(m => toKey.get(m) || m) }))
}

// After both dedup samples fail: the sample whose partition is valid with the fewest soft faults (short topics plus
// unmerged cross-root Jaccard pairs), ties to the earlier sample; null when no sample partitions the keys.
function dedup_best(samples, options, keys, threshold) {
  let best = null
  for (const r of samples) {
    if (!r || !Array.isArray(r.clusters)) continue
    const g = gate_dedup(r.clusters, keys)
    if (!g.ok) continue
    const faults = g.soft.length + gate_dedup_jaccard(options, r.clusters, threshold).violations.length
    if (!best || faults < best.faults) best = { clusters: r.clusters, faults }
  }
  return best
}

// options: [{key, title}], key = `${root}:${branch}:${id}`. Cross-root pairs whose title Jaccard reaches the threshold
// must share a cluster (flow.md §2.5: at 0.4, 9 pairs flagged on the stored run, 0 false positives).
function gate_dedup_jaccard(options, clusters, threshold) {
  const clusterOf = new Map()
  clusters.forEach((c, i) => c.members.forEach(m => clusterOf.set(m, i)))
  const root = k => String(k).split(':')[0]
  const violations = []
  for (let i = 0; i < options.length; i++) {
    for (let j = i + 1; j < options.length; j++) {
      const a = options[i], b = options[j]
      if (root(a.key) === root(b.key)) continue
      const jaccard = txt_jaccard(a.title, b.title)
      if (jaccard >= threshold && (!clusterOf.has(a.key) || clusterOf.get(a.key) !== clusterOf.get(b.key))) violations.push({ a: a.key, b: b.key, jaccard })
    }
  }
  return { ok: !violations.length, violations }
}

function gate_overlap(pairs, rootIds) {
  const errors = []
  for (const p of pairs) {
    if (!rootIds.includes(p.a) || !rootIds.includes(p.b) || p.a === p.b) errors.push(`bad pair ${p.a}/${p.b}`)
    if (txt_words(p.shared_subject) < 3) errors.push(`${p.a}/${p.b}: shared_subject has fewer than 3 words`)
  }
  return { ok: !errors.length, errors }
}

function gate_price_sheet(sheet) {
  const errors = []
  const inst = sheet.instances
  const price = p => typeof p === 'number' && p > 0 && p < 20
  if (inst.length < 5) errors.push(`${inst.length} instances (want at least 5)`)
  if (!inst.some(i => /H100/i.test(i.gpu) && i.n_gpus === 8)) errors.push('no 8x H100 instance')
  for (const i of inst) if (!price(i.per_gpu_usd_h)) errors.push(`${i.n_gpus}x ${i.gpu}: price ${i.per_gpu_usd_h} outside (0, 20)`)
  if (!price(sheet.filesystem.usd_gib_month)) errors.push(`filesystem price ${sheet.filesystem.usd_gib_month} outside (0, 20)`)
  return { ok: !errors.length, errors }
}

// G-plan. pick: {title, branch} (the picked option's title and the branch);
// args: {budget_usd, require_compute_lever: {physical, interp}}. Halt wins over repair; annotations always returned.
function gate_plan(plan, ev, pick, args) {
  const missing = gate_missing(SCHEMA_PLAN, plan, '')
  if (missing.length) return { action: 'halt', reasons: missing.map(p => `missing ${p}`), annotations: [] }
  const budget = args.budget_usd, stated = plan.cost.total_stated
  const usd = x => `$${Number(x).toFixed(2)}`
  const halt = [], repair = [], annotations = []
  const pr = plan.predictions, lv = plan.compute_axis.levels
  if (txt_normalize_title(pr.if_lever) === txt_normalize_title(pr.if_not)) halt.push('if_lever equals if_not')
  if (!txt_has_digit(pr.decision_rule)) halt.push('decision_rule has no number')
  if (lv.length < 2 || Math.max(...lv) / Math.min(...lv) < 2) halt.push(`compute_axis levels ${JSON.stringify(lv)}: need at least 2 levels spanning 2x`)
  if (!plan.phases.length) halt.push('no phase')
  if (!plan.sources.length) halt.push('no source')
  // a restructured plan reaches the same answer sooner: its axis may buy no new answer, so compute_tested "no" does not halt it
  const restructured = gate_restructured(plan)
  if (plan.compute_tested === 'no' && args.require_compute_lever[pick.branch] && !restructured) halt.push(`compute_tested is no: ${plan.compute_tested_why}`)
  if (ev.planned > budget && stated > budget) halt.push(`planned ${usd(ev.planned)} and stated ${usd(stated)} both over ${usd(budget)}`)
  // only errors that stop evaluation route to repair; a value not found in its quote, or a gate naming a non-number,
  // is annotated and left to the dramaturg (an unconfirmed citation is shown as GUESS on the card)
  for (const e of ev.errors) (['quote', 'gate_ref'].includes(e.kind) ? annotations : repair).push(`${e.kind} at ${e.where}: ${e.msg}`)
  if (ev.planned > budget && stated <= budget) repair.push(`planned ${usd(ev.planned)} over ${usd(budget)} while stated ${usd(stated)} is not`)

  if (txt_normalize_title(plan.option_title) !== txt_normalize_title(pick.title))
    annotations.push(`option_title mismatch: plan "${plan.option_title}", pick "${pick.title}" (re-key if it is another option in this branch)`)
  annotations.push(...ev.flags)
  const sourceIds = new Set(plan.sources.map(s => s.id))
  for (const path of Object.keys(gate_card_caps)) {
    const bad = gate_cited_ids(gate_text(plan, path)).filter(id => !sourceIds.has(id))
    if (bad.length) annotations.push(`${path} cites unknown source ${bad.join(', ')}`)
  }
  for (const path of ['anchor.source_id', 'novelty.closest_source_id']) {
    const id = gate_get(plan, path)
    if (id && !sourceIds.has(id)) annotations.push(`${path} ${id} is not in sources`)
  }
  const nv = plan.novelty
  if (typeof nv.prior_max_level === 'number') {
    const src = plan.sources.find(s => s.id === nv.closest_source_id)
    if (!src || !txt_numbers(src.quote).includes(txt_norm_number(String(nv.prior_max_level))))
      annotations.push(`prior_max_level ${nv.prior_max_level} is not in the quote of ${nv.closest_source_id || 'a named source'}`)
  }
  for (const f of ['closest_prior', 'left_open']) if (!String(nv[f] ?? '').trim()) annotations.push(`novelty.${f} is empty`)
  if (restructured) annotations.push(...gate_restructuring_notes(plan, ev))

  if (halt.length) return { action: 'halt', reasons: halt, annotations }
  if (repair.length) return { action: 'repair', reasons: repair, annotations }
  return { action: 'ok', reasons: [], annotations }
}

// Restructured plans: what the method needs to be tested is annotated, never halted (a missing condition or baseline
// lowers the critic's reshape and baseline instead). "Main spend" is the phase with the most core planned dollars.
function gate_restructuring_notes(plan, ev) {
  const r = plan.restructuring, out = []
  for (const f of ['condition', 'condition_phase', 'baseline_sequential', 'baseline_copies']) if (!String(r[f] ?? '').trim()) out.push(`restructuring.${f} is empty`)
  const order = plan.phases.map(p => p.id), cp = String(r.condition_phase ?? '').trim()
  if (cp && !order.includes(cp)) out.push(`restructuring.condition_phase ${cp} is not a phase id`)
  else if (cp) {
    if (!plan.phases.find(p => p.id === cp).gate) out.push(`restructuring.condition_phase ${cp} has no gate`)
    const spend = {}
    for (const l of (ev && ev.lines) || []) if (!l.optional && !(l.instead_of || []).length && typeof l.usd === 'number') spend[l.phase] = (spend[l.phase] || 0) + l.usd
    const main = order.filter(id => id in spend).sort((a, b) => spend[b] - spend[a] || order.indexOf(a) - order.indexOf(b))[0]
    if (main && order.indexOf(cp) >= order.indexOf(main)) out.push(`restructuring.condition_phase ${cp} is not before the phase with the largest planned spend (${main})`)
  }
  const a = plan.anchor || {}
  if (!String(a.independent_code ?? '').trim() && !String(a.tolerance ?? '').trim()) out.push('anchor has neither an independent code nor a tolerance')
  return out
}

// G-cardfields (render path). Every failing reason routes the field to the one repair call; nothing here blocks.
// Record ids are matched only when they hold a digit or "_": plain-word ids ("A", "pilot") would flag ordinary words.
function gate_cardfields(plan, caps) {
  const sourceIds = new Set(plan.sources.map(s => s.id))
  const ids = [...plan.arms, ...plan.phases, ...plan.numbers, ...plan.cost.rates, ...plan.cost.lines, ...(plan.cost.scenarios || []), ...plan.full_scale]
    .map(x => String(x.id)).filter(id => /[\d_]/.test(id))
  const failing = [], annotations = []
  const fail = (field, reason) => {
    const f = failing.find(x => x.field === field)
    if (f) f.reasons.push(reason)
    else failing.push({ field, reasons: [reason] })
  }
  for (const [field, cap] of Object.entries(caps)) {
    if (gate_restructuring_field(field) && !gate_restructured(plan)) continue
    const t = gate_text(plan, field)
    const n = txt_words(t)
    if (n > cap) fail(field, `${n} words (cap ${cap})`)
    const rid = txt_contains_record_id(t, ids)
    if (rid.length) fail(field, `record ids: ${rid.join(', ')}`)
    const codes = [...new Set(txt_coined_codes(t))].filter(c => !rid.includes(c))
    if (codes.length) fail(field, `coined codes: ${codes.join(', ')}`)
    const cost = gate_cost_text(t)
    if (cost) fail(field, cost)
    const bad = gate_cited_ids(t).filter(id => !sourceIds.has(id))
    if (bad.length) fail(field, `unknown sources: ${bad.join(', ')}`)
    for (const s of txt_sentences(t)) if (txt_words(s) > 20) annotations.push(`${field}: a sentence of ${txt_words(s)} words`)
  }
  if (!txt_has_digit(plan.predictions.if_lever) && !txt_has_digit(plan.predictions.if_not))
    fail('predictions.if_lever', 'neither if_lever nor if_not contains a number')
  return { ok: !failing.length, failing, annotations }
}

// Every number in the original field must survive the rewrite (after txt_norm_number).
function gate_number_preservation(orig, rewritten) {
  const kept = new Set(txt_numbers(rewritten))
  return txt_numbers(orig).every(n => kept.has(n))
}

// G-find: each sent ref exactly once; SUPPORTED/PARTIAL carry a page_quote of 15+ characters, other statuses a note of 10+.
function gate_findings(items, sentRefs) {
  const errors = [], degenerate = []
  const sent = new Set(sentRefs)
  for (const ref of sent) {
    const n = items.filter(i => i.ref === ref).length
    if (n !== 1) errors.push(`${ref}: ${n} findings`)
  }
  for (const i of items) {
    if (!sent.has(i.ref)) errors.push(`${i.ref}: not sent`)
    if (!gate_STATUS.includes(i.status)) errors.push(`${i.ref}: status ${i.status}`)
    const quoted = i.status === 'SUPPORTED' || i.status === 'PARTIAL'
    if (String((quoted ? i.page_quote : i.note) ?? '').trim().length < (quoted ? 15 : 10)) degenerate.push(i.ref)
  }
  return { ok: !errors.length && !degenerate.length, errors, degenerate }
}

// Core refs: the core card fields, plus every source a core field cites (its [id]s, the anchor's and the prior's source).
// A restructured plan adds sequential_part: it carries facts such as step counts.
function gate_core_refs(plan) {
  const core = gate_restructured(plan) ? { ...gate_CORE, sequential_part: 'restructuring.sequential_part' } : gate_CORE
  const src = []
  for (const path of Object.values(core)) src.push(...gate_cited_ids(gate_text(plan, path)))
  src.push(gate_get(plan, 'anchor.source_id'), gate_get(plan, 'novelty.closest_source_id'))
  return [...Object.keys(core).map(f => `card:${f}`), ...[...new Set(src.filter(Boolean))].map(id => `src:${id}`)]
}

// Dramaturg items (CONTRACT §2.6), built once for main and replay: every card field with the sources it cites (the anchor
// and the prior also with their own source and value); the sources core fields cite; CITED/PROXY numbers that are
// load-bearing or reach full_scale; and the rates only when no price sheet checked them (opts.rates).
// cardFields: [[ref name, plan path], ...] in card order.
function gate_dramaturg_items(plan, cardFields, opts) {
  const src = Object.fromEntries((plan.sources || []).map(s => [s.id, s]))
  const anchor = plan.anchor || {}, novelty = plan.novelty || {}
  const implicit = { anchor: [anchor.source_id, anchor.published_value], closest_prior: [novelty.closest_source_id, novelty.prior_max_level] }
  const items = []
  for (const [name, path] of cardFields) {
    const text = gate_text(plan, path)
    if (!text || (gate_restructuring_field(path) && !gate_restructured(plan))) continue
    const [sid, value] = implicit[name] || []
    const sources = [...new Set([sid, ...gate_cited_ids(text)])].filter(id => src[id]).map(id => ({ id, url: src[id].url, quote: src[id].quote }))
    items.push({ ref: `card:${name}`, text, sources, ...(value != null ? { value } : {}) })
  }
  for (const ref of gate_core_refs(plan)) {
    const s = ref.startsWith('src:') && src[ref.slice(4)]
    if (s) items.push({ ref, url: s.url, quote: s.quote, supports: s.supports })
  }
  // numbers a full-scale figure reaches, through DERIVED expressions and line expressions (cost's own index)
  const { P } = cost_prepare(plan)
  const lb = new Set(cost_load_bearing(plan).ids)
  const fs = cost_ancestors(P, (plan.full_scale || []).flatMap(f => [...cost_ids(P.ast[`full_scale.${f.id}.usd`]), f.ratio_to]).filter(Boolean))
  for (const x of plan.numbers || []) {
    if ((x.basis === 'CITED' || x.basis === 'PROXY') && (lb.has(x.id) || fs.has(x.id))) {
      items.push({ ref: `num:${x.id}`, name: x.name, value: x.value, unit: x.unit, basis: x.basis, quote: x.quote, page_setting: x.page_setting, differs_in: x.differs_in, url: src[x.source_id] ? src[x.source_id].url : null })
    }
  }
  if (opts && opts.rates) for (const r of (plan.cost && plan.cost.rates) || []) items.push({ ref: `rate:${r.id}`, gpu: r.gpu, gpu_memory_gb: r.gpu_memory_gb, n_gpus: r.n_gpus, per_gpu_usd_h: r.per_gpu_usd_h, url: 'https://lambda.ai/pricing' })
  return items
}

// PASS iff no core item is UNSUPPORTED, CONTRADICTED or UNREACHABLE. num:/rate: items never block on status:
// a CONTRADICTED num: with page_value is re-evaluated at that value and blocks only if the plan is then over budget
// (with no plan, as for planted cards, there is nothing to re-evaluate). Every non-SUPPORTED item that does not block is listed.
function gate_decision(items, coreRefs, plan, ev, given) {
  const core = new Set(coreRefs)
  const blocking = [], listed = []
  for (const it of items) {
    const costItem = it.ref.startsWith('num:') || it.ref.startsWith('rate:')
    const blocks = costItem
      ? plan && it.ref.startsWith('num:') && it.status === 'CONTRADICTED' && typeof it.page_value === 'number' &&
        cost_eval_plan(plan, given, { overrides: { [it.ref.slice(4)]: it.page_value } }).planned > given.budget_usd
      : core.has(it.ref) && ['UNSUPPORTED', 'CONTRADICTED', 'UNREACHABLE'].includes(it.status)
    if (blocks) blocking.push(it)
    else if (it.status !== 'SUPPORTED') listed.push(it)
  }
  return { result: blocking.length ? 'REJECT' : 'PASS', blocking, listed }
}

// G-crit. NA only for lever when compute_axis is absent (never under the current SCHEMA_PLAN, which requires it; the rule is kept),
// and for baseline when the plan is not restructured.
function gate_critique(critique, cardFieldNames, plan, criteria) {
  const errors = []
  for (const c of criteria) {
    const n = critique.scores.filter(s => s.criterion === c).length
    if (n !== 1) errors.push(`${c}: ${n} scores`)
  }
  for (const s of critique.scores) {
    if (!criteria.includes(s.criterion)) { errors.push(`unknown criterion ${s.criterion}`); continue }
    const na = s.value === 'NA'
    const naAllowed = (s.criterion === 'lever' && !plan.compute_axis) || (s.criterion === 'baseline' && !gate_restructured(plan))
    if (na ? !naAllowed : !(Number.isInteger(s.value) && s.value >= 1 && s.value <= 5))
      errors.push(`${s.criterion}: value ${JSON.stringify(s.value)}`)
    const ref = String(s.ref ?? '')
    const resolves = ref.startsWith('card:') ? cardFieldNames.includes(ref.slice(5)) : ref.startsWith('plan:') && gate_get(plan, ref.slice(5)) !== undefined
    if (!na && !resolves) errors.push(`${s.criterion}: ref "${ref}" does not resolve`)
    if (String(s.reason ?? '').trim().length < 15) errors.push(`${s.criterion}: reason under 15 characters`)
  }
  if (critique.decides_by !== 'none' && !plan.phases.some(p => p.id === critique.decides_by)) errors.push(`decides_by ${critique.decides_by} is not a phase id`)
  return { ok: !errors.length, errors }
}

// S0 planted cases (substrate §2.4 cases 6-13, criteria §8.4 case 18, plus Jaccard, number preservation, price sheet).
// Each case is built to make its gate fire; the controls show the same gate passes a valid record.
function gate_selftest() {
  const failures = []
  const check = (name, f) => {
    try { if (!f()) failures.push(name) } catch (e) { failures.push(`${name}: threw ${e && e.message}`) }
  }
  const PLAN = {
    option_title: 'Ensemble size and forecast skill on a synthetic fault',
    question: 'Does forecast skill on a synthetic fault keep rising as the ensemble grows from 32 to 1,024 members?',
    hypothesis: 'Skill levels off below 256 members because model error outweighs sampling error.',
    compute_axis: { quantity: 'ensemble members', unit: 'members', levels: [32, 128, 1024] },
    held_fixed: ['observation network', 'truth runs'],
    predictions: {
      if_lever: 'Skill still rises by more than 0.05 between 256 and 1,024 members.',
      if_not: 'Skill at 256 members is within one standard error of skill at 1,024 members.',
      decision_rule: 'Lever if skill at 1,024 minus skill at 256 exceeds 0.05 and two standard errors.',
      noise_rule: 'Standard error across 5 truth runs.',
      expected: 'if_not',
      expected_why: 'Published ensembles saturate early.',
    },
    compute_tested: 'yes',
    compute_tested_why: 'Ensemble size is bought with GPU time.',
    scored_against: 'Hidden truth runs of the same simulator.',
    arms: [{ id: 'E1', what: 'perfect model' }],
    baseline: { what: 'climatology forecast' },
    anchor: { what: 'Recurrence interval within 1% of the benchmark code [s2].', tolerance: '1%', source_id: 's2' },
    checks: ['reproduce the benchmark first'],
    phases: [{ id: 'P1', what: 'pilot and benchmark' }, { id: 'P2', what: 'ensemble sweep' }],
    numbers: [{ id: 't_sweep', name: 'sweep hours', unit: 'h', basis: 'DESIGN', value: 20 }],
    cost: {
      rates: [{ id: 'h100x8', gpu: 'H100', n_gpus: 8, per_gpu_usd_h: 3.99 }],
      lines: [{ id: 'sweep', phase: 'P2', what: 'ensemble sweep', kind: 'work', rate: 'h100x8', hours: 't_sweep' }],
      total_stated: 638.4,
    },
    full_scale: [],
    outside_budget: [],
    scope_gap: ['real faults'],
    novelty: {
      closest_prior: 'A 150-member ensemble on a lab-scale fault model captured most diversity with 20 members [s1].',
      closest_source_id: 's1', prior_max_level: 150,
      left_open: 'No source reports skill against ensemble size beyond 150 members.',
      decides: 'no', searched: true,
    },
    limits: ['Says nothing about observing stress on a real fault.'],
    test_summary: 'Run ensembles of 32 to 1,024 members on a synthetic fault with known truth, and compare forecast skill across sizes.',
    restructuring: { sequential_part: 'Each ensemble member steps through simulated time in order.', method: 'none' },
    sources: [
      { id: 's1', url: 'https://example.org/a', quote: 'We used a 150-member ensemble.', supports: 'closest prior' },
      { id: 's2', url: 'https://example.org/b', quote: 'The benchmark recurrence interval is 120 years.', supports: 'anchor' },
    ],
    files_read: [],
  }
  const plan = () => JSON.parse(JSON.stringify(PLAN))
  const EV = { ok: true, errors: [], planned: 638.4, flags: [] }
  const PICK = { title: PLAN.option_title, branch: 'physical' }
  const ARGS = { budget_usd: 1000, require_compute_lever: { physical: true, interp: true } }
  const GIVEN = { budget_usd: 1000 }

  check('valid plan: gate_plan ok', () => gate_plan(plan(), EV, PICK, ARGS).action === 'ok')
  check('6 if_lever equal to if_not: halt', () => {
    const p = plan()
    p.predictions.if_not = `  ${p.predictions.if_lever.toUpperCase()}`
    return gate_plan(p, EV, PICK, ARGS).action === 'halt'
  })
  check('7 card field "That costs about $600.": cardfields fails', () => {
    const p = plan()
    p.test_summary = 'That costs about $600.'
    const r = gate_cardfields(p, gate_card_caps)
    return !r.ok && r.failing.some(f => f.field === 'test_summary')
  })
  check('8 unknown source id: cardfields fails', () => {
    const p = plan()
    p.anchor.what = 'Recurrence interval within 1% of the benchmark code [s9].'
    const r = gate_cardfields(p, gate_card_caps)
    return !r.ok && r.failing.some(f => f.field === 'anchor.what')
  })
  check('9 valid card: cardfields passes', () => gate_cardfields(plan(), gate_card_caps).ok)

  const keys = ['R1:physical:W1', 'R2:physical:W1', 'R2:interp:I1']
  check('10 cluster list missing one key: dedup fails', () =>
    gate_dedup([{ topic: 'privacy audits of models', members: keys.slice(0, 2) }], keys).ok === false &&
    gate_dedup([{ topic: 'privacy audits of models', members: keys.slice(0, 2) }, { topic: 'probes on reviewer models', members: keys.slice(2) }], keys).ok)
  check('10c dedup handles: long ids get root:branch:K<n>, clusters map back, unknown handles pass through', () => {
    const o = [{ key: 'R2:interp:A. Inference-time steering' }, { key: 'R2:interp:B. Failure detection' }, { key: 'R3:physical:W1' }]
    const h = dedup_handles(o)
    const back = dedup_unhandle([{ topic: 'steering and failure detection', members: ['R2:interp:K1', 'R2:interp:K2'] }, { topic: 'one other option', members: ['R3:physical:K1', 'R2:interp:A'] }], h.toKey)
    return h.lines.map(l => l.handle).join() === 'R2:interp:K1,R2:interp:K2,R3:physical:K1'
      && back[0].members.join('|') === 'R2:interp:A. Inference-time steering|R2:interp:B. Failure detection'
      && back[1].members.join('|') === 'R3:physical:W1|R2:interp:A'
  })
  check('10b short topic: soft fault, partition still ok; dedup_best keeps the valid sample with fewer faults', () => {
    const short = [{ topic: 'privacy audits', members: keys.slice(0, 2) }, { topic: 'probes on reviewer models', members: keys.slice(2) }]
    const g = gate_dedup(short, keys)
    const opts = keys.map(k => ({ key: k, title: k }))
    const best = dedup_best([{ clusters: [{ topic: 'one cluster missing keys', members: keys.slice(0, 1) }] }, { clusters: short }], opts, keys, 0.4)
    return g.ok && g.soft.length === 1 && best && best.faults === 1 && best.clusters === short
      && dedup_best([{ clusters: [{ topic: 'one cluster missing keys', members: keys.slice(0, 1) }] }], opts, keys, 0.4) === null
  })

  const OPTS = [{ id: 'W1' }, { id: 'W2' }]
  const oc = (value, reason) => [
    { id: 'W1', distance: 'SAME', distance_reason: 'same object of study', scores: [{ criterion: 'stakes', value: 4, reason: 'a lab chooses what to buy on it' }, { criterion: 'open', value, reason }] },
    { id: 'W2', distance: 'ELSEWHERE', distance_reason: 'a different field', scores: [{ criterion: 'stakes', value: 2, reason: 'nobody changes course on it' }, { criterion: 'open', value: 3, reason: 'partly measured up to 64 runs' }] },
  ]
  check('option critic valid: gate_oc ok', () => gate_oc(oc(5, 'no published sweep above 150 members'), OPTS, ['stakes', 'open']).ok)
  check('11 option-critic reason equal to the criterion: degenerate', () => {
    const r = gate_oc(oc(5, 'open'), OPTS, ['stakes', 'open'])
    return !r.ok && r.degenerate.includes('W1')
  })
  check('18 option-critic value "NA": gate_oc fails', () => !gate_oc(oc('NA', 'no published sweep above 150 members'), OPTS, ['stakes', 'open']).ok)

  const core = gate_core_refs(PLAN)
  const item = (ref, status) => ({ ref, status, page_quote: 'a sentence quoted from the page', note: 'what the page says about it' })
  check('12 one CONTRADICTED core item: REJECT', () => {
    const r = gate_decision([item('card:test_summary', 'CONTRADICTED'), item('src:s1', 'SUPPORTED')], core, PLAN, EV, GIVEN)
    return r.result === 'REJECT' && r.blocking.length === 1
  })
  check('13a only PARTIAL: PASS, item listed', () => {
    const r = gate_decision([item('card:test_summary', 'PARTIAL'), item('src:s1', 'SUPPORTED')], core, PLAN, EV, GIVEN)
    return r.result === 'PASS' && r.listed.length === 1 && r.listed[0].ref === 'card:test_summary'
  })
  check('13b CONTRADICTED only in a non-core ref: PASS, item listed', () => {
    const r = gate_decision([item('card:limits', 'CONTRADICTED'), item('card:question', 'SUPPORTED')], core, PLAN, EV, GIVEN)
    return r.result === 'PASS' && r.listed.length === 1 && r.listed[0].ref === 'card:limits'
  })

  const TITLES = [{ key: 'R1:physical:W3', title: 'Training-data attribution and data valuation' }, { key: 'R4:interp:I2', title: 'Probe-based data attribution' }]
  check('Jaccard-0.4 title pair split across clusters: violation', () =>
    !gate_dedup_jaccard(TITLES, [{ topic: 'training data attribution', members: ['R1:physical:W3'] }, { topic: 'probe based attribution', members: ['R4:interp:I2'] }], 0.4).ok &&
    gate_dedup_jaccard(TITLES, [{ topic: 'training data attribution', members: ['R1:physical:W3', 'R4:interp:I2'] }], 0.4).ok)

  check('number preservation catches a dropped number', () =>
    !gate_number_preservation('Skill rises by 0.05 beyond 1,024 members.', 'Skill keeps rising beyond 1024 members.') &&
    gate_number_preservation('Skill rises by 0.05 beyond 1,024 members.', 'Skill rises by 0.05 past 1024 members.'))

  const inst = (gpu, n, p) => ({ gpu, gpu_memory_gb: 80, n_gpus: n, per_gpu_usd_h: p, page_text: `${n}x ${gpu} $${p}` })
  const sheet = extra => ({
    read_at: '2026-10-16',
    instances: [inst('A100', 1, 1.29), inst('A100', 8, 1.79), inst('H100', 1, 2.49), inst('H100', 2, 2.39), inst('B200', 8, 4.99), ...extra],
    filesystem: { usd_gib_month: 0.2, page_text: '$0.20 per GiB per month', example: false },
  })
  check('price sheet without 8x H100: rejected', () => !gate_price_sheet(sheet([])).ok && gate_price_sheet(sheet([inst('H100', 8, 2.99)])).ok)

  // Planted reshape/baseline set (criteria version check): two highs that remove a step-after-step dependency, two lows
  // that only run independent work side by side. Only the gates are tested here; the judges' calibration runs on the model.
  const why = 'a reason long enough to keep'
  const opt = (id, title, compute_open, sequential) => ({ id, title, summary: `${title}.`, root_link: 'none', compute_open, sequential, source_urls: [] })
  const OPT_SET = [
    opt('H1', 'Smoothing a long linear-Gaussian state series', 'none', 'One smoothing pass waits on 1,000,000 steps, each on the last state; few runs are needed and one run keeps under 5% of a GPU busy. The update is associative, so a parallel prefix computation could run all steps at once while the state stays small; nearest attempt https://example.org/prefix'),
    opt('H2', 'Aligning two long sequences by dynamic programming', 'settled: alignment accuracy does not change with compute https://example.org/dp', 'Filling one table waits cell by cell, 100,000,000 cells for two sequences of 10,000; one table leaves most of a GPU idle. Cells on one anti-diagonal do not depend on each other, so each anti-diagonal could run at once when the sequences are long; nearest attempt https://example.org/wavefront'),
    opt('L1', 'Eight independent fine-tuning jobs', 'Jobs: published sweeps stop at 4 https://example.org/sweep; unknown above.', 'none: the answer needs eight independent jobs, one per GPU, which already fill the hardware.'),
    opt('L2', 'Ensemble data assimilation of fault stress', 'Members: one study used 150 https://example.org/a; unknown above.', 'Each ensemble member steps through simulated time in order; the answer needs hundreds of members, so copies side by side already fill the GPUs.'),
  ]
  const OPT_SCORES = OPT_SET.map((o, i) => ({ id: o.id, distance: 'SAME', distance_reason: why,
    scores: [['stakes', 4], ['open', 3], ['reshape', [5, 5, 1, 2][i]]].map(([criterion, value]) => ({ criterion, value, reason: why })) }))
  const STATUS = { H1: 'none', H2: 'settled', L1: 'open', L2: 'open' }
  check('planted reshape set: options pass G-opt and G-oc; totals leave reshape out', () =>
    gate_opt(OPT_SET).ok && !gate_opt([...OPT_SET.slice(0, 3), { ...OPT_SET[3], sequential: ' ' }]).ok &&
    gate_oc(OPT_SCORES, OPT_SET, ['stakes', 'open', 'reshape']).ok &&
    JSON.stringify(gate_totals(OPT_SCORES, ['stakes', 'open', 'reshape'], STATUS)) === JSON.stringify({ H1: 5, H2: 5, L1: 7, L2: 7 }))

  const stub = (o, over) => Object.assign(plan(), { option_title: o.title, novelty: { ...PLAN.novelty, prior_max_level: null } }, over)
  const fast = (o, quantity, levels, sequential_part, method, condition) => stub(o, {
    question: `Can ${o.title.toLowerCase()} reach the sequential answer sooner on one GPU by computing dependent steps at the same time?`,
    hypothesis: 'The dependency can be combined in rounds, so the same answer arrives in far fewer sequential rounds.',
    compute_axis: { quantity, unit: 'steps', levels },
    predictions: { ...PLAN.predictions, if_lever: 'The parallel version beats both baselines beyond 100,000 steps at the same answer.',
      if_not: 'Below 100,000 steps the tuned sequential code stays faster, because rounds cost more than they save.',
      decision_rule: 'Lever if the parallel run is at least 2 times faster than both baselines at the longest chain.' },
    compute_tested: 'no', compute_tested_why: 'The same answer sooner; no new answer is bought.',
    anchor: { what: 'Match the tuned sequential result within a relative error of 1e-6.', tolerance: '1e-6 relative', independent_code: 'the tuned sequential code' },
    phases: [{ id: 'P0', what: 'time one parallel pass on a short chain', gate: { on: 't_sweep', op: '>=', value: 1, else: 'stop' } }, { id: 'P1', what: 'time every arm at three chain lengths' }],
    restructuring: { sequential_part, method, condition, condition_phase: 'P0', baseline_sequential: 'compiled, vectorised sequential code', baseline_copies: '64 independent sequential copies side by side on the same GPU' },
    test_summary: 'Time the parallel version, tuned sequential code and 64 copies side by side at three chain lengths, each to the same answer.',
  })
  const slow = (o, sequential_part) => stub(o, { restructuring: { sequential_part, method: 'none' } })
  const HIGH = [
    fast(OPT_SET[0], 'steps in the chain', [1e4, 1e5, 1e6], 'One smoothing pass updates a small state 1,000,000 times, each step waiting on the one before.',
      'The update is associative, so a parallel prefix computation combines all steps at once in about 20 rounds.', 'State dimension at most 16, checked by timing one pass at 10,000 steps.'),
    fast(OPT_SET[1], 'cells in the table', [1e6, 1e7, 1e8], 'Filling one alignment table visits 100,000,000 cells, each waiting on its left, upper and diagonal neighbours.',
      'Cells on one anti-diagonal depend only on earlier anti-diagonals, so each anti-diagonal is computed at once across threads.', 'Sequences of at least 10,000, checked by timing one table of that size.'),
  ]
  const LOW = [slow(OPT_SET[2], 'Each of eight jobs steps through its own data in order.'), slow(OPT_SET[3], 'Each ensemble member steps through about 20,000 time steps in order.')]
  const EV2 = { ...EV, lines: [{ id: 'pilot', phase: 'P0', kind: 'work', usd: 40, optional: false, instead_of: [] }, { id: 'sweep', phase: 'P2', kind: 'work', usd: 598.4, optional: false, instead_of: [] }] }
  const EVH = { ...EV, lines: [{ id: 'pilot', phase: 'P0', kind: 'work', usd: 40, optional: false, instead_of: [] }, { id: 'main', phase: 'P1', kind: 'work', usd: 598.4, optional: false, instead_of: [] }] }
  const crit = (p, baseline) => ({ scores: [['stakes', 4], ['reshape', 5], ['baseline', baseline]].map(([criterion, value]) => ({ criterion, value, ref: 'card:test_summary', reason: why })),
    decides_by: p.phases[p.phases.length - 1].id, decides_by_reason: why })
  const CRIT3 = ['stakes', 'reshape', 'baseline']
  const CF = [['question', 'question'], ['sequential_part', 'restructuring.sequential_part'], ['method', 'restructuring.method'], ['test_summary', 'test_summary']]
  check('planted highs: restructured; compute_tested no does not halt; no annotation; sequential_part is core and a card field within its cap', () => HIGH.every(p => {
    const g = gate_plan(p, EVH, { title: p.option_title, branch: 'physical' }, ARGS), cf = gate_cardfields(p, gate_card_caps)
    return gate_restructured(p) && g.action === 'ok' && !g.annotations.length && gate_core_refs(p).includes('card:sequential_part') && cf.ok &&
      gate_dramaturg_items(p, CF).some(i => i.ref === 'card:method')
  }))
  check('planted highs: baseline must be scored (NA fails G-crit)', () => HIGH.every(p =>
    gate_critique(crit(p, 4), CF.map(f => f[0]), p, CRIT3).ok && !gate_critique(crit(p, 'NA'), CF.map(f => f[0]), p, CRIT3).ok))
  check('planted lows: not restructured; restructuring fields neither core, nor checked, nor sent; baseline NA accepted', () => LOW.every(p => {
    const long = { ...p, restructuring: { ...p.restructuring, sequential_part: 'word '.repeat(30) } }
    return !gate_restructured(p) && gate_plan(p, EV2, { title: p.option_title, branch: 'physical' }, ARGS).action === 'ok' &&
      !gate_core_refs(p).includes('card:sequential_part') && gate_cardfields(long, gate_card_caps).ok &&
      !gate_dramaturg_items(p, CF).some(i => /^card:(sequential_part|method)$/.test(i.ref)) && gate_critique(crit(p, 'NA'), CF.map(f => f[0]), p, CRIT3).ok
  }))
  check('not restructured: compute_tested no halts where the lever is required; a missing restructuring counts as none', () => {
    const p = { ...LOW[1], compute_tested: 'no' }, q = plan()
    delete q.restructuring
    return gate_plan(p, EV2, { title: p.option_title, branch: 'physical' }, ARGS).action === 'halt' && !gate_restructured(q) && !gate_core_refs(q).includes('card:sequential_part')
  })
  check('restructured: empty condition and baselines, an ungated or late condition phase, an anchor with neither code nor tolerance annotate, never halt', () => {
    const p = JSON.parse(JSON.stringify(HIGH[0]))
    Object.assign(p.restructuring, { condition: '', baseline_sequential: ' ', baseline_copies: undefined })
    const a = gate_plan(p, EVH, { title: p.option_title, branch: 'physical' }, ARGS)
    const late = JSON.parse(JSON.stringify(HIGH[0]))
    late.restructuring.condition_phase = 'P1'
    delete late.phases[1].gate
    const b = gate_plan(late, EVH, { title: late.option_title, branch: 'physical' }, ARGS)
    const none = JSON.parse(JSON.stringify(HIGH[0]))
    none.restructuring.condition_phase = 'P9'
    none.anchor = { absent_reason: 'no reference code' }
    const c = gate_plan(none, EVH, { title: none.option_title, branch: 'physical' }, ARGS).annotations.join('\n')
    return a.action === 'ok' && ['condition', 'baseline_sequential', 'baseline_copies'].every(f => a.annotations.includes(`restructuring.${f} is empty`)) &&
      b.action === 'ok' && b.annotations.includes('restructuring.condition_phase P1 has no gate') && b.annotations.some(x => /P1 is not before the phase with the largest planned spend \(P1\)/.test(x)) &&
      /P9 is not a phase id/.test(c) && /neither an independent code nor a tolerance/.test(c)
  })

  return { ok: !failures.length, failures }
}


// ---- src/render.js ----
// ---------- render: card, table, inventory, frontier, RESULT.md ----------
// Zero-token output the human reads (options-and-card §4, §6; criteria §8.5; cost §8.4). Nothing is dropped
// silently (substrate S10): every pick, halts included, gets a card and a table row.
//
// ctx, one per pick, is also a table row: the contract's {pick, option, root_question, plan, eval, given,
//   findings: [FINDINGS, FINDINGS|null], decision, critique|null, beyond_prior, annotations, halted: {gate, reasons}|null}
// plus three fields (CONTRACT, changes after build):
//   decision2      gate_decision on findings[1], or null; gives "PASS 2/2" or "PASS 1/2"
//   producer_path  producer.md, linked from the card (main.js and replay.js both set it)
//   n_options      options in the pick's branch, optional; gives the "/11" of "random 8/11"
// option = the OPTIONS item merged with its OPTION_SCORES item: {id, title, distance, distance_reason, scores: [{criterion, value, reason}]}.
// Card text holds no em-dash: the card is quoted inside the critic's prompt.

const render_get = (o, path) => path.split(/[.[\]]+/).filter(Boolean).reduce((x, k) => (x == null ? undefined : x[k]), o)
const render_num = n => (Number.isInteger(n) ? String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : String(n))
const render_usd = x => `$${render_num(Math.round(x))}`
const render_cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0)
const render_cell = s => (s == null ? '' : String(s)).replace(/\|/g, '\\|').replace(/\s*\n\s*/g, ' ')
const render_score = (scores, c) => { const s = (scores || []).find(x => x.criterion === c); return s ? s.value : undefined }
const render_label = pick => pick.key.split(':').map(s => (s === 'physical' ? 'phys' : s)).join('·')
const render_anchor_id = pick => `card-${pick.key.replace(/[^A-Za-z0-9_-]+/g, '-')}`
// as gate_restructured: restructuring.method, trimmed and lowercased, is not "none" (missing or empty counts as none)
const render_restructured = plan => !['', 'none'].includes(String(render_get(plan || {}, 'restructuring.method') ?? '').trim().toLowerCase())

// The tolerance is printed by construction: it was lost or misstated in 3 of 3 PASS write-ups (options-and-card N5).
function render_anchor(a) {
  if (!a) return undefined
  if (!a.what) return a.absent_reason && `None: ${a.absent_reason}`
  return a.tolerance && !a.what.includes(a.tolerance) ? `${a.what} Tolerance: ${a.tolerance}.` : a.what
}

// Card fields by the name a critique ref uses ("card:<name>").
const render_fields = {
  question: p => p.question,
  closest_prior: p => render_get(p, 'novelty.closest_prior'),
  left_open: p => render_get(p, 'novelty.left_open'),
  hypothesis: p => p.hypothesis,
  if_lever: p => render_get(p, 'predictions.if_lever'),
  if_not: p => render_get(p, 'predictions.if_not'),
  test_summary: p => p.test_summary,
  anchor: p => render_anchor(p.anchor),
  limits: p => (p.limits || []).join(' '),
  sequential_part: p => render_get(p, 'restructuring.sequential_part'),
  method: p => render_get(p, 'restructuring.method'),
}

// The text a critique ref points at: a card field, else a plan field path. The script prints it next to the score (criteria §8.3).
function render_ref(plan, ref) {
  const path = String(ref).replace(/^(card|plan):/, '')
  const v = render_fields[path] ? render_fields[path](plan) : render_get(plan, path)
  const s = v === undefined ? 'not found' : typeof v === 'string' ? v : JSON.stringify(v)
  return s.length > 240 ? `${s.slice(0, 240)}…` : s
}

// Script line: the axis span, the closest prior's level against it, and whether prior art was searched (options-and-card §3).
function render_axis(plan, beyond) {
  const ax = plan.compute_axis, nv = plan.novelty || {}, out = []
  if (ax && ax.levels && ax.levels.length) {
    const q = String(ax.quantity)
    out.push(`${q[0].toUpperCase()}${q.slice(1)}: ${render_num(Math.min(...ax.levels))}–${render_num(Math.max(...ax.levels))} ${ax.unit}, ${ax.levels.length} levels.`)
  } else out.push('None.')
  if (nv.prior_max_level == null) out.push('Closest prior: not on this axis.')
  else out.push(`Closest prior: ${render_num(nv.prior_max_level)}${nv.closest_source_id ? ` [${nv.closest_source_id}]` : ''}${beyond === true ? ', beyond it' : beyond === false ? ', not beyond it' : ''}.`)
  if (nv.searched === false) out.push('Prior art checked without web search.')
  return out.join(' ')
}

function render_verdict(r) {
  if (r.halted) return `halted: ${r.halted.gate}`
  if (!r.decision) return 'not judged'
  if (r.decision.result !== 'PASS') return `REJECT (${r.decision.blocking.length} blocking)`
  return `PASS ${r.decision2 && r.decision2.result === 'PASS' ? 2 : 1}/${r.decision2 ? 2 : 1}`
}

// Payoff as dollars at decides_by (criteria §5): spend through that phase counted as cost counts spend through a
// pilot (base lines only, storage out when the budget does not cover it), the plan total, and the load-bearing GUESS inputs.
function render_payoff(r) {
  const ev = r.eval
  if (!ev || !r.plan) return 'not computed'
  const tail = `plan ${render_usd(ev.planned)} · ${(ev.uncertain || []).filter(u => u.basis === 'GUESS').length} GUESS`
  const at = r.critique && r.critique.decides_by
  if (!at) return `not judged · ${tail}`
  if (at === 'none') return `none · ${tail}`
  const order = (r.plan.phases || []).map(p => p.id), idx = order.indexOf(at)
  const storageOut = r.given && r.given.budget_covers_storage === false
  const usd = ev.lines
    .filter(l => !l.optional && !(l.instead_of || []).length && !(storageOut && l.kind === 'storage'))
    .filter(l => order.indexOf(l.phase) >= 0 && order.indexOf(l.phase) <= idx)
    .reduce((s, l) => s + l.usd, 0)
  return `${render_usd(usd)} at ${at} · ${tail}`
}

function render_card(ctx) {
  const { pick, plan, option: o } = ctx, ev = ctx.eval
  // Outcome labels follow compute_tested: a test that varies no compute quantity states a hypothesis, not a lever,
  // unless the plan is restructured (the restructuring is the lever; the gates halt only an unrestructured "no").
  const lever = !plan || plan.compute_tested !== 'no' || render_restructured(plan)
  const exp = plan && render_get(plan, 'predictions.expected')
  const expects = exp && { if_lever: lever ? 'the lever' : 'the hypothesis holds', if_not: lever ? 'not the lever' : 'the hypothesis fails', unsure: 'unsure' }[exp]
  const head = [
    pick.root, pick.branch, `${pick.kind} pick`,
    o.distance && `distance ${o.distance}`,
    plan && plan.compute_tested && `compute tested: ${plan.compute_tested}`,
    expects && `plan expects: ${expects}`,
    ctx.halted ? `halted: ${ctx.halted.gate}` : ctx.decision && ctx.decision.result,
  ].filter(Boolean).join(' · ')
  const out = [`<a id="${render_anchor_id(pick)}"></a>**${o.id} · ${String(o.title).replace(/[.?!]$/, '')}.** ${head}`]

  if (plan) {
    const f = k => render_fields[k](plan) || 'not given'
    out.push(
      `**Question.** ${f('question')}`,
      `**What is known.** ${[render_fields.closest_prior(plan), render_fields.left_open(plan)].filter(Boolean).join(' ') || 'not given'}`,
      `**Hypothesis.** ${f('hypothesis')}`)
    // A restructured plan says which chain it computes at the same time and how; any other plan gets a script line.
    const rs = render_restructured(plan)
    if (rs) out.push(`**Restructuring.** ${[f('sequential_part'), f('method')].join(' ')}`)
    out.push(
      `**${lever ? 'If compute is the lever' : 'If the hypothesis holds'}.** ${f('if_lever')}`,
      `**If not.** ${f('if_not')}`,
      `**Test.** ${f('test_summary')}`,
      `*Compute axis.* ${render_axis(plan, ctx.beyond_prior)}`)
    if (!rs) out.push('*Restructuring.* none.')
    out.push(
      `**Check first.** ${f('anchor')}`,
      `**Would not show.** ${f('limits')}`,
      `*Cost.* ${ev ? cost_render_short(ev, plan) : 'not computed'}`)
  }

  // A halt replaces the judged part: no dramaturg or critic ran.
  if (ctx.halted) out.push(`**Halted at ${ctx.halted.gate}.** ${ctx.halted.reasons.join('; ')}`)
  else {
    const why = ctx.critique && ctx.critique.decides_by_reason ? ` (critic: ${ctx.critique.decides_by_reason.replace(/\.$/, '')})` : ''
    out.push(`**Judges.** Dramaturg: ${render_verdict(ctx)}. Decides at: ${render_payoff(ctx)}${why}.`)
  }

  // Appendix, not counted in the word budget, in the contract's order.
  if (ev && plan) {
    out.push(`**Cost block.**\n\`\`\`\n${cost_render_block(ev, plan, ctx.given)}\n\`\`\``)
    out.push(`**Derivations.**\n\`\`\`\n${cost_render_derivations(ev, plan)}\n\`\`\``)
  }
  const samples = (ctx.findings || []).map((fs, i) => fs && fs.items.filter(it => it.status !== 'SUPPORTED').map(it =>
    `- sample ${i + 1} · \`${it.ref}\` ${it.status} · page: "${it.page_quote}" · note: ${it.note}${it.page_value != null ? ` · page value ${it.page_value}` : ''}`))
  if (samples.some(Boolean)) out.push(`**Dramaturg, not SUPPORTED.**\n${samples.filter(Boolean).flat().join('\n') || 'none'}`)
  if (ctx.critique) out.push(`**Critic.**\n${ctx.critique.scores.map(s => `- ${s.criterion} ${s.value} · \`${s.ref}\` "${render_ref(plan, s.ref)}" · ${s.reason}`).join('\n')}`)
  if (o.scores) out.push(`**Option critic.**\n${o.scores.map(s => `- ${s.criterion} ${s.value}: ${s.reason}`).concat(o.distance ? [`- distance ${o.distance}: ${o.distance_reason}`] : []).join('\n')}`)
  if (plan) {
    const g = path => render_get(plan, path) ?? 'not given', sr = render_get(plan, 'novelty.searched')
    out.push(`**Producer says (not judged).** expected ${g('predictions.expected')} (${g('predictions.expected_why')}); compute_tested ${g('compute_tested')} (${g('compute_tested_why')}); decides ${g('novelty.decides')}; searched ${sr === true ? 'yes' : sr === false ? 'no' : 'not given'}.`)
  }
  if ((ctx.annotations || []).length) out.push(`**Annotations.**\n${ctx.annotations.map(a => `- ${a}`).join('\n')}`)
  if (ctx.root_question) out.push(`**Root question (${pick.root}).** ${ctx.root_question}`)
  out.push(`**Producer file.** ${ctx.producer_path ? `[producer.md](${ctx.producer_path})` : 'path not given'}`)
  return out.join('\n\n')
}

// Option critic → critic on the shared constructs (criteria §4). Only a drop of 2 or more in open or stakes is labelled:
// an `open` drop means the critic found a prior; a `stakes` drop is "narrowed" when the plan lists a scope gap.
// reshape is never labelled: the option scores the potential, the card the design.
function render_pair(r, c) {
  const a = render_score(r.option && r.option.scores, c), b = render_score(r.critique && r.critique.scores, c)
  const show = v => (typeof v === 'number' ? v : '—')
  const drop = c !== 'reshape' && typeof a === 'number' && typeof b === 'number' && a - b >= 2
  const label = !drop ? '' : c === 'open' ? ' prior found' : (r.plan.scope_gap || []).length ? ' narrowed' : ' unexplained'
  return `${show(a)} → ${show(b)}${label}`
}

function render_picked(r) {
  const p = r.pick, d = r.option && r.option.distance
  const rank = typeof p.rank === 'number' ? ` ${p.rank}${r.n_options ? `/${r.n_options}` : ''}` : ''
  return `${p.kind}${rank}${d ? ` · ${d}` : ''}${p.tie_note ? `, ${p.tie_note}` : ''}`
}

// Index, one row per pick (criteria §8.5). Within each root: PASS, REJECT, halted; then card lever, open, stakes
// (higher first), then key. No totals.
function render_table(rows) {
  const group = r => (r.halted || !r.decision ? 2 : r.decision.result === 'PASS' ? 0 : 1)
  const card = (r, c) => render_score(r.critique && r.critique.scores, c)
  const sortv = (r, c) => (typeof card(r, c) === 'number' ? card(r, c) : -1)
  const shown = (r, c) => (typeof card(r, c) === 'number' ? card(r, c) : '—')
  const root = r => r.pick.root ?? 'seed'   // seed picks have no root; 'seed' sorts after R1..R5
  const sorted = [...rows].sort((x, y) => render_cmp(root(x), root(y)) || group(x) - group(y) ||
    sortv(y, 'lever') - sortv(x, 'lever') || sortv(y, 'open') - sortv(x, 'open') || sortv(y, 'stakes') - sortv(x, 'stakes') ||
    render_cmp(x.pick.key, y.pick.key))
  const lines = [
    '| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |',
    '|---|---|---|---|---|---|---|---|---|---|---|---|',
    ...sorted.map(r => `| ${[
      `[${render_label(r.pick)}](#${render_anchor_id(r.pick)}) ${r.option.title}`,
      render_verdict(r),
      render_picked(r),
      render_get(r.plan, 'predictions.expected') || '—',
      shown(r, 'lever'),
      render_pair(r, 'open'),
      render_pair(r, 'stakes'),
      shown(r, 'verifiable'),
      r.pick.branch === 'interp' ? shown(r, 'internals') : '—',
      render_pair(r, 'reshape'),
      shown(r, 'baseline'),
      render_payoff(r),
    ].map(render_cell).join(' | ')} |`),
  ]
  if (!rows.length) lines.push('| no picks | | | | | | | | | | | |')
  return lines.join('\n')
}

function render_inventory(inventory) {
  return [
    '| Option | Title | Distance | Cluster | Total | Status | Reason |',
    '|---|---|---|---|---|---|---|',
    ...[...inventory].sort((a, b) => render_cmp(a.key, b.key)).map(o =>
      `| ${[o.key, o.title, o.distance, o.cluster_topic, o.total, o.status, o.reason].map(render_cell).join(' | ')} |`),
  ].join('\n')
}

// Per root: options whose compute effect is measured beyond reach but whose stakes are high. Listed, never produced.
function render_frontier(frontier) {
  if (!frontier.length) return 'None.'
  const out = []
  let root = null
  for (const f of [...frontier].sort((a, b) => render_cmp(a.root, b.root) || render_cmp(a.key, b.key))) {
    if (f.root !== root) { root = f.root; out.push(`${out.length ? '\n' : ''}**${root}**`) }
    out.push(`- ${f.title} (${f.distance}): ${f.compute_open}`)
  }
  return out.join('\n')
}

// RESULT.md. header_counts as main.js builds it: {picks, pass, u4 and u3 (on-goal cards), halted: {gate: n}, ...};
// table, frontier and inventory are rendered strings, cards an array of rendered cards, log an array of lines.
function render_result({ header_counts: h, table, frontier, cards, inventory, log }) {
  const halts = Object.keys(h.halted || {}).sort().map(g => `${g} ${h.halted[g]}`).join(', ') || 'none'
  return [
    '# Result',
    `Picks ${h.picks} · PASS ${h.pass} · on-goal cards U4 ${h.u4} · U3 ${h.u3} · halts: ${halts}`,
    '## Table', table,
    '## Frontier (listed, not produced)', frontier,
    '## Cards', cards.join('\n\n---\n\n') || 'None.',
    '## Inventory', inventory,
    '## Log', `\`\`\`\n${log.join('\n')}\n\`\`\``,
  ].join('\n\n')
}

// Planted cases: section order, outcome labels, the Restructuring section or script line, a halted card, the word budget,
// and the table sort. The fixture is the W1 turbulence card of options-and-card §4.2 (REJECT, plan expects the lever).
function render_selftest() {
  const failures = []
  const check = (ok, msg) => { if (!ok) failures.push(msg) }
  const W1 = {
    pick: { key: 'R5:physical:W1', root: 'R5', branch: 'physical', kind: 'top', rank: 1, total: 9, tie_note: null, replaced: [] },
    n_options: 9,
    option: { id: 'W1', title: 'Turbulent fluid flow (direct numerical simulation)', distance: 'ELSEWHERE', distance_reason: 'Fluid turbulence is not the root question\'s system.',
      scores: [{ criterion: 'stakes', value: 4, reason: 'Turbulence-model choice for engineering flows turns on it.' }, { criterion: 'open', value: 1, reason: 'Settled: published runs reach far larger grids.' }] },
    root_question: 'What limits general-purpose robot manipulation? Is it compute-bound?',
    plan: {
      option_title: 'Turbulent fluid flow (direct numerical simulation)',
      question: 'On one rented machine, does turbulence-simulation cost grow as Reynolds number to the sixth? Does resolving every scale remove turbulence-model error?',
      hypothesis: 'Compute removes turbulence-model error by resolving the scales the model approximates. The plan expects this for small-scale statistics only.',
      compute_axis: { quantity: 'grid points per side', unit: 'points', levels: [128, 256, 512, 1024, 2048] },
      held_fixed: ['viscosity', 'forcing', 'time scheme'],
      predictions: { if_lever: 'Unmodelled error on velocity-gradient statistics falls toward zero at full resolution, while a Smagorinsky model keeps an error floor.',
        if_not: 'The plan states no outcome that would count against the claim. Its predictions confirm expected behaviour: the cost exponent nears six above 512³.',
        decision_rule: 'Lever if gradient error at 1024³ is below 5% while the model error stays above 20%.', noise_rule: 'three seeds per grid',
        expected: 'if_lever', expected_why: 'Resolution removes modelling error by construction.' },
      compute_tested: 'yes', compute_tested_why: 'Grid size is the only varied quantity.',
      scored_against: 'the published 1024³ run', arms: [{ id: 'A1', what: 'direct simulation' }, { id: 'A2', what: 'Smagorinsky model' }],
      baseline: { what: 'Smagorinsky model at three constants' },
      anchor: { what: 'The 1024³ run must reproduce the published Taylor Reynolds number 418 within 4%, energy within 3%, spectrum within 10%.', published_value: 418, tolerance: '4%', source_id: 's2' },
      checks: ['energy balance closes within 1%'],
      phases: [{ id: 'B', what: 'benchmark step times' }, { id: 'M', what: 'grid ladder and model runs' }],
      numbers: [{ id: 't_step', name: 'seconds per step at 1024³ on 8 GPUs', unit: 's', basis: 'GUESS', value: 0.8, rests_on: 'textbook operation count', measured_by: 'B' },
        { id: 'steps', name: 'steps in the ladder', unit: 'steps', basis: 'DESIGN', value: 21825 }],
      cost: { rates: [{ id: 'r8', gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99 }],
        lines: [{ id: 'bench', phase: 'B', what: 'benchmark', kind: 'work', rate: 'r8', hours: '1.25' }, { id: 'main', phase: 'M', what: 'ladder', kind: 'work', rate: 'r8', hours: 't_step * steps / 3600' }],
        scenarios: [], yields: [], total_stated: 194.71 },
      full_scale: [], outside_budget: [], scope_gap: [],
      novelty: { closest_prior: 'Published simulations reach Taylor Reynolds number 1,200 to 1,300; the run this plan copies reached 418.', closest_source_id: 's4', prior_max_level: 8192,
        left_open: 'The cost law follows from the textbook operation count.', decides: 'partly', searched: false },
      limits: ['The plan cannot move the research frontier: it stays below published Reynolds numbers.', 'Small grids under-use the GPUs, which distorts the measured cost law.'],
      test_summary: 'A spectral solver copies the published 1024³ run\'s viscosity, forcing and time scheme on one to eight GPUs. Grids rise from 128³ to 1024³, and to 2048³ only if affordable. Turbulence-model runs at three constants compete at equal spend.',
      sources: [{ id: 's2', url: 'https://example.org/dns418', quote: 'Taylor Reynolds number 418', supports: 'anchor' }, { id: 's4', url: 'https://example.org/dns8192', quote: '8192³', supports: 'closest prior' }],
      files_read: [],
    },
    eval: { ok: true, errors: [], numbers: { t_step: 0.8, steps: 21825 }, rates: { r8: 31.92 }, rate_corrections: [],
      lines: [{ id: 'bench', phase: 'B', kind: 'work', hours: 1.25, usd: 39.9, optional: false, instead_of: [], time_box: false, need_h: null, margin: null },
        { id: 'main', phase: 'M', kind: 'work', hours: 4.85, usd: 154.81, optional: false, instead_of: [], time_box: false, need_h: null, margin: null }],
      planned: 194.71, planned_with_options: 194.71, alternatives: [], unallocated: 805.29, scenarios: [], yields: [], gates: [],
      uncertain: [{ id: 't_step', basis: 'GUESS', value: 0.8, differs_in: [], measured_by: 'B', cum_spend_through_measured_by: 39.9, k_budget: 5.1, k_box: null, dir: 'higher' }],
      full_scale: [], flags: [], log: [] },
    given: { budget_usd: 1000, budget_covers_storage: true, budget_covers_tax: false,
      price_sheet: { read_at: '2026-10-16', instances: [{ gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99, page_text: '8x H100 SXM $3.99/GPU/hr' }], filesystem: { usd_gib_month: 0.2, page_text: '$0.20/GiB/month', example: true } } },
    findings: [{ items: [{ ref: 'card:closest_prior', status: 'CONTRADICTED', page_quote: 'Taylor Reynolds number 1,300', note: 'Largest run is 8,192 points per side.' },
      { ref: 'card:anchor', status: 'SUPPORTED', page_quote: 'Taylor Reynolds number 418', note: '' }] }, null],
    decision: { result: 'REJECT', blocking: [{ ref: 'card:closest_prior', status: 'CONTRADICTED' }], listed: [] },
    decision2: null,
    critique: { scores: [{ criterion: 'stakes', value: 2, ref: 'card:if_not', reason: 'No outcome would change a choice.' },
      { criterion: 'lever', value: 4, ref: 'plan:compute_axis', reason: 'Spans 16x in grid points.' },
      { criterion: 'verifiable', value: 4, ref: 'card:anchor', reason: 'Reproduces a published run.' },
      { criterion: 'open', value: 1, ref: 'card:closest_prior', reason: 'Published runs go far beyond.' }],
      decides_by: 'M', decides_by_reason: 'The ladder gives both outcomes.' },
    beyond_prior: false, annotations: [], halted: null, producer_path: 'run/R5/physical/8ff84fa5/producer.md',
  }
  const has = (card, labels) => labels.map(l => card.indexOf(l)).every((i, k, a) => i >= 0 && (k === 0 || i > a[k - 1]))
  const SECTIONS = ['**Question.**', '**What is known.**', '**Hypothesis.**', '**If compute is the lever.**', '**If not.**', '**Test.**',
    '*Compute axis.*', '**Check first.**', '**Would not show.**', '*Cost.*', '**Judges.**', '**Cost block.**', '**Derivations.**',
    '**Dramaturg, not SUPPORTED.**', '**Critic.**', '**Option critic.**', '**Producer says (not judged).**', '**Producer file.**']
  try {
    const card = render_card(W1)
    check(card.startsWith(`<a id="card-R5-physical-W1"></a>**W1 · `) && has(card, SECTIONS), 'card: sections out of contract order')
    check(card.includes('plan expects: the lever'), 'card: header lacks predictions.expected')
    check(has(card, ['*Compute axis.*', '*Restructuring.* none.', '**Check first.**']) && !card.includes('**Restructuring.**'), 'card: no restructuring, but no "none" script line')
    const rs = render_card({ ...W1, plan: { ...W1.plan, restructuring: { sequential_part: 'Each solver step waits on the last.', method: 'Steps are combined in rounds.' } } })
    check(has(rs, ['**Hypothesis.**', '**Restructuring.** Each solver step waits on the last. Steps are combined in rounds.', '**If compute is the lever.**'])
      && !rs.includes('*Restructuring.* none.'), 'card: Restructuring section missing or misplaced on a restructured plan')
    const no = render_card({ ...W1, plan: { ...W1.plan, compute_tested: 'no' } })
    check(no.includes('**If the hypothesis holds.**') && !no.includes('**If compute is the lever.**'), 'card: labels do not switch on compute_tested no')
    const rsno = render_card({ ...W1, plan: { ...W1.plan, compute_tested: 'no', restructuring: { sequential_part: 'Each solver step waits on the last.', method: 'Steps are combined in rounds.' } } })
    check(rsno.includes('**If compute is the lever.**') && rsno.includes('plan expects: the lever'), 'card: restructured plan with compute_tested no lost the lever labels')
    const body = card.split('\n\n**Judges.**')[0].replace(/<[^>]*>|·/g, ' ')
    check(txt_words(body) <= 320, `card: body ${txt_words(body)} words > 320`)
    const halt = render_card({ ...W1, decision: null, critique: null, findings: [null, null], halted: { gate: 'compute_tested', reasons: ['compute_tested is no'] } })
    check(halt.includes('**Halted at compute_tested.** compute_tested is no') && !halt.includes('**Judges.**') && !halt.includes('**Critic.**'), 'card: halt does not replace the judged part')
    // Table sort: root, then PASS / REJECT / halted, then lever, open, stakes (higher first), then key.
    const row = (key, result, lever, open) => ({ ...W1, pick: { ...W1.pick, key, root: key.split(':')[0], branch: key.split(':')[1] },
      decision: result === 'PASS' || result === 'REJECT' ? { result, blocking: [], listed: [] } : null,
      halted: result === 'halt' ? { gate: 'compute_tested', reasons: [] } : null,
      critique: result === 'halt' ? null : { ...W1.critique, scores: [{ criterion: 'lever', value: lever }, { criterion: 'open', value: open }, { criterion: 'stakes', value: 3 }] } })
    const rows = [row('R2:physical:F', 'REJECT', 5, 5), row('R1:physical:E', 'halt'), row('R1:physical:A', 'PASS', 4, 5), row('R1:physical:D', 'REJECT', 5, 5),
      row('R2:physical:G', 'PASS', 1, 1), row('R1:interp:B', 'PASS', 5, 3), row('R1:interp:A', 'PASS', 4, 5), row('R1:physical:C', 'PASS', 5, 4)]
    const got = render_table(rows).split('\n').filter(l => l.startsWith('| [')).map(l => l.slice(3, l.indexOf(']')))
    const want = ['R1·phys·C', 'R1·interp·B', 'R1·interp·A', 'R1·phys·A', 'R1·phys·D', 'R1·phys·E', 'R2·phys·G', 'R2·phys·F']
    check(got.join() === want.join(), `table: order ${got.join()} != ${want.join()}`)
  } catch (e) {
    failures.push(`render_selftest threw: ${e && e.message}`)
  }
  return { ok: failures.length === 0, failures }
}


// ---- src/prompts.js ----
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


// ---------- args (CONTRACT §3 replay.js): the script cannot read files, so every stored input comes in args ----------
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { return { error: `args is not JSON: ${e.message}` } } }
const NEED = { A: ['seed', 'given', 'picks', 'options_by_branch', 'roots', 'old_scores'], B: ['seed', 'given', 'picks', 'options_by_branch', 'roots', 'old_scores', 'price_sheet', 'records', 'planted_cards'] }
if (!NEED[A.phase]) return { error: 'args.phase must be "A" or "B"' }
const missing = NEED[A.phase].filter(k => A[k] === undefined || A[k] === null)
if (missing.length) return { error: `phase ${A.phase} needs args: ${missing.join(', ')}` }
const SEED = Number(A.seed)
// the run's own args as main builds them (gate_plan reads require_compute_lever and the budget)
const ARGS = {
  require_compute_lever: { physical: true, interp: true }, deepen_on_signal: false, pool_k: 3, picks_per_branch: 2,
  budget_usd: A.given.budget_usd, budget_covers_storage: A.given.budget_covers_storage, budget_covers_tax: A.given.budget_covers_tax,
}
const LOG = []
// role names: the five qt-* agent files; overridable by args.agent_types, because a session that started
// before the files existed cannot resolve them (registry is read at session start)
const ROLE = Object.assign({ 'qt-bare': 'qt-bare', 'qt-research': 'qt-research', 'qt-producer': 'qt-producer', 'qt-web': 'qt-web', 'qt-extract': 'qt-extract' }, A.agent_types || {})
const note = m => { LOG.push(m); log(m) }

// ---------- S0: model-free self-tests, before any agent ----------
const failures = Object.entries({ cost: cost_selftest(), pick: pick_selftest(), gates: gate_selftest(), render: render_selftest() })
  .flatMap(([m, r]) => (r.ok ? [] : (r.failures.length ? r.failures : ['not ok']).map(f => `${m}: ${f}`)))
if (failures.length) return { error: `S0 self-test failed (${failures.length})`, failures }

// ---------- vocabularies and helpers, as in main.js ----------
const OC_CRIT = { physical: ['stakes', 'open', 'reshape'], interp: ['stakes', 'open', 'internals', 'reshape'] }
const CARD_CRIT = { physical: ['stakes', 'lever', 'verifiable', 'open', 'reshape', 'baseline'], interp: ['stakes', 'lever', 'verifiable', 'open', 'internals', 'reshape', 'baseline'] }
const CARD = [
  ['question', 'question', 25], ['hypothesis', 'hypothesis', 22],
  ['sequential_part', 'restructuring.sequential_part', 18], ['method', 'restructuring.method', 22],
  ['if_lever', 'predictions.if_lever', 22], ['if_not', 'predictions.if_not', 25],
  ['test_summary', 'test_summary', 45], ['closest_prior', 'novelty.closest_prior', 30],
  ['left_open', 'novelty.left_open', 30], ['anchor', 'anchor.what', 24], ['limits', 'limits', 30],
]
const CAPS = Object.fromEntries(CARD.map(f => [f[1], f[2]]))
const str = v => (typeof v === 'string' ? v : JSON.stringify(v))
const getPath = (o, p) => p.split('.').reduce((x, k) => (x == null ? x : x[k]), o)
const fieldText = (plan, p) => { const v = getPath(plan, p); return Array.isArray(v) ? v.join(' ') : v == null ? '' : String(v) }
function setField(plan, p, text) {
  const ks = p.split('.'), last = ks.pop(), obj = ks.reduce((x, k) => x[k], plan)
  obj[last] = Array.isArray(obj[last]) ? [text] : text
}
const optionRecord = o => ({ id: o.id, title: o.title, summary: o.summary, root_link: o.root_link, compute_open: o.compute_open, sequential: o.sequential, source_urls: o.source_urls })
// as main.js: "none: ..." is none, any other text names a chain
const seqStatus = s => (String(s ?? '').trim().toLowerCase().startsWith('none') ? 'none' : 'named')
const GIVEN = { ...A.given, price_sheet: A.price_sheet || null }
const ROOTQ = Object.fromEntries(A.roots.map(r => [r.id, r.question]))
// stored options predate root_link, compute_open, sequential and source_urls; the judges are told so. "not given" names
// no "none", so no reshape floor applies and the option critic reads the summary.
const OPTS = Object.entries(A.options_by_branch).flatMap(([bk, items]) => {
  const [root, branch] = bk.split(':')
  return items.map(o => ({ ...o, root_link: 'not recorded', compute_open: 'not recorded', sequential: 'not given (stored run)', source_urls: [], key: `${bk}:${o.id}`, root, branch }))
})
const OPT = Object.fromEntries(OPTS.map(o => [o.key, o]))
const keyOf = p => `${p.root}:${p.branch}:${p.id}`
// parallel() turns a throw into null; log it so a script error is never silent (as in main.js)
const guard = (what, f) => async () => { try { return await f() } catch (e) { note(`${what}: script error: ${(e && e.message) || e}`); return null } }
const tagOf = p => `${p.root}:${p.branch}:${p.kind}`

async function twice(what, ask, check) {
  let rec = null
  for (const s of ['', '-resample']) {
    const r = await ask(s)
    if (r) rec = r
    const c = r ? check(r) : { ok: false, errors: ['agent returned null'] }
    if (c.ok) return { rec: r, ok: true }
    note(`${what}${s ? ' (resample)' : ''}: ${c.errors.join('; ')}`)
  }
  return { rec, ok: false }
}

// ================= phase A =================
async function priceSheet() {
  const r = await twice('price sheet',
    s => agent(P_PRICE_SHEET(), { label: `run:price-sheet${s}`, phase: 'Price', schema: SCHEMA_PRICE_SHEET, agentType: ROLE['qt-web'], model: 'sonnet', effort: 'low' }),
    gate_price_sheet)
  return r.ok ? r.rec : null
}

// REPAIR_EXPR applied to a copy of the plan, as main.js does
function repairedPlan(plan, fix, annotations) {
  const p = JSON.parse(JSON.stringify(plan)), missed = []
  for (const n of fix.numbers || []) { const t = (p.numbers || []).find(x => x.id === n.id); if (t) t.expr = n.expr; else missed.push(n.id) }
  for (const l of fix.lines || []) {
    const t = ((p.cost && p.cost.lines) || []).find(x => x.id === l.id)
    if (!t) { missed.push(l.id); continue }
    for (const k of ['hours', 'usd', 'need']) if (l[k] !== undefined) t[k] = l[k]
  }
  annotations.push(`cost record repaired: ${(fix.numbers || []).length + (fix.lines || []).length} expression(s) rewritten${missed.length ? `; unknown ids ignored: ${missed.join(', ')}` : ''}`)
  return p
}

// {menu_id} -> the computed value; an unknown id stays as written (C9 counts it)
const fillMenu = (text, menu) => text.replace(/\{([a-z][a-z0-9_]*)\}/g, (m, id) => {
  const e = menu.find(x => x.id === id)
  return e ? String(e.value) : m
})

// The writer side cell (P2'): 10 picks, the lowest in a seeded order of their own keys.
const WRITER_KEYS = new Set(A.picks.map(keyOf).sort((a, b) => pick_u(SEED, `replaywriter:${a}`) - pick_u(SEED, `replaywriter:${b}`)).slice(0, 10))

async function replayPick(p) {
  const key = keyOf(p), tag = tagOf(p), o = OPT[key]
  const rec = { pick: { key, root: p.root, branch: p.branch, kind: p.kind, id: p.id, title: p.title }, plan: null, eval: null, gate: null, card: null,
    writer_text: null, writer_raw: null, menu: null, block: null, repairs: [], cardfields: null, np_failures: [], beyond_prior: null, annotations: [], halted: null }
  let plan = await agent(P_EXTRACT(p.producer_path, p.dir), { label: `${tag}:extract`, phase: 'Extract', schema: SCHEMA_PLAN, agentType: ROLE['qt-extract'], model: 'sonnet', effort: 'low' })
  if (!plan) { rec.halted = { gate: 'schema', reasons: ['no valid PLAN from the extract'] }; note(`${tag}: extract returned no valid PLAN`); return rec }
  try {
    let ev = cost_eval_plan(plan, GIVEN), g = gate_plan(plan, ev, rec.pick, ARGS)
    if (g.action === 'repair') {
      note(`${tag}: G-plan repair: ${g.reasons.join('; ')}`)
      const errs = ev.errors.length ? ev.errors.map(e => `${e.kind} at ${e.where}: ${e.msg}`) : g.reasons
      const fix = await agent(P_REPAIR_EXPR(errs, plan), { label: `${tag}:repair-expr`, phase: 'Extract', schema: SCHEMA_REPAIR_EXPR, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
      rec.repairs.push({ kind: 'expr', reasons: g.reasons, fix })
      if (fix) { plan = repairedPlan(plan, fix, rec.annotations); ev = cost_eval_plan(plan, GIVEN); g = gate_plan(plan, ev, rec.pick, ARGS) }
      else note(`${tag}: cost repair returned null`)
    }
    rec.plan = plan
    rec.eval = ev
    rec.gate = g
    rec.annotations.push(...g.annotations)
    // A halt is recorded and the chain continues: the replay judges every card ("PASS before the compute halt", substrate P1).
    if (g.action !== 'ok') { rec.halted = { gate: g.action === 'repair' ? 'cost record broken' : 'G-plan', reasons: g.reasons }; note(`${tag}: ${rec.halted.gate}: ${g.reasons.join('; ')}`) }

    // S7 as in main: failing card fields get one repair, kept only if every number survives
    const cf = gate_cardfields(plan, CAPS)
    rec.cardfields = cf
    rec.annotations.push(...cf.annotations)
    if (!cf.ok) {
      const orig = Object.fromEntries(cf.failing.map(f => [f.field, fieldText(plan, f.field)]))
      const caps = Object.fromEntries(cf.failing.map(f => [f.field, CAPS[f.field]]))
      const fix = await agent(P_REPAIR_FIELDS(orig, caps, plan), { label: `${tag}:repair-fields`, phase: 'Card', schema: SCHEMA_REPAIR_FIELDS, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
      rec.repairs.push({ kind: 'fields', fields: Object.keys(orig), fix })
      for (const f of Object.keys(orig)) {
        const t = fix && fix.fields && fix.fields[f]
        if (typeof t !== 'string') continue
        if (gate_number_preservation(orig[f], t)) { setField(plan, f, t); rec.annotations.push(`${f}: rewritten by the field repair`) }
        else { rec.np_failures.push(f); rec.annotations.push(`${f}: the field repair dropped a number; original kept`) }
      }
      gate_cardfields(plan, CAPS).failing.forEach(f => rec.annotations.push(`card field ${f.field} still fails: ${f.reasons.join(', ')}`))
    }
    const lv = (plan.compute_axis && plan.compute_axis.levels) || [], pm = plan.novelty && plan.novelty.prior_max_level
    rec.beyond_prior = typeof pm === 'number' && lv.length ? Math.max(...lv) > pm : null
    rec.block = cost_render_block(ev, plan, GIVEN)
    rec.menu = cost_menu(ev, plan)
    rec.card = render_card({ pick: rec.pick, option: o, root_question: ROOTQ[p.root], plan, eval: ev, given: GIVEN, findings: [null, null],
      decision: null, decision2: null, critique: null, beyond_prior: rec.beyond_prior, annotations: rec.annotations, halted: rec.halted, producer_path: p.producer_path })

    if (WRITER_KEYS.has(key)) {
      const { cost, ...planNoCost } = plan
      const w = await agent(P_WRITER(ROOTQ[p.root], optionRecord(o), planNoCost, rec.menu), { label: `${tag}:writer`, phase: 'Card', agentType: ROLE['qt-bare'], model: 'sonnet' })
      if (typeof w === 'string') { rec.writer_raw = w; rec.writer_text = fillMenu(w, rec.menu) }
      else note(`${tag}: writer returned no text`)
    }
  } catch (e) { rec.error = String((e && e.message) || e); note(`${tag}: script error: ${rec.error}`) }
  return rec
}

// ================= phase B =================
function criticView(plan) {
  const { cost, full_scale, compute_tested, compute_tested_why, files_read, ...rest } = plan
  const { expected, expected_why, ...predictions } = plan.predictions || {}
  const { decides, searched, ...novelty } = plan.novelty || {}
  return { ...rest, predictions, novelty }
}
const criticCard = plan => CARD.map(([name, p]) => `card:${name}: ${fieldText(plan, p)}`).join('\n')

// one dramaturg sample with one resample on a degenerate return, decided by the script's rule
async function dramaturg(label, items, decide) {
  const refs = items.map(i => i.ref)
  const r = await twice(`${label}: dramaturg`,
    s => agent(P_DRAMATURG(items), { label: `${label}:dramaturg${s}`, phase: 'Check', schema: SCHEMA_FINDINGS, agentType: ROLE['qt-web'] }),
    f => { const g = gate_findings(f.items, refs); return { ok: g.ok && !g.degenerate.length, errors: [...g.errors, ...g.degenerate.map(d => `degenerate: ${str(d)}`)] } })
  return { items, findings: r.rec, findings_ok: r.ok, decision: r.rec ? decide(r.rec.items) : null }
}

async function judgeRecord(r) {
  // the same items main builds (gate_dramaturg_items); the replay always has a price sheet, so rates are never items
  const d = await dramaturg(tagOf(r.pick), gate_dramaturg_items(r.plan, CARD), f => gate_decision(f, gate_core_refs(r.plan), r.plan, r.eval, GIVEN))
  return { key: r.pick.key, ...d }
}

// a planted card is one card item plus its sources, every item core
async function judgePlanted(c) {
  const items = [{ ref: 'card:text', text: c.card_text, sources: c.sources.map(s => ({ id: s.id, url: s.url, quote: s.quote })) },
    ...c.sources.map(s => ({ ref: `src:${s.id}`, url: s.url, quote: s.quote, supports: s.supports }))]
  const d = await dramaturg(`planted:${c.id}`, items, f => gate_decision(f, items.map(i => i.ref), null, null, GIVEN))
  return { id: c.id, expected: c.expected, ...d }
}

async function critic(r) {
  const tag = tagOf(r.pick), cb = r.pick.branch, plan = r.plan
  const cr = await twice(`${tag}: critic`,
    s => agent(P_CRITIC(ROOTQ[r.pick.root], optionRecord(OPT[r.pick.key]), criticCard(plan), criticView(plan), CRIT_CARD(cb)), { label: `${tag}:critic${s}`, phase: 'Check', schema: SCHEMA_CRITIQUE, agentType: ROLE['qt-bare'], model: 'sonnet' }),
    x => gate_critique(x, CARD.map(f => f[0]), plan, CARD_CRIT[cb]))
  return { key: r.pick.key, critique: cr.rec, critique_ok: cr.ok }
}

// three independent option-critic samples per stored branch; no resample, so the samples stay independent draws (K3)
const BRANCH_KEYS = Object.keys(A.options_by_branch)
const branchOpts = bk => OPTS.filter(o => `${o.root}:${o.branch}` === bk)
const optionCritic = (bk, i) => agent(P_OPTION_CRITIC(ROOTQ[bk.split(':')[0]], CRIT_OPTION(bk.split(':')[1]), branchOpts(bk).map(optionRecord)),
  { label: `${bk}:option-critic:${i + 1}`, phase: 'Options', schema: SCHEMA_OPTION_SCORES, agentType: ROLE['qt-bare'] })

// pick_run input from a set of samples: each criterion is the mean over the samples that returned the branch,
// rounded (a missing or invalid score counts 1, as in main); distance is the median label (main's fallback ADJACENT)
const DIST = ['SAME', 'ADJACENT', 'ELSEWHERE']
function scoreBranch(bk, samples) {
  const [root, branch] = bk.split(':'), crit = OC_CRIT[branch], got = samples.filter(Boolean)
  const scored = branchOpts(bk).map(o => {
    const its = got.map(s => (s.items || []).find(it => it.id === o.id) || {})
    const scores = crit.map(c => {
      const vs = its.map(it => { const s = (it.scores || []).find(x => x.criterion === c); return s && Number.isInteger(s.value) && s.value >= 1 && s.value <= 5 ? s.value : 1 })
      return { criterion: c, value: vs.length ? Math.round(vs.reduce((a, b) => a + b, 0) / vs.length) : 1 }
    })
    const ds = its.map(it => DIST.indexOf(it.distance)).filter(d => d >= 0).sort((x, y) => x - y)
    return { id: o.id, distance: ds.length ? DIST[ds[Math.floor((ds.length - 1) / 2)]] : 'ADJACENT', scores }
  })
  // "not recorded" is neither settled nor none, so every stored option is open (CONTRACT §2.2)
  const status = Object.fromEntries(scored.map(s => [s.id, 'open']))
  const totals = gate_totals(scored, crit, status)
  return { root, branch, options: scored.map(s => ({ key: `${bk}:${s.id}`, id: s.id, title: OPT[`${bk}:${s.id}`].title, total: totals[s.id],
    scores: Object.fromEntries(s.scores.map(x => [x.criterion, x.value])), distance: s.distance, compute_open_status: 'open',
    sequential_status: seqStatus(OPT[`${bk}:${s.id}`].sequential), compute_open: 'not recorded' })) }
}
const runPicks = (branches, clusters) => pick_run({ seed: SEED, args: { pool_k: ARGS.pool_k, picks_per_branch: ARGS.picks_per_branch, require_compute_lever: ARGS.require_compute_lever }, branches, clusters, seed_ideas: [] })

async function dedupJudge() {
  const keys = OPTS.map(o => o.key), samples = [], H = dedup_handles(OPTS)
  const dd = await twice('dedup judge',
    async s => {
      const r = await agent(P_DEDUP(H.lines.map(({ handle, option: o }) => `${handle}: ${o.title}. ${o.summary}`)), { label: `run:dedup${s}`, phase: 'Options', schema: SCHEMA_DEDUP, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
      const t = r && { ...r, clusters: dedup_unhandle(r.clusters, H.toKey) }
      samples.push(t)
      return t
    },
    r => {
      const g = gate_dedup(r.clusters, keys), j = gate_dedup_jaccard(OPTS, r.clusters, 0.4)
      return { ok: g.ok && !g.soft.length && j.ok, errors: [...g.errors, ...g.soft, ...j.violations.map(v => `title Jaccard >= 0.4 not merged: ${str(v)}`)] }
    })
  const single = OPTS.map(o => ({ topic: o.title, members: [o.key] }))
  const best = dd.ok ? null : dedup_best(samples, OPTS, keys, 0.4)
  if (!dd.ok) note(best ? `dedup judge failed twice: kept the valid sample with ${best.faults} soft fault(s)` : 'dedup judge failed twice: one cluster per option')
  const clusters = dd.ok ? dd.rec.clusters : best ? best.clusters : single
  // P9'(b): the cross-root pairs at title Jaccard >= 0.4 are the violations of the all-singleton clustering
  return { samples, ok: dd.ok, clusters, jaccard_pairs_n: gate_dedup_jaccard(OPTS, single, 0.4).violations.length,
    jaccard_violations_n: gate_dedup_jaccard(OPTS, clusters, 0.4).violations.length }
}

async function overlapJudge() {
  const raw = await agent(P_OVERLAP(A.roots.map(r => ({ id: r.id, question: r.question }))), { label: 'roots:overlap', phase: 'Options', schema: SCHEMA_OVERLAP, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
  return { raw, gate: raw ? gate_overlap(raw.pairs, A.roots.map(r => r.id)) : null }
}

// ================= run =================
if (A.phase === 'A') {
  const sheet = A.price_sheet || await priceSheet()
  if (!sheet) return { error: 'price sheet failed twice; pass args.price_sheet to replay', log: LOG }
  GIVEN.price_sheet = sheet
  const records = await parallel(A.picks.map(p => () => replayPick(p)))
  return { phase: 'A', price_sheet: sheet, records: records.map((r, i) => r || { pick: { key: keyOf(A.picks[i]) }, error: 'pick chain threw' }), log: LOG }
}

// phase-A records written before PLAN.restructuring existed have none: read as {sequential_part: '', method: 'none'},
// so gates, core refs, the critic's view and its baseline NA rule see a plan that is not restructured
const withRestructuring = plan => (plan.restructuring ? plan : { ...plan, restructuring: { sequential_part: '', method: 'none' } })
// phase B can be split so each launch carries small args: record slices (skip_branch_jobs) and one branch-level run (skip_records)
const judged = A.skip_records ? [] : A.records.filter(r => r.plan).map(r => ({ ...r, plan: withRestructuring(r.plan) }))
A.records.filter(r => !r.plan).forEach(r => note(`${r.pick.key}: no plan; not judged`))
const skipB = !!A.skip_branch_jobs
const [dram, planted, crit, oc, dd, overlap] = await parallel([
  () => parallel(judged.map(r => guard(`${r.pick.key}: dramaturg`, () => judgeRecord(r)))),
  () => parallel(A.planted_cards.map(c => guard(`planted:${c.id}`, () => judgePlanted(c)))),
  () => parallel(judged.map(r => guard(`${r.pick.key}: critic`, () => critic(r)))),
  () => parallel(skipB ? [] : BRANCH_KEYS.flatMap(bk => [0, 1, 2].map(i => () => optionCritic(bk, i)))),
  skipB ? () => Promise.resolve(null) : guard('dedup judge', dedupJudge),
  skipB ? () => Promise.resolve(null) : guard('overlap judge', overlapJudge),
])
if (skipB) return { phase: 'B', slice: A.slice ?? null, dramaturg: dram, planted, critic: crit, log: LOG }
const dedup = dd || { samples: [], ok: false, clusters: OPTS.map(o => ({ topic: o.title, members: [o.key] })), jaccard_pairs_n: null, jaccard_violations_n: null }
const option_critic = Object.fromEntries(BRANCH_KEYS.map((bk, b) => [bk, oc.slice(3 * b, 3 * b + 3)]))
// branches scored from all samples (i undefined) or from sample i alone; a branch with no sample back is left out, and logged
function scoredBranches(i) {
  const use = bk => (i === undefined ? option_critic[bk] : [option_critic[bk][i]])
  return BRANCH_KEYS.filter(bk => {
    const got = use(bk).some(Boolean)
    if (!got) note(`${bk}: no option-critic sample${i === undefined ? 's' : ` ${i + 1}`}; branch left out`)
    return got
  }).map(bk => scoreBranch(bk, use(bk)))
}
const branches = scoredBranches()
const legacy = BRANCH_KEYS.map(bk => {
  const [root, branch] = bk.split(':')
  return { root, branch, options: A.old_scores[bk].map(s => ({ key: `${bk}:${s.id}`, id: s.id, title: OPT[`${bk}:${s.id}`].title, total: s.total })) }
})
return {
  phase: 'B', dramaturg: dram, planted, critic: crit, option_critic,
  new_scores: Object.fromEntries(branches.map(b => [`${b.root}:${b.branch}`, b.options])),
  dedup, overlap,
  pick_run: runPicks(branches, dedup.clusters),
  pick_run_by_sample: [0, 1, 2].map(i => runPicks(scoredBranches(i), dedup.clusters)),
  pick_run_legacy: pick_run_legacy({ seed: SEED, branches: legacy }),
  log: LOG,
}
