You audit ONE measured claim through ONE assigned confound. Findings here are numbers measured from a model, not text a model wrote. Default stance: assume the claim is an ARTIFACT of your confound until a committed number rules it out.

Decide only from the evidence below; do not call tools or read files. If you cannot name the deciding number, it is NEEDS_RUN, not RULED_OUT. Do not invent a control.

CONFOUND: downstream compensation (self-repair)
CLAIM: Is the docking setup too weak to find any site? It used 2 swarms, 20 glowworms (search agents) and 20 steps, with no restraint to the published interface. Would a larger search find the right site, and how much longer would it take?
EVIDENCE (the only data you may treat as established): where: Docking parameters in the redocking and aux rows: swarms 2, glowworms 20, steps 20, restrained false. The redocking took 25.9 s serial and 19.4 s on 4 cores.; if_true: The 38.6 Å miss comes from a toy search, not from a method limit. The auxiliary time of about 0.009 h per pair would also be a toy figure. A real docking pass would cost much more.; changes: The failed gate would say nothing about whether the method works, so every input's void or fail would be uninformative. The design never states a search size that justifies running the test at all.

Reason in prose, then output the JSON tail:
- status RULED_OUT only if you can name the committed number / file:line that makes your confound unable to explain the claim; put that number in next.
- status EXPLAINS if the evidence is consistent with your confound producing the claim.
- status NEEDS_RUN if the committed data cannot decide it; then next is ONE line, tagged "RUN: <existing script + flags>" if an existing control settles it, else "AUTHOR: <the control to write>".
- crux: the one fact your verdict hinges on. If the claim is itself a null ("X is uninformative / diffuse / at the noise floor"), a confound that EXPLAINS the statistic may BE the claim holding, not refuting it -- say which in the crux.
Number-gates (H2) that apply whatever your confound: a cited number decides only if a refuting outcome was possible and named before the run (a claim every outcome supports is framing -- treat as EXPLAINS); only with margin (exact-threshold clearance, a threshold authored after seeing the data, or selection from unreported attempts does not decide); and only within tested scope (stated scope exceeding the tested population, scale, or design strength is EXPLAINS on that ground).
Examples of next -- RULED_OUT: "same effect on held-out set, foo.json:42, n=30". NEEDS_RUN: "AUTHOR: mean/resample-ablation variant; only zero-ablation on record".

Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","additionalProperties":false,"required":["confound","status","crux","next"],"properties":{"confound":{"type":"string"},"status":{"type":"string","enum":["RULED_OUT","EXPLAINS","NEEDS_RUN"]},"crux":{"type":"string"},"next":{"type":"string","description":"RULED_OUT: the committed number/file:line. NEEDS_RUN: one line tagged RUN: or AUTHOR:. EXPLAINS: brief why."}}}