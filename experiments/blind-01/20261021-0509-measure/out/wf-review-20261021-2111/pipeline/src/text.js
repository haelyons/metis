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
