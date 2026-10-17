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
