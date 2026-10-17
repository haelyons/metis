'use strict'
// JSON Schema subset used by src/schemas.js: type, properties, required, items, enum, anyOf, minimum, maximum,
// additionalProperties. OpenCode models get the schema in the prompt; this checks what comes back.
const TYPES = {
  object: x => x !== null && typeof x === 'object' && !Array.isArray(x), array: Array.isArray, string: x => typeof x === 'string',
  number: x => typeof x === 'number' && Number.isFinite(x), integer: Number.isInteger, boolean: x => typeof x === 'boolean', null: x => x === null,
}
const kind = v => (v === null ? 'null' : Array.isArray(v) ? 'array' : typeof v)

function validate(schema, v, at = '$', errs = []) {
  if (errs.length >= 40 || !schema) return errs
  if (schema.anyOf) {
    if (!schema.anyOf.some(s => !validate(s, v, at, []).length)) errs.push(`${at}: matches none of the allowed forms`)
    return errs
  }
  if (schema.type) {
    const ts = [].concat(schema.type)
    if (!ts.some(t => TYPES[t] && TYPES[t](v))) { errs.push(`${at}: expected ${ts.join(' or ')}, got ${kind(v)}`); return errs }
  }
  if (schema.enum && !schema.enum.includes(v)) errs.push(`${at}: ${JSON.stringify(v)} is not one of ${JSON.stringify(schema.enum)}`)
  if (typeof v === 'number') {
    if (schema.minimum != null && v < schema.minimum) errs.push(`${at}: ${v} is below ${schema.minimum}`)
    if (schema.maximum != null && v > schema.maximum) errs.push(`${at}: ${v} is above ${schema.maximum}`)
  }
  if (Array.isArray(v) && schema.items) v.forEach((x, i) => validate(schema.items, x, `${at}[${i}]`, errs))
  if (TYPES.object(v)) {
    const props = schema.properties || {}
    for (const k of schema.required || []) if (!(k in v)) errs.push(`${at}: missing "${k}"`)
    for (const [k, s] of Object.entries(props)) if (k in v) validate(s, v[k], `${at}.${k}`, errs)
    if (schema.additionalProperties === false) { for (const k of Object.keys(v)) if (!(k in props)) errs.push(`${at}: unexpected "${k}"`) }
    else if (TYPES.object(schema.additionalProperties)) { for (const k of Object.keys(v)) if (!(k in props)) validate(schema.additionalProperties, v[k], `${at}.${k}`, errs) }
  }
  return errs
}

const promptSuffix = schema => `\n\nReturn only one JSON value, with no other text, that matches this JSON Schema:\n${JSON.stringify(schema)}`

module.exports = { validate, promptSuffix }
