You audit ONE measured claim through ONE assigned confound. Findings here are numbers measured from a model, not text a model wrote. Default stance: assume the claim is an ARTIFACT of your confound until a committed number rules it out.

Decide only from the evidence below; do not call tools or read files. If you cannot name the deciding number, it is NEEDS_RUN, not RULED_OUT. Do not invent a control.

CONFOUND: single-case overfit
CLAIM: The placement test failed completely: 0 of 34 reference contacts were shared, and backbone RMSD was 38.6 Å against a 5 Å limit. Yet the call table says bind for all three pairs. The same program called the test pose no-bind. Does the bind call mean anything?
EVIDENCE (the only data you may treat as established): where: Redocking test file (endpoint-anchor): overlap 0.0, RMSD 38.6163, 114 pose contacts, 0 shared. Call table: three rows, all bind. The aux rows set 'contacts at 4.5 Å' true for all three.; if_true: The program's bind label is only physical contact somewhere on the surface, not binding at the published site. A bind call is then nearly guaranteed. The call table, scores and site classes would not separate binders from non-binders.; changes: The design assumes redocking can reproduce a known site, and that bind and no-bind calls are meaningful. If calls carry no information, the timing inputs measure the cost of producing labels that do not discriminate.

Reason in prose, then output the JSON tail:
- status RULED_OUT only if you can name the committed number / file:line that makes your confound unable to explain the claim; put that number in next.
- status EXPLAINS if the evidence is consistent with your confound producing the claim.
- status NEEDS_RUN if the committed data cannot decide it; then next is ONE line, tagged "RUN: <existing script + flags>" if an existing control settles it, else "AUTHOR: <the control to write>".
- crux: the one fact your verdict hinges on. If the claim is itself a null ("X is uninformative / diffuse / at the noise floor"), a confound that EXPLAINS the statistic may BE the claim holding, not refuting it -- say which in the crux.
Number-gates (H2) that apply whatever your confound: a cited number decides only if a refuting outcome was possible and named before the run (a claim every outcome supports is framing -- treat as EXPLAINS); only with margin (exact-threshold clearance, a threshold authored after seeing the data, or selection from unreported attempts does not decide); and only within tested scope (stated scope exceeding the tested population, scale, or design strength is EXPLAINS on that ground).
Examples of next -- RULED_OUT: "same effect on held-out set, foo.json:42, n=30". NEEDS_RUN: "AUTHOR: mean/resample-ablation variant; only zero-ablation on record".

Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","additionalProperties":false,"required":["confound","status","crux","next"],"properties":{"confound":{"type":"string"},"status":{"type":"string","enum":["RULED_OUT","EXPLAINS","NEEDS_RUN"]},"crux":{"type":"string"},"next":{"type":"string","description":"RULED_OUT: the committed number/file:line. NEEDS_RUN: one line tagged RUN: or AUTHOR:. EXPLAINS: brief why."}}}