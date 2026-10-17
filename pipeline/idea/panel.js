'use strict'
// Merge a panel of critic replies (SCHEMA_CRITIQUE) into one: per criterion the median value, with the ref and reason
// of the first member who gave that value; NA only when most members gave NA; decides_by by majority (ties: first member).
function mergeCritique(replies) {
  const rs = replies.filter(r => r && Array.isArray(r.scores))
  if (!rs.length) return null
  const criteria = [...new Set(rs.flatMap(r => r.scores.map(s => s.criterion)))]
  const scores = criteria.map(c => {
    const given = rs.map(r => r.scores.find(s => s.criterion === c)).filter(Boolean)
    const nums = given.filter(s => Number.isInteger(s.value)).map(s => s.value).sort((a, b) => a - b)
    if (nums.length * 2 <= given.length) return given.find(s => s.value === 'NA')
    const med = nums[Math.floor((nums.length - 1) / 2)]   // lower median: an even split never rounds up
    return given.find(s => s.value === med)
  })
  const votes = rs.map(r => r.decides_by)
  const decides_by = votes.slice().sort((a, b) => votes.filter(v => v === b).length - votes.filter(v => v === a).length)[0]
  const first = rs.find(r => r.decides_by === decides_by)
  return { scores, decides_by, decides_by_reason: first.decides_by_reason }
}
module.exports = { mergeCritique }
