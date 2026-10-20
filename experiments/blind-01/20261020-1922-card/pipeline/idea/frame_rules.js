'use strict'
// Rules the script applies to a frame check from the checked record, so a critic cannot score past the evidence.
const OKS = ['SUPPORTED', 'PARTIAL']

// p: the researcher's programme record; i: its 1-based number; marks: {ref: [finding or null, one per dramaturg]}
function programmeFlags(p, i, marks) {
  const found = ref => (marks[ref] || []).filter(Boolean)
  const passed = ref => found(ref).some(x => OKS.includes(x.status))
  const done = p.already_done || {}
  return {
    // archived or stopped, and a checker found the page that says so
    inactive: (p.activity || {}).state === 'inactive' && passed(`p${i}:activity`),
    // "not done" (or partly, or unknown) while a checker found the page contradicts that
    done_contradicted: ['no', 'partly', 'unknown'].includes(done.status) && found(`p${i}:done`).some(x => x.status === 'CONTRADICTED'),
    // the step is put in the card's terms, or no checker found it in the programme's own words
    step_restates_card: /\bthe card\b/i.test(p.step || '') || (found(`p${i}:step`).length > 0 && !passed(`p${i}:step`)),
  }
}

// scores: {fit, change, new}, each {median, ...}; caps the medians in place and returns a note per cap applied
function applyCaps(scores, flags) {
  const notes = []
  const cap = (c, max, why) => {
    if (scores[c] && scores[c].median != null && scores[c].median > max) { notes.push(`${c} ${scores[c].median} -> ${max}: ${why}`); scores[c].median = max }
  }
  if (flags.inactive) cap('change', 1, 'the programme is inactive or archived')
  if (flags.done_contradicted) cap('new', 3, 'a checker contradicted the claim that this has not been done')
  return notes
}

module.exports = { programmeFlags, applyCaps }
