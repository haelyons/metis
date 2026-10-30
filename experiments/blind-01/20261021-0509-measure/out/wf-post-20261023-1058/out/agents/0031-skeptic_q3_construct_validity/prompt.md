You audit ONE measured claim through ONE assigned confound. Findings here are numbers measured from a model, not text a model wrote. Default stance: assume the claim is an ARTIFACT of your confound until a committed number rules it out.

Decide only from the evidence below; do not call tools or read files. If you cannot name the deciding number, it is NEEDS_RUN, not RULED_OUT. Do not invent a control.

CONFOUND: construct validity
CLAIM: The auxiliary time of 0.00949 h per pair is 35 times below the lower band edge of 0.3333 h. The three pairs took 32.6, 34.2 and 35.7 s. Does that measure the card's auxiliary work or only a toy search?
EVIDENCE (the only data you may treat as established): where: Endpoint C3 and rows_aux_tag-m4.jsonl. Docking used 2 swarms, 20 glowworms and 20 steps, 4 cores, no restraint to the published interface. It took 22 to 23 s of the total per pair.; if_true: If the search is far smaller than the card's, the FAIL says the toy is cheap, not that the card's 1 h guess is wrong. It is also the only decided input, and a FAIL it inherits from a failed anchor.; changes: The one decided result then says little about the card's cost. The design called this term undefined and read it by guess, so the FAIL may only reflect that guessed reading.

Reason in prose, then output the JSON tail:
- status RULED_OUT only if you can name the committed number / file:line that makes your confound unable to explain the claim; put that number in next.
- status EXPLAINS if the evidence is consistent with your confound producing the claim.
- status NEEDS_RUN if the committed data cannot decide it; then next is ONE line, tagged "RUN: <existing script + flags>" if an existing control settles it, else "AUTHOR: <the control to write>".
- crux: the one fact your verdict hinges on. If the claim is itself a null ("X is uninformative / diffuse / at the noise floor"), a confound that EXPLAINS the statistic may BE the claim holding, not refuting it -- say which in the crux.
Number-gates (H2) that apply whatever your confound: a cited number decides only if a refuting outcome was possible and named before the run (a claim every outcome supports is framing -- treat as EXPLAINS); only with margin (exact-threshold clearance, a threshold authored after seeing the data, or selection from unreported attempts does not decide); and only within tested scope (stated scope exceeding the tested population, scale, or design strength is EXPLAINS on that ground).
Examples of next -- RULED_OUT: "same effect on held-out set, foo.json:42, n=30". NEEDS_RUN: "AUTHOR: mean/resample-ablation variant; only zero-ablation on record".

Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","additionalProperties":false,"required":["confound","status","crux","next"],"properties":{"confound":{"type":"string"},"status":{"type":"string","enum":["RULED_OUT","EXPLAINS","NEEDS_RUN"]},"crux":{"type":"string"},"next":{"type":"string","description":"RULED_OUT: the committed number/file:line. NEEDS_RUN: one line tagged RUN: or AUTHOR:. EXPLAINS: brief why."}}}