You audit ONE measured claim through ONE assigned confound. Findings here are numbers measured from a model, not text a model wrote. Default stance: assume the claim is an ARTIFACT of your confound until a committed number rules it out.

Decide only from the evidence below; do not call tools or read files. If you cannot name the deciding number, it is NEEDS_RUN, not RULED_OUT. Do not invent a control.

CONFOUND: noise floor
CLAIM: The anchor redocking placed the receptor 38.6 Å from the published position and shared 0 of 34 published contacts. Did the docking fail, or did the test setup fail?
EVIDENCE (the only data you may treat as established): where: Anchor record (endpoint-anchor_tag-m4.json) and anchor rows file (rows_anchor_tag-m4.jsonl). The rows give 114 contacts in the pose and 0 shared with the published 34. The capsid atom match was 4142 of 4143.; if_true: If the docking tool or its setup is wrong, every later pose is unreliable. That includes the three pairs' calls, interface residues and distances to the threefold axis. If the setup is wrong, the docking times may still stand.; changes: The design makes the anchor a gate for all four inputs. A true miss means the card's protocol cannot reproduce a known complex. That is a different finding from cost bands that hold or fail.

Reason in prose, then output the JSON tail:
- status RULED_OUT only if you can name the committed number / file:line that makes your confound unable to explain the claim; put that number in next.
- status EXPLAINS if the evidence is consistent with your confound producing the claim.
- status NEEDS_RUN if the committed data cannot decide it; then next is ONE line, tagged "RUN: <existing script + flags>" if an existing control settles it, else "AUTHOR: <the control to write>".
- crux: the one fact your verdict hinges on. If the claim is itself a null ("X is uninformative / diffuse / at the noise floor"), a confound that EXPLAINS the statistic may BE the claim holding, not refuting it -- say which in the crux.
Number-gates (H2) that apply whatever your confound: a cited number decides only if a refuting outcome was possible and named before the run (a claim every outcome supports is framing -- treat as EXPLAINS); only with margin (exact-threshold clearance, a threshold authored after seeing the data, or selection from unreported attempts does not decide); and only within tested scope (stated scope exceeding the tested population, scale, or design strength is EXPLAINS on that ground).
Examples of next -- RULED_OUT: "same effect on held-out set, foo.json:42, n=30". NEEDS_RUN: "AUTHOR: mean/resample-ablation variant; only zero-ablation on record".

Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","additionalProperties":false,"required":["confound","status","crux","next"],"properties":{"confound":{"type":"string"},"status":{"type":"string","enum":["RULED_OUT","EXPLAINS","NEEDS_RUN"]},"crux":{"type":"string"},"next":{"type":"string","description":"RULED_OUT: the committed number/file:line. NEEDS_RUN: one line tagged RUN: or AUTHOR:. EXPLAINS: brief why."}}}