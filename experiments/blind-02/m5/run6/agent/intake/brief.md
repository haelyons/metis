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


## Calibration request (science step s04)

This request specifies one bounded, timing-only runtime calibration: the seed's "small runtime calibration to define feasible budgets". It is not the seed's full experiment. Preserve the seed above. The operator selects --stop-after-reproduce. Do not continue to profile, seal, propose, implement or evaluate.

Scope and exclusions

- All three seed configurations are timed: cpu_standard, gpu_standard, gpu_dense, on exactly the four apo cases above, in the order 1aua, 1ax2, 1dv1, 1nr5.
- No native reference is read by run_command.sh or run_anchors.sh. No DockQ is computed. The evaluator is not imported during timing.
- No comparison between configurations is computed: no score, rank, transform, coordinate or DockQ difference between any two arms, and no agreement verdict. Seed order requires tolerances to be justified before comparative results are examined; this calibration must not produce comparative results. Raw outputs are preserved and hashed, not compared.
- No acceleration, affordability or quality verdict. Timing ratios are calibration inputs for budget definition only.

Purpose

Tree run 20261103-0124-tree has two retained candidates whose calibration phases both specify this screen: R1:physical:P1 ("timing-only screen: all 4 fixed cases, 1 warmup plus 3 repeats per arm, study native scoring disabled") and seed:idea:2 ("time all 3 configurations across all 4 cases without native DockQ"). The physical card then sets common per-case budget tiers from 2 x the maximum calibrated warm invocation time per arm, including an evaluator reserve. This calibration supplies those walls.

Prior measurements supplied by the scientific reader (historical evidence, not new anchors)

- Blind-02 m5 run4 (CPU standard, this box type, same pins): per-case maximum complete evaluator wall for 50 poses (fresh Python process, BiotiteDockQ, fixed R/L mapping), seconds: 1aua 1.9728683570000385, 1ax2 1.7721286510000027, 1dv1 2.5732721009999295, 1nr5 2.4245986219999622; maximum of 16 walls 2.5732721009999295. These are the evaluator reserves E for this calibration; do not remeasure them on GPU outputs.
- Run4 CPU-standard MEGADOCK printed Elapsed time, seconds: 1aua 9.14, 1ax2 7.14, 1dv1 11.98, 1nr5 11.86; docking plus reconstruction of all four cases 45.19964612500007 s.
- Run4 setup: MEGADOCK 9575280 CPU help (megadock -h) prints valid usage and exits 255. Accept exit 255 only together with valid usage text; any other non-zero status remains a failure. Apply the same rule to megadock-gpu -h.

Materials, pins and preparation

Identical to the s03 request that run4 executed: MEGADOCK source 9575280c875732553266e26adc607dd892b02616; PINDER source ebeb28a2f8411363cef722b7d293c978f7442672; release 2024-02. Verify source payload hashes from the addendum above; generate prepared inputs by changing only the chain field (column 22) to R or L on ATOM/HETATM/ANISOU/TER records, retaining all other bytes and lines; copy short aliases data/inputs/<prefix>_R.pdb and _L.pdb byte for byte. Verify all eight prepared hashes before docking; any mismatch stops the run:

```json
{
  "1aua": {"receptor": "162aad227fdbdb6a0600a5b6a4f5b461663ee7ce419798061ea0cd8ae9be6f35", "ligand": "f5158ee7030ce712cc5fb419d1e7532d4db2d4b4ddb64b50a5d0d9e45a973600"},
  "1ax2": {"receptor": "a9be54841e5e92e301558c198a7188b6765ab34cf30cb5d939b46f99db103d35", "ligand": "8d3948ddc69f493dfeea785aefc09f3de7b191ab7f8250dc102f63dc1d35810e"},
  "1dv1": {"receptor": "880a12d8a36e84fc8bea31cb4105284827ce1a985128413e4e8f70582fe52ea2", "ligand": "f9c72e23a1f2afe893c672da0412e82fa8345be23902d1d5cc7c17971193f623"},
  "1nr5": {"receptor": "ec52d962eacf8e92518ead142a51f6feb18e8d74590ea7048fffc461f52cacf2", "ligand": "83ad5cf3938c63172fea2254e31e6fe05d5751d072323ff7ed3463d92af0d1a2"}
}
```

These hashes were printed by blind-02 m5 run2's executed setup and reproduced by run4's setup check (prepared_hashes_valid true). Intake must not read earlier experiment folders; this brief carries them.

Build both binaries from the same MEGADOCK checkout. Historical run2 build commands (exact excerpt, run2 setup.sh:52-80), which built and ran both binaries on this box type:

```bash
# Matching SDK headers; these are build dependencies, never substituted kernels.
if [[ ! -d baseline-published/cuda-samples/.git ]]; then
    git clone --depth 1 --branch v12.8 https://github.com/NVIDIA/cuda-samples baseline-published/cuda-samples
fi
git -C baseline-published/cuda-samples describe --tags --exact-match
samples=$(pwd)/baseline-published/cuda-samples
ls -l "$samples/Common/helper_cuda.h"
# Make variables configure the published Makefile without changing source.
# sm_90 targets the probed H100; retain published -O3 and -use_fast_math.
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 \
    CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr \
    FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
make -C baseline-published/megadock -j 8 USE_GPU=1 USE_MPI=0 \
    CPPCOMPILER=/usr/bin/g++ SM_VERSIONS=sm_90 \
    "NVCC=$CUDA_NVCC -Xcompiler -fopenmp -arch=sm_90 -use_fast_math" \
    "INCLUDES=-Isrc -I$CUDA_INCLUDE -I$samples/Common" \
    FFTW_CFLAGS=-I/usr/include \
    "LIB=-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L$CUDA_LIB -Wl,-rpath,$CUDA_LIB -lcudart -lcufft"
for binary in megadock megadock-gpu decoygen; do
    test -x "baseline-published/megadock/$binary"
    ldd "baseline-published/megadock/$binary"
done
# Help exits 255 in this published release. Require its actual usage output.
for binary in megadock megadock-gpu; do
    rc=0
    OMP_NUM_THREADS=26 CUDA_VISIBLE_DEVICES=0 "baseline-published/megadock/$binary" -h > "out/setup/$binary-help.log" 2>&1 || rc=$?
    [[ "$rc" == 0 || "$rc" == 255 ]]
    grep -q 'Usage: megadock' "out/setup/$binary-help.log"
done
```

CUDA paths are discovered from the box (run4 found nvcc 12.8 at /usr/bin/nvcc, headers /usr/include, libraries /usr/lib/x86_64-linux-gnu). Record SHA-256 of megadock, megadock-gpu and decoygen, compiler/CUDA/driver versions, GPU name and UUID, host CPU/topology/affinity and RAM. Evaluator dependencies are not needed for timing; install them only if the preparation step needs pandas, and record versions.

Commands

Common environment for every invocation: OMP_NUM_THREADS=26, OMP_DYNAMIC=FALSE, OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1, NUMEXPR_NUM_THREADS=1, LC_ALL=C, LANG=C, CUDA_VISIBLE_DEVICES=0 (the CPU binary ignores the GPU). Shared settings: -N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3. Per arm:

    cpu_standard: baseline-published/megadock/megadock     -R data/inputs/<prefix>_R.pdb -L data/inputs/<prefix>_L.pdb -o <job>/docking.out <shared> -r 3600
    gpu_standard: baseline-published/megadock/megadock-gpu -R data/inputs/<prefix>_R.pdb -L data/inputs/<prefix>_L.pdb -o <job>/docking.out <shared> -r 3600
    gpu_dense:    baseline-published/megadock/megadock-gpu -R data/inputs/<prefix>_R.pdb -L data/inputs/<prefix>_L.pdb -o <job>/docking.out <shared> -D

Reconstruction for every job: for rank 1..50, baseline-published/megadock/decoygen <job>/ligand_<rank>.pdb data/inputs/<prefix>_L.pdb <job>/docking.out <rank>; model_<rank>.pdb = receptor records without END lines, then ligand records without END/ENDMDL lines, then one END line. Each job writes to its own directory out/timing/block_<b>/<arm>/<prefix>/; nothing is overwritten or reused between jobs.

Schedule, sealed now

Serial execution, one job at a time, no concurrent workload. Block 0 is an untallied warmup (recorded, excluded from the endpoint). Blocks 1-3 are retained. Then one diagnostic block D (excluded from timing endpoints). Orders were fixed by the scientific step, balanced so each arm appears early, middle and late across blocks; they are not drawn from a random generator:

- Block 0: cpu/1aua, gpu/1ax2, dense/1dv1, cpu/1nr5, gpu/1aua, dense/1ax2, cpu/1dv1, gpu/1nr5, dense/1aua, cpu/1ax2, gpu/1dv1, dense/1nr5
- Block 1: dense/1aua, cpu/1ax2, gpu/1dv1, dense/1nr5, cpu/1aua, gpu/1ax2, dense/1dv1, cpu/1nr5, gpu/1aua, dense/1ax2, cpu/1dv1, gpu/1nr5
- Block 2: gpu/1aua, dense/1ax2, cpu/1dv1, gpu/1nr5, dense/1aua, cpu/1ax2, gpu/1dv1, dense/1nr5, cpu/1aua, gpu/1ax2, dense/1dv1, cpu/1nr5
- Block 3: cpu/1nr5, dense/1dv1, gpu/1ax2, cpu/1aua, gpu/1nr5, dense/1ax2, cpu/1dv1, gpu/1aua, dense/1nr5, cpu/1ax2, gpu/1dv1, dense/1aua
- Block D: Block 1 order, with nvidia-smi sampling (timestamp, utilization.gpu, memory.used, at 1-second interval) running for the whole block, written to out/timing/gpu_telemetry.csv.

(cpu = cpu_standard, gpu = gpu_standard, dense = gpu_dense.)

Measurements per job (parent Python, time.monotonic):

- W, production wall (primary): from immediately before docking process creation to after all 50 model PDBs are written, closed and validated (validation below). Includes process start, CUDA initialisation, docking, output write, 50 decoygen calls and complex assembly.
- D, docking process wall: process creation to process exit.
- P, MEGADOCK printed "Elapsed time" seconds, parsed from the log.
- R, reconstruction wall: first decoygen start to last model written.
- Status: complete, failed (rc != 0), invalid_output or timeout. Per-job timeout 600 s with process-group kill; a timeout records lower_bound_s and status timeout, never a completed wall.

Validation per job (inside W): docking.out has 4 header lines plus 50 rows of 7 finite fields; header grid positive and voxel 1.2; printed rotation count 3600 for standard arms and 54000 for gpu_dense; printed thread count 26; printed GPU count 0 for cpu_standard and 1 for the GPU arms; 50 non-empty models whose ATOM/HETATM inventory equals receptor plus ligand inputs, with chains exactly R and L. Validation must not read native references or other arms' outputs.

Output: out/timing_calibration.json with protocol identity (this section's SHA-256), pins, binary hashes, host/GPU identity, setup checks, every job record {block, order_index, arm, case, status, W_s, D_s, P_s, R_s, lower_bound_s, docking_out_sha256}, the evaluator reserves E above copied verbatim and labelled historical, per case and arm the maximum and median of W over blocks 1-3, stage walls, and a scope statement "timing-only; no native access; no cross-arm comparison". Preserve all logs and docking.out files with hashes. Empty published anchors stay empty; write out/anchors_measured.json as {} as run4 did. Never invent anchors.

Quantities the scientific step will compute afterwards (stated now so they are sealed; the harness need not compute them)

For case c and arm a: M[c,a] = max over blocks 1-3 of W[c,a] + E[c]. Ratio rho[c] = M[c,gpu_dense] / max(M[c,cpu_standard], M[c,gpu_standard]). Physical-card tiers: tier1 = 0.75 x 2 x max(M_cpu, M_gpu), tier2 = 2 x max(M_cpu, M_gpu), tier3 = 2 x max(M_cpu, M_gpu, M_dense). Dense is calibrated as eligible at tier k for case c iff M[c,gpu_dense] <= tier_k.

Decision rule, fixed before execution

- All 48 primary jobs (blocks 0-3) complete and valid, pins and prepared hashes valid: the calibration is valid. Then for each case: rho <= 1.5, dense eligible at all three physical tiers; 1.5 < rho <= 2.0, dense eligible at tiers 2 and 3 only (tier1 dense recorded unavailable in any later study, never DockQ 0); rho > 2.0, dense eligible only at the dense-defined tier3, and "affordable within a CPU-standard-derived budget" is answered negatively for that case at this tariff. The physical candidate goes forward with these tiers in every valid outcome.
- For seed:idea:2: if, for every case, max W[c,gpu_dense] <= max W[c,cpu_standard] + 60 s, its primary affordability cap (CPU-standard envelope plus the fixed 60-second evaluator allowance) is non-discriminating, and seed:idea:2's affordability component is dropped unless rewritten in a new sealed plan with a measured allowance. Its acceleration component is kept for later agreement-gated testing only if, for every case, the median over blocks 1-3 of (W_cpu + E)/(W_gpu + E) is at least 1.05; otherwise the acceleration component is dropped as unpromising at workflow level (this is a calibration screen, not an acceleration verdict).
- Any job failed, invalid or timed out without a completed replacement: calibration incomplete; quantities for affected case/arm are unknown; no tier for that case. Do not rerun beyond the schedule; preserve every attempt. A timeout above 600 s on gpu_dense is itself a valid witness that dense exceeds tier2 for that case.

Budget, stop and lifecycle

Run4 used 1396 s of allocation from box start (02:29:59Z) to its last receipt (02:53:15Z), including intake, harness authoring, one repair, setup, a 121 s anchors receipt and freeze. This run adds a GPU build and about 60 timed jobs (historical docking-only: CPU standard 7.1-12.0 s, GPU standard 1.4-1.9 s, GPU dense 13.9-19.5 s per case, plus about 1.3 s reconstruction). Projection: about 1 allocated hour at historical USD 3.29/h = USD 3.29, plus USD 0.71 billing, tax and termination uncertainty = USD 4 all-in. Hard stop at 2 allocated hours or USD 10, whichever comes first; stop new scientific work at 75 allocated minutes and keep the rest for export and termination. Do not launch if the current compatible tariff projection exceeds USD 10. No paid persistent filesystem, no larger or replacement box. The general 6 h soft and 12 h hard ceilings remain upper limits, not this test's budget. Preserve partial results and overruns. The operator must verify the --stop-after-reproduce wrapper, watchdog and termination path before allocation, as for run4. If intake or harness cannot express this timing-only calibration with these boundaries, report the exact contract gap and stop before paid work. Do not fall through to the seed's full three-configuration scientific study.
