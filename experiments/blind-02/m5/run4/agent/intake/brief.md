Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget?

Use the four unbound PINDER cases examined by blind01’s unit probe. Pin their exact identities, prepared inputs and reference structures before execution. Treat this as a small pilot.

Compare three configurations:

1. CPU execution with standard rotational sampling.
2. GPU execution with the same sampling and scientific settings.
3. GPU execution with the documented denser rotational sampling.

Use MEGADOCK’s existing implementations. Keep scoring settings and the number of retained predictions fixed at 50.

First establish correct execution and scientific agreement between CPU and GPU configurations at identical search settings. Define justified numerical tolerances before examining comparative results.

Then measure whether denser search improves recovery. Report DockQ for the top-ranked prediction and the best of 50 separately. Use reference structures only for evaluation.

Use a small runtime calibration to define feasible budgets. Seal configurations, timing repetitions, comparison rules and the total spending cap before evaluation. Report complete workflow time, GPU activity and billed allocation cost.

Keep three conclusions separate: execution acceleration, scientific agreement at identical settings, and quality changes from additional search. Preserve negative results and budget overruns.

Identify any pipeline contract that cannot express these comparisons. Report that limitation explicitly without substituting a different scientific question.

Limit conclusions to these four cases. Do not infer biological efficacy from docking accuracy.

## Materials from blind-01 records (owner decisions 2026-11-02; recorded by an authorized reader agent)


Owner’s answer, 2026-11-02, case identities:

> "Codex addendum": a Codex reader copies the four case identities, their prepared input records and reference-structure sources from blind-01's records into a labelled section added to the brief. Your text stays unchanged.


Owner’s answer, 2026-11-02, same data location:

> "Yes, same mirror": the addendum also lists the mirror's URLs and SHA-256 hashes from blind-01's records, with provenance kept as unverified_mirror.


Owner’s words, 2026-10-31, first paragraph:

> I approve option 2: proceed with the unverified mirror for this local experiment. This supersedes the acquisition instruction that an unverified mirror can never count as usable. I think generally speaking, this rule is too hard - the mirror becomes usable from our use and results.


Owner’s words, 2026-10-31, third paragraph:

> Keep all scientific checks unchanged. Passing published-value anchors checks the properties those anchors measure; it does not prove the copy matches the original. Preserve that uncertainty in any resulting claims.


The FroDock distribution in these records has provenance `unverified_mirror`. The four recorded units are apo pairings from PINDER release `2024-02`, sampled at zero-based unit-manifest indices `3, 5, 9, 15`. Their recorded examination was a FroDock CPU/MPI unit-concurrency probe whose listed comparison outputs were fifty final ranked PDBs per unit. The identities and input records below are those sampled units.


### Cases and prepared input records

Each fenced CSV block is the original UTF-8 header followed by one original selected record, with LF line endings and a final LF. The path strings in those records are logical prepared-input names emitted by the recorded preprocessing; remote source locations are given separately. The full four-unit selection, in the order below, is 644 bytes with SHA-256 `f34c87e11bc77f02997f41aaae17cf6958ce02976b9621886d96c03029b27af0`.


#### 1. `1aua__A1_P24280--1aua__A2_P24280:apo`

PINDER system: `1aua__A1_P24280--1aua__A2_P24280`; kind: `apo`; unit index: `3`. In the recorded index entry, `pinder_s=True`, `apo_R=True`, `apo_L=True`; `apo_R_pdb=6f0e__A1_P24280.pdb` and `apo_L_pdb=6f0e__A1_P24280.pdb`.


Prepared CSV block: 179 bytes; SHA-256 `a97af77279a2cac61eee504904b82603710ae1194885ff132569cae5826d3e18`. The record alone, excluding header, is 155 bytes with SHA-256 `2e55e24dd1c1edea33bcc687150727fbb1cdd30ee5b3a1f34c59b8fd2f2e3431`.

```csv
id,kind,receptor,ligand
1aua__A1_P24280--1aua__A2_P24280,apo,1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_R.pdb,1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_L.pdb
```


The source-index selection is the single row whose `id` equals the system identifier above, with pairing `apo` and its recorded canonical `apo_R_pdb` / `apo_L_pdb` fields. The recorded preprocessing reads those complete monomer files, assigns chain labels `R` and `L` to receptor and ligand respectively, and serializes them to the named prepared PDBs. This describes the recorded input origin; no new residue or atom selection is introduced.


| Input source or reference location | Fetch URL | Recorded bytes | Recorded SHA-256 |
| --- | --- | ---: | --- |
| Index source; exact row selection above: `index.parquet` | https://pinderdata.org/2024-02/index.parquet | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Canonical receptor source: `pdbs/6f0e__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb | 192456 | `622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd` |
| Canonical ligand source: `pdbs/6f0e__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb | 192456 | `622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd` |
| Reference native bound complex: `pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb | 388881 | `a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48` |


The reference location is a directly fetched PDB, so no archive-member path applies. Reference contents are not included here.


#### 2. `1ax2__A1_P16404--1ax2__A2_P16404:apo`

PINDER system: `1ax2__A1_P16404--1ax2__A2_P16404`; kind: `apo`; unit index: `5`. In the recorded index entry, `pinder_s=True`, `apo_R=True`, `apo_L=True`; `apo_R_pdb=3n35__A1_P16404.pdb` and `apo_L_pdb=3n35__A1_P16404.pdb`.


Prepared CSV block: 179 bytes; SHA-256 `2357dfd034f88367b5e4b51d92effc039c8f413ed15030eacec858e7fa5006d8`. The record alone, excluding header, is 155 bytes with SHA-256 `9f1d3b6811303f2dccc7004f25a8827defdbfee1c1a8100186790a0b4674be3b`.

```csv
id,kind,receptor,ligand
1ax2__A1_P16404--1ax2__A2_P16404,apo,1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_R.pdb,1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_L.pdb
```


The source-index selection is the single row whose `id` equals the system identifier above, with pairing `apo` and its recorded canonical `apo_R_pdb` / `apo_L_pdb` fields. The recorded preprocessing reads those complete monomer files, assigns chain labels `R` and `L` to receptor and ligand respectively, and serializes them to the named prepared PDBs. This describes the recorded input origin; no new residue or atom selection is introduced.


| Input source or reference location | Fetch URL | Recorded bytes | Recorded SHA-256 |
| --- | --- | ---: | --- |
| Index source; exact row selection above: `index.parquet` | https://pinderdata.org/2024-02/index.parquet | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Canonical receptor source: `pdbs/3n35__A1_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb | 151794 | `b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e` |
| Canonical ligand source: `pdbs/3n35__A1_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb | 151794 | `b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e` |
| Reference native bound complex: `pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb | 300591 | `111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10` |


The reference location is a directly fetched PDB, so no archive-member path applies. Reference contents are not included here.


#### 3. `1dv1__A1_P24182--1dv1__B1_P24182:apo`

PINDER system: `1dv1__A1_P24182--1dv1__B1_P24182`; kind: `apo`; unit index: `9`. In the recorded index entry, `pinder_s=True`, `apo_R=True`, `apo_L=True`; `apo_R_pdb=3g8c__A1_P24182.pdb` and `apo_L_pdb=3g8d__A1_P24182.pdb`.


Prepared CSV block: 179 bytes; SHA-256 `90912611cb8363253de9a33055834c1edab8898865a69d413aae39efb11e0eb9`. The record alone, excluding header, is 155 bytes with SHA-256 `29685cddda4e4da851c041bcf8fbefe06b020c716e8014d492f44a4e1b4272fa`.

```csv
id,kind,receptor,ligand
1dv1__A1_P24182--1dv1__B1_P24182,apo,1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_R.pdb,1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_L.pdb
```


The source-index selection is the single row whose `id` equals the system identifier above, with pairing `apo` and its recorded canonical `apo_R_pdb` / `apo_L_pdb` fields. The recorded preprocessing reads those complete monomer files, assigns chain labels `R` and `L` to receptor and ligand respectively, and serializes them to the named prepared PDBs. This describes the recorded input origin; no new residue or atom selection is introduced.


| Input source or reference location | Fetch URL | Recorded bytes | Recorded SHA-256 |
| --- | --- | ---: | --- |
| Index source; exact row selection above: `index.parquet` | https://pinderdata.org/2024-02/index.parquet | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Canonical receptor source: `pdbs/3g8c__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb | 277182 | `48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60` |
| Canonical ligand source: `pdbs/3g8d__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb | 234657 | `1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c` |
| Reference native bound complex: `pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb | 536625 | `a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e` |


The reference location is a directly fetched PDB, so no archive-member path applies. Reference contents are not included here.


#### 4. `1nr5__A1_P07547--1nr5__A2_P07547:apo`

PINDER system: `1nr5__A1_P07547--1nr5__A2_P07547`; kind: `apo`; unit index: `15`. In the recorded index entry, `pinder_s=True`, `apo_R=True`, `apo_L=True`; `apo_R_pdb=1sg6__A1_P07547.pdb` and `apo_L_pdb=1sg6__A1_P07547.pdb`.


Prepared CSV block: 179 bytes; SHA-256 `cba9eaa447e9a2a228eaa9c322892f1b8cccb7687e1c24ec089edd4d11804aa9`. The record alone, excluding header, is 155 bytes with SHA-256 `ae51c38740db1a6d2d067395b18b37743b98085be8e40a72ce278c981028bb65`.

```csv
id,kind,receptor,ligand
1nr5__A1_P07547--1nr5__A2_P07547,apo,1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_R.pdb,1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_L.pdb
```


The source-index selection is the single row whose `id` equals the system identifier above, with pairing `apo` and its recorded canonical `apo_R_pdb` / `apo_L_pdb` fields. The recorded preprocessing reads those complete monomer files, assigns chain labels `R` and `L` to receptor and ligand respectively, and serializes them to the named prepared PDBs. This describes the recorded input origin; no new residue or atom selection is introduced.


| Input source or reference location | Fetch URL | Recorded bytes | Recorded SHA-256 |
| --- | --- | ---: | --- |
| Index source; exact row selection above: `index.parquet` | https://pinderdata.org/2024-02/index.parquet | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Canonical receptor source: `pdbs/1sg6__A1_P07547.pdb` | https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb | 234171 | `4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5` |
| Canonical ligand source: `pdbs/1sg6__A1_P07547.pdb` | https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb | 234171 | `4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5` |
| Reference native bound complex: `pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb` | https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb | 484785 | `ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861` |


The reference location is a directly fetched PDB, so no archive-member path applies. Reference contents are not included here.


### Recorded data and source locations

This inventory contains the four entries’ recorded structural/mapping locations, index and metadata, the test-monomer archive, PINDER source and the FroDock distribution with provenance `unverified_mirror`. Auxiliary predicted/alternative-apo files are included because the recorded PINDER entry downloader enumerates them; they are not additional selected cases or prepared apo records. The native reference files above are separate from the test-monomer ZIP.


The recorded test-monomer archive is https://pinderdata.org/2024-02/test_set_pdbs.zip (181968169 bytes; SHA-256 `884052770ed6c2e8d7ae9d133f0fb5dd618eaacca6d57425d3e096143057d99c`). Its separated holo members associated with these identities are:


- `test_set_pdbs/1aua__A1_P24280-R.pdb` and `test_set_pdbs/1aua__A2_P24280-L.pdb`.

- `test_set_pdbs/1ax2__A1_P16404-R.pdb` and `test_set_pdbs/1ax2__A2_P16404-L.pdb`.

- `test_set_pdbs/1dv1__A1_P24182-R.pdb` and `test_set_pdbs/1dv1__B1_P24182-L.pdb`.

- `test_set_pdbs/1nr5__A1_P07547-R.pdb` and `test_set_pdbs/1nr5__A2_P07547-L.pdb`.


The canonical apo files and native reference complexes listed above are not members of that ZIP. Their direct URLs are recorded individually.


Reachability checks used anonymous HTTPS HEAD requests from this reader’s machine, with no login and no payload download. Times below are UTC check completion times. Byte counts and SHA-256 values are copied from blind-01’s recorded inventory; these HEAD checks establish current reachability, not a new payload-hash comparison.


| Input | Exact fetch URL | Provenance | HEAD completed UTC | Recorded bytes | Recorded SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| `frodock_distribution:unverified_mirror` | https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz | `unverified_mirror` | 2026-11-02T16:07:44.007752+00:00 | 26637000 | `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4` |
| `index.parquet` | https://pinderdata.org/2024-02/index.parquet | `official_original_location` | 2026-11-02T16:07:44.224415+00:00 | 124511839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| `mappings/1aua__A1_P24280-R.parquet` | https://pinderdata.org/2024-02/mappings/1aua__A1_P24280-R.parquet | `official_original_location` | 2026-11-02T16:07:44.208062+00:00 | 17094 | `895025d624f59e49294f1931ca0f43009249544784c28a4186db4eb7ebc6c3d0` |
| `mappings/1aua__A2_P24280-L.parquet` | https://pinderdata.org/2024-02/mappings/1aua__A2_P24280-L.parquet | `official_original_location` | 2026-11-02T16:07:44.195741+00:00 | 17094 | `f788f0a1bacf513f72282b48ba9bba229b1d4e346102f52fa04acdc01a5b3502` |
| `mappings/1ax2__A1_P16404-R.parquet` | https://pinderdata.org/2024-02/mappings/1ax2__A1_P16404-R.parquet | `official_original_location` | 2026-11-02T16:07:44.278880+00:00 | 15672 | `b025372cd5ab64d4eba0802e6113ac6392c312ed164fb1e95c81b1f418176ea2` |
| `mappings/1ax2__A2_P16404-L.parquet` | https://pinderdata.org/2024-02/mappings/1ax2__A2_P16404-L.parquet | `official_original_location` | 2026-11-02T16:07:44.449497+00:00 | 15672 | `b8071e73b37010f6bc1a76b8fcab79b5843162e93d2a2ae7b9db04bc16cab863` |
| `mappings/1dv1__A1_P24182-R.parquet` | https://pinderdata.org/2024-02/mappings/1dv1__A1_P24182-R.parquet | `official_original_location` | 2026-11-02T16:07:44.509525+00:00 | 20459 | `608fa0418db362b88012e5ba62f13ce1ccf989679e969162995702acfc22de94` |
| `mappings/1dv1__B1_P24182-L.parquet` | https://pinderdata.org/2024-02/mappings/1dv1__B1_P24182-L.parquet | `official_original_location` | 2026-11-02T16:07:44.521255+00:00 | 20423 | `3b12d7e1fb064baf19f4a730d1e68bdff8eed6a6eb136f5320b5efe26fab9d83` |
| `mappings/1dv2__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/1dv2__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:44.544390+00:00 | 20551 | `e09ac0e6776e3f7b2ee3258733a45ebf84049cdb08c721ea256ce7983664dcbf` |
| `mappings/1nr5__A1_P07547-R.parquet` | https://pinderdata.org/2024-02/mappings/1nr5__A1_P07547-R.parquet | `official_original_location` | 2026-11-02T16:07:44.714713+00:00 | 19257 | `f94dbc1b085864611888d5fc5882d48206bd291ba57b262900a86c5af7fdd9d2` |
| `mappings/1nr5__A2_P07547-L.parquet` | https://pinderdata.org/2024-02/mappings/1nr5__A2_P07547-L.parquet | `official_original_location` | 2026-11-02T16:07:44.796258+00:00 | 19257 | `5a1298f932165350055e5cd02d8399406340acae56b204dcf362261cde5694e0` |
| `mappings/1sg6__A1_P07547.parquet` | https://pinderdata.org/2024-02/mappings/1sg6__A1_P07547.parquet | `official_original_location` | 2026-11-02T16:07:44.808786+00:00 | 19188 | `655df7b00914130b70d2e6e32a20502936818b49b6d4b772cb8a335e166da0a7` |
| `mappings/2gps__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2gps__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:44.833243+00:00 | 20762 | `0fbde0e0456958a928883bc6a2e9aefa755801c3303df77b9a7ef7c94f3cb1f1` |
| `mappings/2gpw__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2gpw__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:44.978375+00:00 | 20762 | `db91d019689d0bc015bbc1255b58634e8fd51a9112c13c8cdc0bde6ae749ccb8` |
| `mappings/2j9g__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2j9g__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.056683+00:00 | 20533 | `c6ebcc427e1672fc81881a87c2c04547c6daa4c3e70fc39599f260b40a24b18a` |
| `mappings/2v58__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2v58__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.044919+00:00 | 20520 | `834fe0e45123d0a364fa09f27bad0ba71e9b34b5d85ef5592cf89a4978c10446` |
| `mappings/2v59__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2v59__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.064071+00:00 | 20508 | `1fa729b18ce24f7945e4790f24a2b81994f6489609c00516a3e74f1e140c3c75` |
| `mappings/2v5a__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2v5a__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.229977+00:00 | 20520 | `32986672aa73be0c02d78cbd01bac271cd8f953a179d8fbe7df1b2f78d5ab58e` |
| `mappings/2vr1__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2vr1__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.336678+00:00 | 20525 | `afbc4c4d158c8dfff94dd8a74d646b86a2b01e4171e62b82e451a51997f5465a` |
| `mappings/2w6m__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2w6m__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.305305+00:00 | 20520 | `a5f23797e6b354d3d3d6a6207ff3fdbe06e9b6cbb81cee5a5e60e55f662fddbe` |
| `mappings/2w6n__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2w6n__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.325338+00:00 | 20508 | `06ddf99c261999aacaa2bfc15c07c592d4aacf3fe6ed0185922065d44b62f874` |
| `mappings/2w6o__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2w6o__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.520218+00:00 | 20512 | `7de3609f62c7a26e098539a0ff54f8b8422629c8ac311c1e9a7397f513110e99` |
| `mappings/2w6p__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2w6p__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.580425+00:00 | 20516 | `d77b4900aa3d4a2903aa8d0fa4df0e2a5b8e960147cc1aef97df9577aa566a64` |
| `mappings/2w6q__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2w6q__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.593335+00:00 | 20520 | `6ca0e7c9d1e0c4bf2a911cecb6f49c0d27f18145d8ef9b37924904ab32ea7fea` |
| `mappings/2w6z__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2w6z__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.601285+00:00 | 20520 | `d2202d385d1eb61e0a6cdbe6c734e99feae5eeeae26dca21594e7c997f5f6228` |
| `mappings/2w70__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2w70__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.747707+00:00 | 20516 | `52ab2f8cc1bcdd1165390d989c762179ebd621f5737cdf1bd7717813bc3ce2fa` |
| `mappings/2w71__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/2w71__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.825349+00:00 | 20520 | `f6cf2b87d880ce586693b1d7fcc10abd28f4b58cf7210a9fb43f6834db6f3ddf` |
| `mappings/3g8c__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/3g8c__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.868117+00:00 | 20457 | `367ef1aa764dd0637630b7fbbbf3a87707da475e4efa40aaf5864e720fce30c6` |
| `mappings/3g8d__A1_P24182.parquet` | https://pinderdata.org/2024-02/mappings/3g8d__A1_P24182.parquet | `official_original_location` | 2026-11-02T16:07:45.792709+00:00 | 20077 | `26607578e3829b4b13b21b11cec6f46e79da26c5933c13032e4d83996b0cd08c` |
| `mappings/3n35__A1_P16404.parquet` | https://pinderdata.org/2024-02/mappings/3n35__A1_P16404.parquet | `official_original_location` | 2026-11-02T16:07:45.972480+00:00 | 15771 | `e40ed097e43e05f2b5626dc505061890f2d2addb52a2c8e7552aff476ec927a7` |
| `mappings/3n36__A1_P16404.parquet` | https://pinderdata.org/2024-02/mappings/3n36__A1_P16404.parquet | `official_original_location` | 2026-11-02T16:07:46.068227+00:00 | 15771 | `c56a03bd481256f833518e2c9b8d5cfaa09f290410ed9992d48af8beb985bfee` |
| `mappings/3n3h__A1_P16404.parquet` | https://pinderdata.org/2024-02/mappings/3n3h__A1_P16404.parquet | `official_original_location` | 2026-11-02T16:07:46.135944+00:00 | 15771 | `487974339e0811cd3d7ce7edadbde80534d5824311a3cb7bae02890031372052` |
| `mappings/6f0e__A1_P24280.parquet` | https://pinderdata.org/2024-02/mappings/6f0e__A1_P24280.parquet | `official_original_location` | 2026-11-02T16:07:46.173238+00:00 | 17316 | `7b309badad0192bd35ce0346c8a038104afc4951c3714584b47ad87d03f9ce29` |
| `mappings/7zg9__A1_P24280.parquet` | https://pinderdata.org/2024-02/mappings/7zg9__A1_P24280.parquet | `official_original_location` | 2026-11-02T16:07:46.238764+00:00 | 17078 | `7d4511ebc490fa54c26b893e30d688c4e0eff7768deab78a3df76d692f2086cd` |
| `mappings/7zga__A1_P24280.parquet` | https://pinderdata.org/2024-02/mappings/7zga__A1_P24280.parquet | `official_original_location` | 2026-11-02T16:07:46.455556+00:00 | 17094 | `d2f5ee0a0e22947d8f0349de8809c8112f7569375161b669ffae78219900b231` |
| `mappings/7zgb__A1_P24280.parquet` | https://pinderdata.org/2024-02/mappings/7zgb__A1_P24280.parquet | `official_original_location` | 2026-11-02T16:07:46.474270+00:00 | 17094 | `1af9e6478066fea6553144af7332e3570b3bad61013409a3d4e062b68e59fbad` |
| `mappings/7zgc__A1_P24280.parquet` | https://pinderdata.org/2024-02/mappings/7zgc__A1_P24280.parquet | `official_original_location` | 2026-11-02T16:07:46.420722+00:00 | 17300 | `e464496d35973d62ff4d40dd6c6cec8ddb0360abdac99d0624f8435fcfd34c24` |
| `mappings/7zgd__A1_P24280.parquet` | https://pinderdata.org/2024-02/mappings/7zgd__A1_P24280.parquet | `official_original_location` | 2026-11-02T16:07:46.505958+00:00 | 17292 | `2cf707e289645c3237bbf226fcef81ddd3fd88789e947ced6c703ab09f651e2f` |
| `metadata.parquet` | https://pinderdata.org/2024-02/metadata.parquet | `official_original_location` | 2026-11-02T16:07:46.752796+00:00 | 103835983 | `3e3cfdc21d6c685891d6732edda13fea9d5566d056dfea56a2ae902ab80b4e6c` |
| `pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb | `official_original_location` | 2026-11-02T16:07:46.761443+00:00 | 388881 | `a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48` |
| `pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb | `official_original_location` | 2026-11-02T16:07:46.814913+00:00 | 300591 | `111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10` |
| `pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:46.730485+00:00 | 536625 | `a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e` |
| `pdbs/1dv2__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/1dv2__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.014836+00:00 | 280503 | `f7a8e4aa61bb8046c2cb9fdedaf34a2dc8281371af96b14566388a672d21de4b` |
| `pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb` | https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb | `official_original_location` | 2026-11-02T16:07:47.077968+00:00 | 484785 | `ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861` |
| `pdbs/1sg6__A1_P07547.pdb` | https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb | `official_original_location` | 2026-11-02T16:07:47.022679+00:00 | 234171 | `4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5` |
| `pdbs/2gps__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2gps__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.051142+00:00 | 279531 | `eb28f1ff89b49ea335e276e2ce35f4415ee87035ba2ecafdc9554b15b598641d` |
| `pdbs/2gpw__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2gpw__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.373182+00:00 | 278235 | `49c11dab2e53631c9c56707b630e0740c6d4d7f87b63943475360c4f5a6663dd` |
| `pdbs/2j9g__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2j9g__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.611116+00:00 | 277344 | `6f12c2aa199753da317ae8a6121a06dde1c731c863c95dcfda733efde9ecca64` |
| `pdbs/2v58__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2v58__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.419480+00:00 | 278235 | `a2635ce6e42c882dbb9563fbb047a496a1ca8fa11a82df0bc851d775ae3a2688` |
| `pdbs/2v59__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2v59__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.424662+00:00 | 277506 | `96b14067946c2bd344187065501abe4c4d250338bd011fd1e1f52b50109b036c` |
| `pdbs/2v5a__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2v5a__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.636619+00:00 | 278235 | `e2b1736a1bf59f26519fab295645f9244d7f45f42e661a550c5c84bf4f9b247f` |
| `pdbs/2vr1__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2vr1__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.650937+00:00 | 277506 | `3958af75fef3ae62b68065a6bef8fff7749ca75605f260f32a2ab7033aeace87` |
| `pdbs/2w6m__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2w6m__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.723679+00:00 | 278235 | `549ede56edc006db49cdd5b681b75a73b765c7b48f87e71d9661d19e7a4097c8` |
| `pdbs/2w6n__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2w6n__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:48.111243+00:00 | 277506 | `b11497561689f6366352cd4ddebec5ed3e026622a228854f990f500552248b42` |
| `pdbs/2w6o__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2w6o__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.919895+00:00 | 277506 | `6566ddfb110ea8549e8f71adba241e07d41c9d4fbc2435127c42df99d3373775` |
| `pdbs/2w6p__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2w6p__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.972680+00:00 | 278154 | `e2ff156afa33f50d5cbcff1532c30fcda392c3fa9f730a72820ad7881759133e` |
| `pdbs/2w6q__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2w6q__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:47.967674+00:00 | 278235 | `ef1213cdb4e8d8d3044cedded85a17252690e08f7fdf8efec53dd78f3a9107b6` |
| `pdbs/2w6z__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2w6z__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:48.211848+00:00 | 278235 | `29a4a1451c3e765d7de202c61aeb9f1c62e4371ee7a4f087f50ede867ef48b05` |
| `pdbs/2w70__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2w70__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:48.183085+00:00 | 278154 | `808d961efee834211e86a4010a73fa2c71cb5d9baedee1142a43e70e484f7532` |
| `pdbs/2w71__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/2w71__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:48.231058+00:00 | 278235 | `a8138e57f5f0eae54969045e47ea9cf3fe3623145d7d1c4ca07b93b3d02096b6` |
| `pdbs/3g8c__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:48.431096+00:00 | 277182 | `48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60` |
| `pdbs/3g8d__A1_P24182.pdb` | https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb | `official_original_location` | 2026-11-02T16:07:48.419566+00:00 | 234657 | `1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c` |
| `pdbs/3n35__A1_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb | `official_original_location` | 2026-11-02T16:07:48.479222+00:00 | 151794 | `b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e` |
| `pdbs/3n36__A1_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/3n36__A1_P16404.pdb | `official_original_location` | 2026-11-02T16:07:48.504573+00:00 | 151794 | `acf6fae1beda8c5e0a2ca50c4816ce2dd97d08c034ebefcc0274524f12ccd4bb` |
| `pdbs/3n3h__A1_P16404.pdb` | https://pinderdata.org/2024-02/pdbs/3n3h__A1_P16404.pdb | `official_original_location` | 2026-11-02T16:07:48.681641+00:00 | 151794 | `e7e5d801e766c9815da00dce1f21e5984c9fc477f9b57eb698fa07d045893667` |
| `pdbs/6f0e__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb | `official_original_location` | 2026-11-02T16:07:48.692376+00:00 | 192456 | `622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd` |
| `pdbs/7zg9__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/7zg9__A1_P24280.pdb | `official_original_location` | 2026-11-02T16:07:48.792651+00:00 | 193995 | `c54e1c9833492a99fc699cf8c6ac5497f2abfa1e38d75419d812ee4972e1cd44` |
| `pdbs/7zga__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/7zga__A1_P24280.pdb | `official_original_location` | 2026-11-02T16:07:48.781602+00:00 | 194238 | `986464c54973929f839ad936adacea12309dee2338fc3279ac2f66df021c7aae` |
| `pdbs/7zgb__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/7zgb__A1_P24280.pdb | `official_original_location` | 2026-11-02T16:07:49.082121+00:00 | 194481 | `5cf336d9120a8fb449968e1a6a30de92799249b819f93b7dda1cb160a7794055` |
| `pdbs/7zgc__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/7zgc__A1_P24280.pdb | `official_original_location` | 2026-11-02T16:07:48.937027+00:00 | 189297 | `84730f6784fcd9d02560f03a257aa2d7db83f471807b48d0c294e12da004ae81` |
| `pdbs/7zgd__A1_P24280.pdb` | https://pinderdata.org/2024-02/pdbs/7zgd__A1_P24280.pdb | `official_original_location` | 2026-11-02T16:07:49.065859+00:00 | 193833 | `8f32aae242535a02f5f8b917097fc6399d73728db6153f5565e2f158d37607ba` |
| `pdbs/af__P07547.pdb` | https://pinderdata.org/2024-02/pdbs/af__P07547.pdb | `official_original_location` | 2026-11-02T16:07:48.980476+00:00 | 982854 | `bb67ff3ece04a5369db404a2a373e0d20c9d84327de94afe3e21f36b42d7221d` |
| `pdbs/af__P16404.pdb` | https://pinderdata.org/2024-02/pdbs/af__P16404.pdb | `official_original_location` | 2026-11-02T16:07:49.209712+00:00 | 176094 | `a7004016e485c59b8b0ee7000162a3558211183c75c002ed13308b8f87d9d2db` |
| `pdbs/af__P24182.pdb` | https://pinderdata.org/2024-02/pdbs/af__P24182.pdb | `official_original_location` | 2026-11-02T16:07:49.269472+00:00 | 280341 | `760f24b4fa0993c0d646ca6d58e62df51da969e87fabf691475e61430fd7e3cc` |
| `pdbs/af__P24280.pdb` | https://pinderdata.org/2024-02/pdbs/af__P24280.pdb | `official_original_location` | 2026-11-02T16:07:49.275847+00:00 | 199341 | `27f96833ff571d18aee33b6d43bdcd7e41a20e923e8885bdc95c843bff268a75` |
| `pinder_source@ebeb28a2f8411363cef722b7d293c978f7442672` | https://codeload.github.com/pinder-org/pinder/tar.gz/ebeb28a2f8411363cef722b7d293c978f7442672 | `official_original_location` | 2026-11-02T16:07:49.312427+00:00 | 22835334 | `b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd` |
| `test_set_pdbs.zip` | https://pinderdata.org/2024-02/test_set_pdbs.zip | `official_original_location` | 2026-11-02T16:07:49.413702+00:00 | 181968169 | `884052770ed6c2e8d7ae9d133f0fb5dd618eaacca6d57425d3e096143057d99c` |
| `test_set_pdbs/1aua__A1_P24280-R.pdb` | https://pinderdata.org/2024-02/test_set_pdbs/1aua__A1_P24280-R.pdb | `official_original_location` | 2026-11-02T16:07:49.476820+00:00 | 194481 | `b9ecdbf04547fbd00c2d6864c3f409a821b86d0c2341a29d79a2c7e0a83c0cc3` |
| `test_set_pdbs/1aua__A2_P24280-L.pdb` | https://pinderdata.org/2024-02/test_set_pdbs/1aua__A2_P24280-L.pdb | `official_original_location` | 2026-11-02T16:07:49.525399+00:00 | 194481 | `c4c8f851151c6e28744df3b622fb7452d301b44e58066fcea3227638dc20dbd0` |
| `test_set_pdbs/1ax2__A1_P16404-R.pdb` | https://pinderdata.org/2024-02/test_set_pdbs/1ax2__A1_P16404-R.pdb | `official_original_location` | 2026-11-02T16:07:49.519350+00:00 | 150336 | `c4fed656e98dfa44e1fff709d79c01d02bb68a66843b43591007559d81675e59` |
| `test_set_pdbs/1ax2__A2_P16404-L.pdb` | https://pinderdata.org/2024-02/test_set_pdbs/1ax2__A2_P16404-L.pdb | `official_original_location` | 2026-11-02T16:07:49.695702+00:00 | 150336 | `f0a761161d2eb5ceb13db3ffc4e47bea9456d73c7774087cf8cf6204e0a6aa45` |
| `test_set_pdbs/1dv1__A1_P24182-R.pdb` | https://pinderdata.org/2024-02/test_set_pdbs/1dv1__A1_P24182-R.pdb | `official_original_location` | 2026-11-02T16:07:49.696382+00:00 | 271593 | `cead07e446397d66d91d4fde9be50d8e58c72aa1b55e9e345b01f5497942d1eb` |
| `test_set_pdbs/1dv1__B1_P24182-L.pdb` | https://pinderdata.org/2024-02/test_set_pdbs/1dv1__B1_P24182-L.pdb | `official_original_location` | 2026-11-02T16:07:49.921632+00:00 | 265113 | `40cce57a67c36291552c1a351ed1650c15d23b2d66d3aa53a4918244422d8d38` |
| `test_set_pdbs/1nr5__A1_P07547-R.pdb` | https://pinderdata.org/2024-02/test_set_pdbs/1nr5__A1_P07547-R.pdb | `official_original_location` | 2026-11-02T16:07:49.804990+00:00 | 242433 | `536bdad1af469b224f0fbbf0c13d28063dac30f48308882d23c8e5c804ea761c` |
| `test_set_pdbs/1nr5__A2_P07547-L.pdb` | https://pinderdata.org/2024-02/test_set_pdbs/1nr5__A2_P07547-L.pdb | `official_original_location` | 2026-11-02T16:07:49.938439+00:00 | 242433 | `9c99a2ad5c73fcb28d558fefc1dfe1b912accbbbcf995a906194e9b858163dea` |


### Software pins from blind-01 run9’s records

These are historical run9 records. They do not specify blind-02 configurations.


- **MEGADOCK:** the inspected run9 intake, harness and saved setup records contain no MEGADOCK repository/package, commit, tag/release, build command, CPU/GPU implementation pin, build-option pin, or standard/denser rotational-sampling option. No MEGADOCK setting has been added to this materials record.
- **PINDER, including run9’s DockQ implementation:** repository identifier `https://github.com/pinder-org/pinder`, commit `ebeb28a2f8411363cef722b7d293c978f7442672`, tree `adc153de2eef1ac428c1136d609b30728c88cc7b`. The fetchable source archive, size and SHA-256 are in the inventory above; archive root is `pinder-ebeb28a2f8411363cef722b7d293c978f7442672/`. No tag/release was recorded. Installed version was the archive-build SCM value `0.0.0+gebeb28a2`. Run9 used the `pinder_eval` DockQ implementation in this repository; a separate standalone DockQ package/release pin was not recorded.
- **Run9’s actual docking software, FroDock:** distribution provenance `unverified_mirror`, README label `FRODOCK 3.12`, dated February 8, 2020. No FroDock git commit or authenticated original release hash was established. Archive root is `frodock3_linux64/`; its URL, bytes and SHA-256 appear above. The four run9 GNU/MPI tools were recorded as compiled: `frodockgrid_mpi_gcc`, `frodock_mpi_gcc`, `frodockcluster_gcc`, `frodockview_gcc`. The archive’s `frodock3_linux64/bin/soap.bin` was recorded as 7,536,604 bytes, SHA-256 `791f31ec8ef1ef1466092b425638e926755519c9626f5678ca675ef6c76234fc`; it is an internal member, not another fetch location.


Run9’s recorded build/install commands included the following exact script excerpts. Variable names denote that run’s logical build layout.

```sh
python3 -m venv --system-site-packages "$VENV"
"$VPY" -m pip install --no-cache-dir --upgrade "setuptools>=64" "setuptools_scm>=8" packaging wheel 2>&1 \
  | tee "$SOUT/pip_install_build_tools.log"
SETUPTOOLS_SCM_PRETEND_VERSION="$PINDER_SCM_VERSION" SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PINDER="$PINDER_SCM_VERSION" \
  "$VPY" -m pip install --no-cache-dir --no-build-isolation "$WORK/$BP/pinder-src" 2>&1 | tee "$SOUT/pip_install_pinder.log"
"$VPY" -m pip install --no-cache-dir fire 2>&1 | tee "$SOUT/pip_install_fire.log"
printf 'numpy<2\n' > "$SOUT/venv_constraints.txt"
"$VPY" -m pip install --no-cache-dir --upgrade -c "$SOUT/venv_constraints.txt" networkx pandas scikit-learn 2>&1 \
  | tee "$SOUT/pip_install_venv_refresh.log"
```


Run9’s FroDock build invocation was `( cd "$BP/frodock" && ./compile_frodock.sh )`. Run9 also applied a recorded PINDER adapter/entry-point repair patch, SHA-256 `295af03d22550b21c1e0852f723f324c35e9f5caa75e1759ba82bee5ed0259c3`, before installation. The patch repaired CSV reading, entry-point dispatch, input staging, binary-path construction, output copying and relative input-path resolution. The measured wrapper additionally contained ligand HETATM chain-label restoration. These are part of the recorded run9 baseline, not a pristine-source assertion.


Run9’s saved environment record gives Python `3.10.12`, Open MPI `4.1.2`, stock and venv torch `2.7.0`, Intel Xeon Platinum `8480+`, and 26 host logical CPUs. Its CUDA layout was `distro`, with `nvcc=/usr/bin/nvcc`, includes `/usr/include`, and libraries `/usr/lib/x86_64-linux-gnu`; the recorded FroDock build did not use CUDA. The run9 docking wrapper exposed zero GPUs (`CUDA_VISIBLE_DEVICES=""`), used eight MPI ranks and fifty solutions, and scored through PINDER. The saved freeze includes `biotite==1.2.0`, `numpy==1.26.4`, `networkx==3.4.2`, `pandas==2.3.3`, `scikit-learn==1.7.2`, `pyarrow==25.0.1`, `fire==0.7.1`, `packaging==26.3`, and `setuptools-scm==10.3.4`. The setup record reports no apt packages newly installed; the setup script listed GNU/build tools, Open MPI, FFTW and HDF5 packages. No immutable base-image digest or complete OS dependency lock was recorded.


The FroDock distribution with provenance `unverified_mirror` contained compiled/prebuilt alternatives; run9 recorded all four required tools as compiled. Its README and build-script version labels differ internally, as recorded in blind-01. Those records supply no MEGADOCK implementation or sampling-option evidence.


The mirror copy’s identity with the original is unverified. Agreement with published-value anchors checks only the properties those anchors measure and does not establish that identity.


## Calibration request (science step s03)

This request specifies one bounded runtime calibration, not the seed's full experiment. Preserve the seed above. The only execution configuration in this calibration is CPU standard. No fresh GPU comparison, dense search, concurrency, method proposal or quality-effect inference is requested. The operator selects --stop-after-reproduce. Do not continue to profile, seal, propose, implement or evaluate.

Scientific purpose and limitation

Tree run 20261103-0124-tree, seed:idea:2, assumes eval_runtime_s <=60 seconds for complete evaluation of one case's 50 saved predictions. Its measuring phase is agreement, but the compiled record loses configuration detail. Measure a cheaper necessary condition first: maximum complete evaluator wall across CPU-standard outputs on all four fixed cases. This is a deliberately partial falsification screen. A value above60 rejects that unchanged allowance. Values at most60 retain the candidate provisionally; they do not resolve the full card input, prove a maximum for GPU/dense outputs, validate CPU/GPU agreement, or release quality study. The branch card R1:physical:P1 remains a conditional alternative with independently calibrated evaluator reserves. Do not write a ledger entry claiming full card_number_resolved from this screen.

Configuration, materials and provenance

Use exactly the four apo cases and preparation/reference records above, in listed order: 1aua, 1ax2, 1dv1, 1nr5 (full IDs above). MEGADOCK source 9575280c875732553266e26adc607dd892b02616; PINDER source ebeb28a2f8411363cef722b7d293c978f7442672; release2024-02. Reuse documented preparation, atom/residue selection, fixed R/L chains and PDB serialization from run2; verify hashes of retrieved source objects and prepared inputs against retained run2 intake records before execution. Hash actual input/native/script/binary/dependency bytes; preserve mirror provenance unverified_mirror. The material addendum contains CSV/source hashes; those are not automatically prepared-PDB hashes. No source or scientific setting changes to make a result pass. If historical prepared-byte identity cannot be established, stop and report unknown transferability rather than silently substitute a preparation.

Target one H100 PCIe80GB allocation with same26-logical-CPU host entitlement as run2. CPU docking runs on its host; allocated GPU is paid for and remains idle for docking. Record host CPU/topology/affinity, RAM, CUDA/compiler/FFTW/OpenMP, dependency lock, MEGADOCK/decoygen hashes, evaluator source hash and allocation identity. MEGADOCK printed4.1.3 versus source tag4.1.4 is retained uncertainty; source/binary identities must be recorded rather than explained away. Pin PINDER evaluation dependencies consistently with run2's recorded environment; report changes and do not pool incompatible timings. No CPU-only market tariff claim.

Command and harness requirements

Author a fresh harness. Exact reuse of run2 run_anchors.sh is unsuitable: it runs all12 configuration/case jobs and native density contrasts. run_command.sh runs only the four CPU-standard jobs, once each, serially, with OMP_NUM_THREADS=26, OMP_DYNAMIC=FALSE, OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1, NUMEXPR_NUM_THREADS=1, LC_ALL=C, LANG=C. Preserve inherited CUDA_MPS_* variables unchanged; no daemon management. For each fixed case, scientific docking argv is:

    baseline-published/megadock/megadock -R data/inputs/<prefix>_R.pdb -L data/inputs/<prefix>_L.pdb -o out/<case>/docking.out -N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3 -r 3600

Expand placeholders from the frozen manifest, never from native quality. Reconstruct all50 complexes using pinned decoygen and run2 receptor/ligand concatenation with END only after both chains. Preserve every scientific output, including failures. Record docking-only printed timers and separate monotonic invocation-to-last-pose walls. No evaluator import or native access in run_command.sh. run_anchors.sh must invoke bash harness/run_command.sh once, then perform checks and the evaluator benchmark below. Record all extra calibration measurements under out/; intake anchor scoring remains whatever the actual intake specifies. Never invent a published anchor or count empty 0/0 anchors as independent scientific validation.

Execution checks before timing

Require verified source/material/preparation identity, four header lines plus50 finite seven-field ranked rows, positive actual grid and voxel1.2, expected standard sampling,50 readable nonempty final complexes with expected R/L chains and atom inventory. Record reference chain/residue mapping from pinned preparation before timing. No native-guided docking/ranking. Use a separate native-self evaluator smoke check per case before benchmarks: same native file as model and reference, identical fixed mapping, mathematical identity target DockQ1 within1e-6. Label this DESIGN identity check, not independent published-value reproduction or docking accuracy validation. Failure stops benchmark; preserve measured value. Do not loosen it after inspection. This smoke does not justify the card's CPU/GPU score tolerance0.20.

Evaluator benchmark, sealed now

Use pinder.eval.dockq.BiotiteDockQ with the same calculation as run2 run_anchors.sh:50-56: native=the case's pinned reference; decoys=all50 saved CPU-standard complexes; native_receptor_chain=['R'], native_ligand_chain=['L'], decoy_receptor_chain=['R'], decoy_ligand_chain=['L'], parallel_io=False; calculate(), validate50 unique model names and finite DockQ, then write full result CSV. Keep all endpoint values in owner artifacts; do not compute density contrasts or issue recovery/agreement verdicts.

Run four fixed serial blocks. Each block visits all four cases in listed order, one fresh Python subprocess per case. Each child imports evaluator from scratch, reads all50 poses and native, calculates, validates, writes and flushes its CSV, then exits. Parent monotonic timer begins immediately before process creation and ends after successful child exit and output existence/size check. This includes interpreter/import, local file I/O, calculation, validation and CSV serialization/flush. Store calculation-only timers separately; they never replace primary full-child wall. Do not flush OS caches or treat later blocks as cold-disk samples. All16 full-child timings, including first block, are retained; no untallied warmup or selective exclusions. Setup/install, docking/reconstruction and operator retrieval/export lie outside evaluator endpoint but remain separately timed and charged in allocation accounting.

Primary endpoint T=max of the16 complete evaluator walls, seconds. Store per-case max and all raw values. Timeout each child at180 seconds, with process-group cleanup and partial artifacts retained. An observed live child exceeding60 seconds already falsifies the60-second screen; if it times out180 seconds, retain a right-censored lower bound and mark T unknown, allowance failed, rather than substitute180 as completed wall. Continue other prespecified cases/blocks only if lifecycle budget allows; no added repeats. Missing rows, nonfinite values, incorrect pins, failed smoke or missing primary boundaries make screen inconclusive, never a passing fast evaluator. A valid completed sample over60 remains a falsification even if later infrastructure fails. Never trim large cases or failed attempts to obtain a maximum under60.

Output out/calibration.json should carry protocol identity/hash, cases/configuration, pins, setup checks, native-self smoke values, all16 records {case_id, block, status, wall_s or null, lower_bound_s or null, n_scored}, T_s or null, per-case maxima, allowance60_screen {pass|fail|unknown}, explicit scope CPU-standard-only, stage walls, allocation projection and receipts. Preserve raw CSV/logs, manifests and hashes. Missing actual invoice stays unknown; separately report estimated dollars from allocation wall and verified tariff. No inference from m5 overall reproduce PASS to scientific agreement.

Decision rule, fixed before execution

- Any valid complete evaluator wall>60 seconds, or confirmed evaluator-only elapsed lower bound>60: drop seed:idea:2's unchanged60-second budget allowance and cap schedule. Preserve failure. A changed allowance requires a new sealed plan; it cannot rescue this outcome. Keep physical branch candidate conditional, with measured evaluator reserve and later GPU coverage, if affordable.
- All16 valid complete walls<=60 with setup/smoke/pins valid: retain C2 provisionally, along with physical branch. Do not mark the full eval_runtime_s record resolved; GPU-standard and dense evaluation coverage remain unmeasured. Scientific tolerances and comparison executor remain blockers to final study.
- Missing or invalid protocol/identity/output/timing or interrupted execution without a valid>60 witness: unknown. Repair the specific execution problem before another scientific claim. No automatic retry beyond pipeline's bounded infra rules; preserve all attempts.

Budget, stop and lifecycle

Forecast GUESS: typical maximum complete evaluator wall5-30 seconds, broad expected1-60 seconds. Historical run2 anchors receipt1571s includes docking, reconstruction, scoring and transfer; freeze receipt1402s has no docking. Their169s difference is only indirect aggregate evidence, never per-case evaluator timing. No measured per-case evaluator runtime exists in those summaries.

One fresh run only, setup+anchors+freeze, no profile/concurrency. Historical setup145s + anchors1571s + freeze1402s =3118s=0.8661h before additional wrapper/model/other overhead. Reserve total2 allocation hours for the substantially smaller CPU-only benchmark, including retrieval, uploads, setup, model idle, smoke,16 scorings, freeze, export and termination. At historicalUSD3.29/h this isUSD6.58; addUSD1.42 billing/tax/termination uncertainty =USD8 projected all-in. USD10 hard lifecycle spending stop; no launch if current compatible tariff/tax/termination projection exceedsUSD10 or cannot remain strictly belowUSD20. Stop new scientific work at90 allocated minutes, reserve remaining30 minutes for export/termination. Stop at2 allocated hours orUSD10, whichever first; external operator watchdog must include idle and terminate the allocation. No paid persistent filesystem, no larger replacement box or additional rental. The general6h soft/12h hard ceilings remain upper limits, not this test's budget. Preserve partial results and overruns.

Operator must verify supplied --stop-after-reproduce wrapper exits after setup/anchors/freeze and termination path is bounded before allocating. This is an offered wrapper option, not a claim m5 pipeline.js itself has a direct stop flag. If intake/harness cannot express this CPU-only descriptive calibration or adequate endpoint boundaries, report the exact contract gap and stop before paid work. Do not fall through to original three-configuration scientific study. No owner decision is needed for this underUSD10 calibration preparation.


### Historical evidence supplied to close run3 intake failure

This is an evidence-handoff repair only. Run3 did not execute setup, docking or evaluator timing. Its intake found the nine canonical apo/native URLs reachable, but could not verify the additional historical prepared-byte requirement from the brief alone. Intake must not read earlier experiment folders; the authorized scientific reader supplies the relevant records below inside this brief. References label provenance, not additional files intake must open. All quantities below are historical evidence, not new calibration measurements or independently published anchors. The same four cases, CPU-standard configuration, evaluator endpoint, 16 attempts, smoke, thresholds, decision rule and budget above remain fixed. Do not weaken the historical prepared-byte gate.

Inputs below are generated from the addendum's already pinned raw PDBs. They are not a new dataset, new case or external prepared-file download. Verify source payload hashes from the unchanged addendum during setup; apply the historical preparation; verify all eight generated hashes against the historical targets below before docking. Missing generated files before setup are not by themselves inaccessible source data. Any actual source failure, hash mismatch or unsupported generation remains an explicit failure; never force data=available or bypass an intake gate.

Historical intake carried prepared hashes as null because preparation had not run yet. Historical setup then printed the eight actual hashes. Authoritative evidence is run2's executed setup log, not those intake nulls. Preparation changes only chain field column22 on ATOM/HETATM/ANISOU/TER records, retaining every other byte and line; no atom/residue selection, renumbering, alignment or new serialization library. Short data/inputs/<prefix>_R.pdb and _L.pdb aliases are byte copies. Native reference is the unchanged raw bound-complex PDB listed in each case. Reference use remains evaluation only.

Historical case and prepared-byte manifest (copied from experiments/blind-02/m5/run2/agent/intake/data.json cases; hashes from agent/results/reproduce/out/setup/setup.log:510-519):

```json
{
  "release": "2024-02",
  "cases": [
    {
      "id": "1aua__A1_P24280--1aua__A2_P24280:apo",
      "system_id": "1aua__A1_P24280--1aua__A2_P24280",
      "kind": "apo",
      "unit_manifest_index_zero_based": 3,
      "prepared_record": {
        "id": "1aua__A1_P24280--1aua__A2_P24280",
        "kind": "apo",
        "receptor": "1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_R.pdb",
        "ligand": "1aua__A1_P24280--1aua__A2_P24280/inputs/apo/1aua_apo_L.pdb"
      },
      "apo_receptor_source": "pdbs/6f0e__A1_P24280.pdb",
      "apo_ligand_source": "pdbs/6f0e__A1_P24280.pdb",
      "reference": "pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb",
      "historical_prepared_sha256": {
        "receptor": "162aad227fdbdb6a0600a5b6a4f5b461663ee7ce419798061ea0cd8ae9be6f35",
        "ligand": "f5158ee7030ce712cc5fb419d1e7532d4db2d4b4ddb64b50a5d0d9e45a973600"
      }
    },
    {
      "id": "1ax2__A1_P16404--1ax2__A2_P16404:apo",
      "system_id": "1ax2__A1_P16404--1ax2__A2_P16404",
      "kind": "apo",
      "unit_manifest_index_zero_based": 5,
      "prepared_record": {
        "id": "1ax2__A1_P16404--1ax2__A2_P16404",
        "kind": "apo",
        "receptor": "1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_R.pdb",
        "ligand": "1ax2__A1_P16404--1ax2__A2_P16404/inputs/apo/1ax2_apo_L.pdb"
      },
      "apo_receptor_source": "pdbs/3n35__A1_P16404.pdb",
      "apo_ligand_source": "pdbs/3n35__A1_P16404.pdb",
      "reference": "pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb",
      "historical_prepared_sha256": {
        "receptor": "a9be54841e5e92e301558c198a7188b6765ab34cf30cb5d939b46f99db103d35",
        "ligand": "8d3948ddc69f493dfeea785aefc09f3de7b191ab7f8250dc102f63dc1d35810e"
      }
    },
    {
      "id": "1dv1__A1_P24182--1dv1__B1_P24182:apo",
      "system_id": "1dv1__A1_P24182--1dv1__B1_P24182",
      "kind": "apo",
      "unit_manifest_index_zero_based": 9,
      "prepared_record": {
        "id": "1dv1__A1_P24182--1dv1__B1_P24182",
        "kind": "apo",
        "receptor": "1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_R.pdb",
        "ligand": "1dv1__A1_P24182--1dv1__B1_P24182/inputs/apo/1dv1_apo_L.pdb"
      },
      "apo_receptor_source": "pdbs/3g8c__A1_P24182.pdb",
      "apo_ligand_source": "pdbs/3g8d__A1_P24182.pdb",
      "reference": "pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb",
      "historical_prepared_sha256": {
        "receptor": "880a12d8a36e84fc8bea31cb4105284827ce1a985128413e4e8f70582fe52ea2",
        "ligand": "f9c72e23a1f2afe893c672da0412e82fa8345be23902d1d5cc7c17971193f623"
      }
    },
    {
      "id": "1nr5__A1_P07547--1nr5__A2_P07547:apo",
      "system_id": "1nr5__A1_P07547--1nr5__A2_P07547",
      "kind": "apo",
      "unit_manifest_index_zero_based": 15,
      "prepared_record": {
        "id": "1nr5__A1_P07547--1nr5__A2_P07547",
        "kind": "apo",
        "receptor": "1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_R.pdb",
        "ligand": "1nr5__A1_P07547--1nr5__A2_P07547/inputs/apo/1nr5_apo_L.pdb"
      },
      "apo_receptor_source": "pdbs/1sg6__A1_P07547.pdb",
      "apo_ligand_source": "pdbs/1sg6__A1_P07547.pdb",
      "reference": "pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb",
      "historical_prepared_sha256": {
        "receptor": "ec52d962eacf8e92518ead142a51f6feb18e8d74590ea7048fffc461f52cacf2",
        "ligand": "83ad5cf3938c63172fea2254e31e6fe05d5751d072323ff7ed3463d92af0d1a2"
      }
    }
  ]
}
```

Historical preparation implementation, exact excerpt from experiments/blind-02/m5/run2/agent/harness/setup.sh:709-735 (whole script SHA-256 743db59db27f71d647b9808f967bdea2ddc099b27f7c3e06f47a9f0361ea0182). This snippet assumes verified source downloads under data/2024-02, pandas installed, and manifest.data.cases set to the case records above. Preserve both logical prepared paths and short aliases.

```python
index=pd.read_parquet(root/'index.parquet')
cases=manifest['data']['cases']; selected=index[index.id.isin([c['system_id'] for c in cases])]
if len(selected)!=4: raise RuntimeError('Missing or duplicate selected index rows')
selected.to_parquet(pathlib.Path('data/custom_index.parquet'),index=False)
prepared={}
for case in cases:
    row=selected.loc[selected.id==case['system_id']].iloc[0]
    for role,chain in [('receptor','R'),('ligand','L')]:
        src=case['apo_'+role+'_source']
        if row['apo_'+chain+'_pdb']!=pathlib.Path(src).name:
            raise RuntimeError('Canonical apo identity differs from intake')
        dest=pathlib.Path('data')/case['prepared_record'][role]
        dest.parent.mkdir(parents=True,exist_ok=True)
        # Preserve every atom/residue and coordinate. Change chain field only.
        lines=[]
        for line in (root/src).read_text().splitlines(keepends=True):
            if line.startswith(('ATOM  ','HETATM','ANISOU','TER   ')):
                line=line[:21]+chain+line[22:]
            lines.append(line)
        dest.write_text(''.join(lines))
        prepared[str(dest)]=hashlib.sha256(dest.read_bytes()).hexdigest()
        # Short aliases keep published decoygen's filename buffers within bounds.
        short=pathlib.Path('data/inputs')/(case['system_id'][:4]+'_'+chain+'.pdb')
        short.parent.mkdir(exist_ok=True)
        short.write_bytes(dest.read_bytes())
pathlib.Path('data/prepared_sha256.json').write_text(json.dumps(prepared,indent=2)+'\n')
print(json.dumps(prepared,indent=2))
```

Historical evaluator mapping is exactly native_receptor_chain=['R'], native_ligand_chain=['L'], decoy_receptor_chain=['R'], decoy_ligand_chain=['L'], parallel_io=False. There is no independently curated historical residue-map file in the supplied run2 harness. BiotiteDockQ computes its correspondence from the pinned structures and implementation. Do not invent a missing curated map as an additional required source dataset. Capture the actual chain/residue correspondence and native identity before timing, under these same semantics. The native-self smoke still must pass before benchmarks. No native-derived remapping, case selection or ranking adjustment is permitted.

Historical evaluator call and validation, exact excerpt from experiments/blind-02/m5/run2/agent/harness/run_anchors.sh:50-56 (whole script SHA-256 ce1d681deeba11003145b1ca79a5a7cc9d402902123e878de311144e67d0d800):

```python
        df=BiotiteDockQ(native=pathlib.Path('data/2024-02')/case['reference'],decoys=poses,
                       native_receptor_chain=['R'],native_ligand_chain=['L'],
                       decoy_receptor_chain=['R'],decoy_ligand_chain=['L'],parallel_io=False).calculate()
        if len(df)!=50 or set(df.model_name)!={f'model_{i}' for i in range(1,51)}: raise RuntimeError('Missing scored pose')
        values=[float(x) for x in df.DockQ]
        if not all(math.isfinite(v) for v in values): raise RuntimeError('Invalid DockQ output')
        df.to_csv(job/'dockq.csv',index=False)
```

Historical CPU build and evaluator install commands follow. They are execution evidence, not an assertion that all current package artifacts or system libraries are available. The fresh harness must use the same immutable MEGADOCK and PINDER source pins above, discover actual stock paths, author its own CPU-only setup and record dependencies. No GPU build or GPU execution is added by these records. Compiler/FFTW/OS identities and actual binary hashes remain measured setup outputs; no historical complete OS lock or immutable image digest is asserted.

Exact excerpts, run2/agent/harness/setup.sh:61-63 and :81-95:

```bash
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 \
    CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr \
    FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
python3 -m venv --system-site-packages baseline-published/venv
vpy=baseline-published/venv/bin/python
python3 - <<'PY' > out/setup/constraints.txt
import torch
print('torch=='+torch.__version__)
print('numpy==1.26.4\nbiotite==1.2.0\nnetworkx==3.4.2\npandas==2.3.3\nscikit-learn==1.7.2')
PY
"$vpy" -m pip install 'setuptools>=65.4' 'setuptools_scm>=8' packaging wheel 'build==0.10.0'
"$vpy" -m pip install --no-build-isolation -c out/setup/constraints.txt ./baseline-published/pinder fire networkx
"$vpy" -m pip freeze > out/setup/pip-freeze.txt
"$vpy" - <<'PY'
import torch
from pinder.eval.dockq import BiotiteDockQ
print('Stock torch preserved:', torch.__version__)
PY
```

Historical constraints, exact bytes from run2/agent/results/reproduce/out/setup/constraints.txt (SHA-256 2d6a1578fd5a62e45971045da25b04cdc517f6a9ce87180bf6e6e73a840f33e1):

```text
torch==2.7.0
numpy==1.26.4
biotite==1.2.0
networkx==3.4.2
pandas==2.3.3
scikit-learn==1.7.2
```

Historical installed package inventory, exact bytes from run2/agent/results/reproduce/out/setup/pip-freeze.txt (SHA-256 b30ef7ab9dffc69be8bc135a9f2de6bbc01448529adea578a0c9e683351c14e8) follows. This is a freeze including inherited system packages, not a universally installable requirements lock. Its pinder file:// path names the old allocation and is not a download dependency: install PINDER from the fixed source commit. Use compatible version pins for the evaluator dependency stack; record actual versions and changes as already required above. Do not silently pool incompatible evaluator timings. Missing historical OS/wheel hashes do not become new inaccessible PDB data. If setup cannot meet the protocol, stop and retain failure.

```text
absl-py==2.1.0
aiohappyeyeballs==2.7.1
aiohttp==3.14.5
aiosignal==1.4.0
annotated-types==0.8.0
appdirs==1.4.4
argcomplete==1.8.1
astunparse==1.6.3
async-timeout==5.0.1
attrs==21.2.0
Automat==20.2.0
Babel==2.8.0
backcall==0.2.0
bcrypt==3.2.0
beautifulsoup4==4.10.0
beniget==0.4.1
biotite==1.2.0
biotraj==1.2.2
bleach==4.1.0
blinker==1.4
bottle==0.12.19
Brotli==1.0.9
build==0.10.0
certifi==2020.6.20
cffi==1.15.0
chardet==4.0.0
click==8.0.3
cloud-init==25.1.2
cloudpickle==3.1.2
colorama==0.4.4
command-not-found==0.3
commonmark==0.9.1
configobj==5.0.6
constantly==15.1.0
cryptography==3.4.8
ctop==1.0.0
cycler==0.11.0
dbus-python==1.2.18
decorator==4.4.2
defusedxml==0.7.1
distlib==0.3.4
distro==1.7.0
distro-info==1.1+ubuntu0.2
docker==5.0.3
entrypoints==0.4
fastjsonschema==2.22.3
fastpdb==1.3.3
filelock==3.6.0
fire==0.7.1
flake8==4.0.1
flatbuffers===1.12.1-git20200711.33e2d80-dfsg1-0.6
fonttools==4.29.1
frozenlist==1.8.0
fs==2.4.12
fsspec==2024.3.1
future==0.18.2
gast==0.5.2
Glances==3.2.4.2
google-pasta==0.2.0
grpcio==1.30.2
h5py==3.6.0
h5py.-debian-h5py-serial==3.6.0
html5lib==1.1
httplib2==0.20.2
hyperlink==21.0.0
icdiff==2.0.4
idna==3.3
importlib-metadata==4.6.4
incremental==21.3.0
influxdb==5.3.1
iotop==0.6
ipykernel==6.7.0
ipython==7.31.1
ipython_genutils==0.2.0
jax==0.6.0
jax-cuda12-pjrt==0.6.0
jax-cuda12-plugin==0.6.0
jaxlib==0.6.0
jedi==0.18.0
jeepney==0.7.1
Jinja2==3.0.3
joblib==1.6.0
jsonpatch==1.32
jsonpointer==2.0
jsonschema==3.2.0
jupyter-client==7.1.2
jupyter_core==5.9.1
kaptan==0.5.12
keras==3.10.0
keyring==23.5.0
kiwisolver==1.3.2
launchpadlib==1.10.16
lazr.restfulclient==0.14.4
lazr.uri==1.0.6
libtmux==0.10.1
livereload==2.6.3
lxml==4.8.0
lz4==3.1.3+dfsg
Markdown==3.3.6
MarkupSafe==2.0.1
matplotlib==3.5.1
matplotlib-inline==0.1.3
mccabe==0.6.1
mkdocs==1.1.2
ml-dtypes==0.5.1
more-itertools==8.10.0
mpmath==0.0.0
msgpack==1.0.3
multidict==7.1.0
namex==0.0.8
narwhals==2.28.0
nbformat==5.11.1
nest-asyncio==1.5.4
netifaces==0.11.0
networkx==3.4.2
numpy==1.26.4
nvidia-ml-py==12.555.43
oauthlib==3.2.0
olefile==0.46
opt-einsum==3.3.0
optree==0.15.0
packaging==26.3
pandas==2.3.3
parso==0.8.1
pexpect==4.8.0
pickleshare==0.7.5
Pillow==9.0.1
pinder @ file:///tmp/m5-7a8ba461-a7a3-4233-ac9f-650a4ddabd27/baseline-published/pinder
pipx==1.0.0
platformdirs==2.5.1
plotly==7.1.0
ply==3.11
prompt-toolkit==3.0.28
propcache==0.5.4
protobuf==4.21.12
psutil==5.9.0
ptyprocess==0.7.0
py==1.10.0
pyarrow==25.0.1
pyasn1==0.4.8
pyasn1-modules==0.2.1
pycodestyle==2.8.0
pycparser==2.21
pycryptodomex==3.11.0
pydantic==2.14.2
pydantic_core==2.50.2
pyflakes==2.4.0
Pygments==2.11.2
PyGObject==3.42.1
PyHamcrest==2.0.2
pyinotify==0.9.6
PyJWT==2.3.0
pyOpenSSL==21.0.0
pyparsing==2.4.7
pyproject_hooks==1.3.3
pyrsistent==0.18.1
pyserial==3.5
pysmi==0.3.2
pysnmp==4.4.12
pystache==0.6.0
python-apt==2.4.0+ubuntu4
python-dateutil==3.0.0
python-magic==0.4.24
pythran==0.10.0
pytz==2022.1
PyYAML==5.4.1
pyzmq==22.3.0
requests==2.25.1
rich==11.2.0
scikit-learn==1.7.2
scipy==1.15.3
SecretStorage==3.3.1
service-identity==18.1.0
setuptools-scm==10.3.4
six==1.16.0
sos==4.8.2
soupsieve==2.3.1
ssh-import-id==5.11
sympy==1.12
tabulate==0.10.0
tensorboard==2.19.0
tensorflow==2.19.0
termcolor==1.1.0
threadpoolctl==3.1.0
tmuxp==1.9.2
tomli==2.5.0
torch==2.7.0
torch-geometric==2.8.1
torchtyping==0.1.5
torchvision==0.22.0
tornado==6.1
tqdm==4.70.1
traitlets==5.16.1
triton==3.3.0
Twisted==22.1.0
typeguard==2.13.3
typing-inspection==0.4.4
typing_extensions==4.16.0
tzdata==2026.6
ufoLib2==0.13.1
ufw==0.36.1
unattended-upgrades==0.1
unicodedata2==14.0.0
urllib3==1.26.5
userpath==1.8.0
vcs-versioning==2.6.0
virtualenv==20.13.0+ds
wadllib==1.3.6
wcwidth==0.2.5
webencodings==0.5.1
websocket-client==1.2.3
Werkzeug==2.0.2
wrapt==1.13.3
xxhash==4.0.2
yarl==1.25.1
zipp==1.0.0
zope.interface==5.4.0
```

The new benchmark harness is to be authored by m5 reproduce as specified above; it is not claimed to be an independently published evaluator-timing benchmark. Published MEGADOCK baseline commands and pinned PINDER evaluation are unchanged. Reproduce's harness contract explicitly permits additional measurements under out/; empty anchors remain empty, not synthetic published anchors. Stop/lifecycle assurance remains the external wrapper's obligation, not evidence that a PDB source is unavailable. The run3 receipt shows only intake and downstream skips, so it did not test successful reproduce stopping. Verify the wrapper, watchdog, compatible tariff and termination path before allocation as required above; do not claim they are proven by this brief. No silent continuation if that assurance is absent.
