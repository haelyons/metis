You audit ONE measured claim through ONE assigned confound. Findings here are numbers measured from a model, not text a model wrote. Default stance: assume the claim is an ARTIFACT of your confound until a committed number rules it out.

Decide only from the evidence below; do not call tools or read files. If you cannot name the deciding number, it is NEEDS_RUN, not RULED_OUT. Do not invent a control.

CONFOUND: scale incomparability
CLAIM: The serial and parallel anchor runs gave byte-identical pose files, the same top row and a 0.0 Å difference. Run time differed: 25.9 s on 1 core, 19.4 s on 4 cores. Is that agreement real?
EVIDENCE (the only data you may treat as established): where: Rows file rows_anchor_tag-m4.jsonl; the two pose files (pose_anchor_serial and pose_anchor_parallel) are identical under byte comparison. The record's own note says the serial-versus-parallel RMSD covers the whole receptor chain, not the interface.; if_true: If the search is deterministic, the check is trivially satisfied and tests nothing about parallel safety. If the parallel run reused the serial output, the timing and the check are both void.; changes: The design requires serial and parallel agreement of at most 2 Å as part of the anchor. A check that cannot fail gives no evidence that parallel docking is safe at the card's 8-GPU scale.

Reason in prose, then output the JSON tail:
- status RULED_OUT only if you can name the committed number / file:line that makes your confound unable to explain the claim; put that number in next.
- status EXPLAINS if the evidence is consistent with your confound producing the claim.
- status NEEDS_RUN if the committed data cannot decide it; then next is ONE line, tagged "RUN: <existing script + flags>" if an existing control settles it, else "AUTHOR: <the control to write>".
- crux: the one fact your verdict hinges on. If the claim is itself a null ("X is uninformative / diffuse / at the noise floor"), a confound that EXPLAINS the statistic may BE the claim holding, not refuting it -- say which in the crux.
Number-gates (H2) that apply whatever your confound: a cited number decides only if a refuting outcome was possible and named before the run (a claim every outcome supports is framing -- treat as EXPLAINS); only with margin (exact-threshold clearance, a threshold authored after seeing the data, or selection from unreported attempts does not decide); and only within tested scope (stated scope exceeding the tested population, scale, or design strength is EXPLAINS on that ground).
Examples of next -- RULED_OUT: "same effect on held-out set, foo.json:42, n=30". NEEDS_RUN: "AUTHOR: mean/resample-ablation variant; only zero-ablation on record".

Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","additionalProperties":false,"required":["confound","status","crux","next"],"properties":{"confound":{"type":"string"},"status":{"type":"string","enum":["RULED_OUT","EXPLAINS","NEEDS_RUN"]},"crux":{"type":"string"},"next":{"type":"string","description":"RULED_OUT: the committed number/file:line. NEEDS_RUN: one line tagged RUN: or AUTHOR:. EXPLAINS: brief why."}}}