// text.js tests. Wrapped so names cannot collide with other test files in the shared context.
;(() => {
  test('txt_words counts tokens holding a letter or digit', () => {
    assert.equal(txt_words('Skill rises by 5 points.'), 5)
    assert.equal(txt_words('a — b 3 —'), 3)
    assert.equal(txt_words('  '), 0)
    assert.equal(txt_words(null), 0)
  })

  test('txt_sentences: abbreviations and decimals do not split', () => {
    assert.deepEqual(
      txt_sentences('Use a probe, e.g. a linear one. It costs 3.5 hours. Then stop! van Dinther et al. 2019 showed it. Is it? Yes'),
      ['Use a probe, e.g. a linear one.', 'It costs 3.5 hours.', 'Then stop!', 'van Dinther et al. 2019 showed it.', 'Is it?', 'Yes'])
    assert.deepEqual(txt_sentences('One, i.e. Two. Three approx. ten. Four "quoted." Five'), ['One, i.e. Two.', 'Three approx. ten.', 'Four "quoted."', 'Five'])
    assert.deepEqual(txt_sentences(''), [])
  })

  test('txt_normalize_title: case, punctuation, quotes, spaces', () => {
    assert.equal(txt_normalize_title('  "High-fidelity"  Cloth: SIM. '), 'high fidelity cloth sim')
    assert.equal(txt_normalize_title('“Proof search” for formal maths'), txt_normalize_title('proof   search for FORMAL maths!'))
    assert.notEqual(txt_normalize_title('Proof search'), txt_normalize_title('Proof searches'))
  })

  test('txt_jaccard reproduces the calibration values (flow-work/strdedup.py)', () => {
    const titles = fixture('gates/titles.json')
    const t = prefix => titles.find(o => o.title.startsWith(prefix)).title
    const r2 = x => Math.round(x * 100) / 100
    assert.equal(r2(txt_jaccard(t('Turbulent flow by direct'), t('Turbulent fluid flow'))), 0.83)
    assert.equal(r2(txt_jaccard(t('High-fidelity contact and cloth'), t('High-fidelity cloth and deformable'))), 0.8)
    assert.equal(r2(txt_jaccard(t('Kilometre-scale weather and climate'), t('Kilometer-scale weather and climate simulation'))), 0.75)
    assert.equal(r2(txt_jaccard(t('Proof search for formal'), t('Proof search on fixed'))), 0.43)
    assert.equal(txt_jaccard('Training-data attribution and data valuation', 'Probe-based data attribution'), 0.4)
    assert.equal(txt_jaccard('The of and', 'a an the'), 0)
    assert.equal(txt_jaccard('Proof search', 'proof search'), 1)
  })

  test('txt_coined_codes: regex, hardware whitelist, URLs ignored', () => {
    assert.deepEqual(txt_coined_codes('W11 beats E2 on 8x H100, A100, A10, H200, B200, V100, L4 and L40'), ['W11', 'E2'])
    assert.deepEqual(txt_coined_codes('see https://example.org/E3/W12 and file:///tmp/C2.md, then (www.x.org/P1) Q1'), ['Q1'])
    assert.deepEqual(txt_coined_codes('H100s, GH200, E2x, ABC1, P100'), [])
  })

  test('txt_coined_codes on the W11 render card (options-and-card §5.1: 10 coined plus BP1)', () => {
    const fields = fixture('gates/card_w11_render.txt').split('\n').filter(l => /^##(?!HEADER|AXIS|COST)/.test(l))
    const codes = txt_coined_codes(fields.join('\n'))
    const count = c => codes.filter(x => x === c).length
    assert.equal(codes.length, 11)
    assert.equal(count('W11'), 2)
    assert.equal(codes.filter(x => /^E[1-4]$/.test(x)).length, 7)
    assert.equal(count('C2'), 1)
    assert.equal(count('BP1'), 1)
  })

  test('txt_numbers: normalised numeric tokens, not digits inside codes', () => {
    assert.deepEqual(
      txt_numbers('From 1,979 to 20k steps, 5.0 and −3 dB, 10-20 runs, H100 and E2, $1,000, 1e6, (1, 2, 3), 2.5M, 100MB, 8x'),
      ['1979', '20000', '5', '-3', '10', '20', '1000', '1000000', '1', '2', '3', '2500000', '100', '8'])
    assert.deepEqual(txt_numbers('no numbers, v1.2 aside'), [])
  })

  test('txt_has_digit', () => {
    assert.equal(txt_has_digit('above 5 points'), true)
    assert.equal(txt_has_digit('above five points'), false)
    assert.equal(txt_has_digit(undefined), false)
  })

  test('txt_contains_record_id: exact tokens only', () => {
    assert.deepEqual(txt_contains_record_id('Arm E2 beats n_seeds; E23, BE2, n_seeds_total', ['E2', 'n_seeds', 'E3', 'E2']), ['E2', 'n_seeds'])
    assert.deepEqual(txt_contains_record_id('E23 and BE2 and n_seeds_total', ['E2', 'n_seeds']), [])
    assert.deepEqual(txt_contains_record_id('phase P1-a then (P2).', ['P1-a', 'P2', 'P3']), ['P1-a', 'P2'])
  })

  test('txt_norm_number', () => {
    assert.equal(txt_norm_number('1,979'), '1979')
    assert.equal(txt_norm_number('20k'), '20000')
    assert.equal(txt_norm_number('5.0'), '5')
    assert.equal(txt_norm_number('1.1k'), '1100')
    assert.equal(txt_norm_number('2M'), '2000000')
    assert.equal(txt_norm_number('−3.50'), '-3.5')
    assert.equal(txt_norm_number(1979), '1979')
    assert.equal(txt_norm_number(' abc '), 'abc')
  })
})()
