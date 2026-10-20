// schemas.js tests: structure (root object, required within properties) and validation of hand-written instances
// with a small strict checker (no library). Wrapped to keep names local.
;(() => {
  const NAMES = ['QUESTIONS', 'OVERLAP', 'VERDICT', 'OPTIONS', 'OPTION_SCORES', 'DEDUP', 'PRICE_SHEET', 'PLAN', 'FINDINGS', 'CRITIQUE', 'REPAIR_FIELDS', 'REPAIR_EXPR']
  // top-level const bindings are not properties of the global object, so look them up by name
  const schemaOf = n => { try { return eval(`SCHEMA_${n}`) } catch (e) { return undefined } }

  // Every schema node, with its path.
  const nodes = (s, path = '$', out = []) => {
    out.push([path, s])
    for (const [k, v] of Object.entries(s.properties || {})) nodes(v, `${path}.${k}`, out)
    if (s.items) nodes(s.items, `${path}[]`, out)
    if (s.anyOf) s.anyOf.forEach((v, i) => nodes(v, `${path}|${i}`, out))
    if (s.additionalProperties && typeof s.additionalProperties === 'object') nodes(s.additionalProperties, `${path}{}`, out)
    return out
  }

  // Strict structural check: types, enums, bounds, required, and no properties the schema does not name.
  const validate = (s, v, path = '$') => {
    if (s.anyOf) return s.anyOf.some(b => !validate(b, v, path).length) ? [] : [`${path}: no anyOf branch matches`]
    const types = [].concat(s.type || [])
    const is = t => t === 'null' ? v === null : t === 'array' ? Array.isArray(v) : t === 'integer' ? Number.isInteger(v)
      : t === 'object' ? v !== null && typeof v === 'object' && !Array.isArray(v) : typeof v === t
    if (types.length && !types.some(is)) return [`${path}: expected ${types.join('|')}, got ${JSON.stringify(v)}`]
    const errs = []
    if (s.enum && !s.enum.includes(v)) errs.push(`${path}: ${JSON.stringify(v)} not in enum`)
    if (typeof v === 'number' && ((s.minimum !== undefined && v < s.minimum) || (s.maximum !== undefined && v > s.maximum))) errs.push(`${path}: ${v} out of bounds`)
    if (Array.isArray(v)) v.forEach((x, i) => errs.push(...validate(s.items, x, `${path}[${i}]`)))
    if (is('object') && types.includes('object')) {
      for (const k of s.required || []) if (!(k in v)) errs.push(`${path}.${k}: missing`)
      for (const [k, x] of Object.entries(v)) {
        const sub = (s.properties || {})[k] || (typeof s.additionalProperties === 'object' ? s.additionalProperties : null)
        if (sub) errs.push(...validate(sub, x, `${path}.${k}`))
        else errs.push(`${path}.${k}: not in schema`)
      }
    }
    return errs
  }

  const instances = () => ({ ...fixture('gates/records.json'), PLAN: fixture('gates/plan.json') })

  test('every contract schema exists with root type object', () => {
    for (const n of NAMES) {
      assert.equal(typeof schemaOf(n), 'object', `SCHEMA_${n} missing`)
      assert.equal(schemaOf(n).type, 'object', `SCHEMA_${n} root type`)
    }
  })

  test('required is within properties at every level; every object node has properties', () => {
    for (const n of NAMES) {
      for (const [path, s] of nodes(schemaOf(n))) {
        if (s.type !== 'object') continue
        const props = Object.keys(s.properties || {})
        assert.ok(props.length || s.additionalProperties, `SCHEMA_${n} ${path}: object with no properties`)
        for (const r of s.required || []) assert.ok(props.includes(r), `SCHEMA_${n} ${path}: required ${r} not in properties`)
        assert.ok(Array.isArray(s.required || []), `SCHEMA_${n} ${path}: required not an array`)
      }
    }
  })

  test('hand-written valid instances validate', () => {
    const inst = instances()
    for (const n of NAMES) assert.deepEqual(validate(schemaOf(n), inst[n]), [], `SCHEMA_${n}`)
  })

  test('the checker rejects broken instances (missing required, bad enum, NA in option scores, wrong anchor form)', () => {
    const inst = instances()
    const plan = inst.PLAN
    delete plan.predictions.noise_rule
    plan.compute_tested = 'maybe'
    plan.anchor = { what: 'a check with no tolerance' }
    const errs = validate(SCHEMA_PLAN, plan).join('\n')
    assert.match(errs, /predictions\.noise_rule: missing/)
    assert.match(errs, /compute_tested: "maybe" not in enum/)
    assert.match(errs, /anchor: no anyOf branch/)
    inst.OPTION_SCORES.items[0].scores[0].value = 'NA'
    assert.ok(validate(SCHEMA_OPTION_SCORES, inst.OPTION_SCORES).length)
    inst.CRITIQUE.scores[0].value = 6
    assert.ok(validate(SCHEMA_CRITIQUE, inst.CRITIQUE).length)
    assert.ok(validate(SCHEMA_PLAN, { ...fixture('gates/plan.json'), extra_field: 1 }).length)
  })

  test('PLAN accepts the absent-anchor form and leaves optional fields optional', () => {
    const plan = fixture('gates/plan.json')
    plan.anchor = { absent_reason: 'no published number for this setting' }
    delete plan.cost.scenarios
    delete plan.cost.yields
    delete plan.cost.spend_cap_usd
    delete plan.novelty.prior_max_level
    plan.numbers[0] = { id: 'g', name: 'guess', unit: 'x', basis: 'GUESS', value: 2, rests_on: 'a hunch from the pilot', measured_by: 'P1' }
    plan.restructuring = { sequential_part: 'Each step waits on the last.', method: 'Steps are combined in rounds.', condition: 'updates nearly commute; the pilot measures it',
      condition_phase: 'P1', baseline_sequential: 'the tuned reference trainer', baseline_copies: 'eight copies side by side' }
    assert.deepEqual(validate(SCHEMA_PLAN, plan), [])
  })

  // changed contract: PLAN.speedup is replaced by the required PLAN.restructuring; OPTIONS items require sequential
  test('PLAN requires restructuring (sequential_part, method; the rest optional) and has no speedup; OPTIONS items require sequential', () => {
    const plan = fixture('gates/plan.json')
    assert.equal(SCHEMA_PLAN.properties.speedup, undefined)
    assert.match(validate(SCHEMA_PLAN, { ...plan, speedup: {} }).join('\n'), /speedup: not in schema/)
    const { restructuring, ...without } = plan
    assert.match(validate(SCHEMA_PLAN, without).join('\n'), /\$\.restructuring: missing/)
    assert.match(validate(SCHEMA_PLAN, { ...plan, restructuring: { method: 'none' } }).join('\n'), /restructuring\.sequential_part: missing/)
    assert.deepEqual(SCHEMA_PLAN.properties.restructuring.required, ['sequential_part', 'method'])
    const opts = fixture('gates/records.json').OPTIONS
    delete opts.items[0].sequential
    assert.match(validate(SCHEMA_OPTIONS, opts).join('\n'), /items\[0\]\.sequential: missing/)
  })

  test('PLAN expression fields accept a string or a bare number, nothing else', () => {
    const plan = fixture('gates/plan.json')
    plan.numbers.push({ id: 'd', name: 'derived', unit: 'h', basis: 'DERIVED', expr: 12 })
    plan.cost.lines[0].hours = 20
    plan.cost.lines[0].need = '18'
    plan.full_scale = [{ id: 'all', what: 'every run', usd: 5000 }]
    assert.deepEqual(validate(SCHEMA_PLAN, plan), [])
    plan.cost.lines[0].usd = true
    assert.match(validate(SCHEMA_PLAN, plan).join('\n'), /lines\[0\]\.usd: no anyOf branch matches/)
  })

  test('descriptions on fields whose meaning is not obvious; no em-dashes in schema text', () => {
    const desc = (n, path) => nodes(schemaOf(n)).find(([p]) => p === path)[1].description
    for (const [n, path] of [
      ['OPTIONS', '$.items[].compute_open'], ['OPTIONS', '$.items[].sequential'], ['OPTIONS', '$.items[].root_link'], ['OVERLAP', '$.pairs[].shared_subject'],
      ['PLAN', '$.restructuring.sequential_part'], ['PLAN', '$.restructuring.method'], ['PLAN', '$.restructuring.condition'], ['PLAN', '$.restructuring.condition_phase'],
      ['PLAN', '$.restructuring.baseline_sequential'], ['PLAN', '$.restructuring.baseline_copies'],
      ['PRICE_SHEET', '$.instances[].page_text'], ['PLAN', '$.numbers[].basis'], ['PLAN', '$.predictions.noise_rule'],
      ['PLAN', '$.novelty.prior_max_level'], ['PLAN', '$.cost.lines[].need'], ['PLAN', '$.scored_against'],
      ['FINDINGS', '$.items[].ref'], ['CRITIQUE', '$.scores[].ref'], ['CRITIQUE', '$.decides_by'],
    ]) assert.ok(desc(n, path), `SCHEMA_${n} ${path} has no description`)
    for (const n of NAMES) assert.ok(!JSON.stringify(schemaOf(n)).includes('—'), `SCHEMA_${n} has an em-dash`)
  })
})()
