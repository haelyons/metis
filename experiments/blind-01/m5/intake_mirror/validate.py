"""Mechanical output checks; selected FroDock provenance remains unverified_mirror."""
from pathlib import Path
import csv
import hashlib
import json
import re

from finalize import FIRST, THIRD, HEADER

OUT = Path(__file__).resolve().parent
WORK = OUT.parent
brief = (WORK / 'BRIEF.md').read_bytes()
enriched = (OUT / 'BRIEF_run5.md').read_bytes()
section = enriched[len(brief):].decode()
checks = {}
checks['exact_brief_prefix'] = enriched[:len(brief)] == brief
checks['header_once'] = section.count(HEADER) == 1
checks['owner_quotes_verbatim'] = all(('> ' + s + '\n') in section for s in [FIRST, THIRD])
checks['no_local_paths_in_addendum'] = not any(s in section for s in ['/home/', '~/.cache/', 'intake_check_dl', 'file://', 'local_path'])
checks['no_licence_claim_in_addendum'] = not re.search(r'\b(?:licen[cs]e|permission|SPDX|Apache|CC0|CC-BY)\b', section, re.I)
checks['uncertainty_retained'] = ('identity with the original study distribution remains unverified' in section
                                 and 'does not establish identity with the original' in section)
rows = json.loads((OUT / 'refetch_results.json').read_text())
with (OUT / 'HASHES.tsv').open() as stream:
    table = list(csv.DictReader(stream, delimiter='\t'))
checks['exact_tsv_columns'] = list(table[0]) == ['input', 'url', 'local_path', 'bytes', 'sha256', 'refetch_sha256', 'match']
checks['all_3602_files_covered'] = (len(rows) == len(table) == 3602
                                  and {r['input'] for r in rows} == {r['input'] for r in table})
checks['all_streams_match'] = all(r['match'] and r['sha256'] == r['refetch_sha256'] and r['bytes'] == r['refetch_bytes']
    and r['http_status'] == 200 and r['curl_exit'] == 0 and r['stream_only'] and not r['login_used'] for r in rows)
checks['all_tsv_hashes_match'] = all(r['match'] == 'true' and re.fullmatch('[0-9a-f]{64}', r['sha256'])
                                   and r['sha256'] == r['refetch_sha256'] for r in table)
checks['all_files_in_brief'] = all(
    f'| `{r["input"]}` | {r["url"]} | `{r["provenance"]}` | {r["ended_utc"]} | {r["bytes"]} | `{r["sha256"]}` |' in section
    for r in rows)
checks['mirror_never_promoted'] = next(r for r in rows if r['input'] == 'frodock_distribution:unverified_mirror')['provenance'] == 'unverified_mirror'
git = json.loads((OUT / 'git_verification.json').read_text())
checks['git_commit_and_tree'] = git['ls_remote_contains_pin'] and git['tree_match'] and git['commit_match'] and git['official_tree'] in section
protected = json.loads((OUT / 'protected_before.json').read_text())
checks['protected_inputs_unchanged'] = all(hashlib.file_digest((WORK / p).open('rb'), 'sha256').hexdigest() == sha for p, sha in protected.items())
checks['cache_sizes_mtimes_unchanged'] = all(Path(r['local_path']).stat().st_size == r['bytes']
    and Path(r['local_path']).stat().st_mtime_ns == r['cache_mtime_ns'] for r in rows)
status = json.loads((OUT / 'status.json').read_text())
enums = {
    'prerequisite': ['data', 'licence_evidence', 'data_and_licence_evidence', 'other', 'none_found'],
    'cause': ['transient_unreachable', 'source_moved', 'gated_access', 'source_choice', 'materials_missing', 'other'],
    'materials_usable': [True, False],
    'alternative': ['none', 'official_new_location', 'archive_snapshot', 'author_deposit', 'verified_mirror', 'regenerated_official', 'unverified_mirror'],
    'hashes_recorded': [True, False],
    'refetch': ['match', 'mismatch', 'unreachable', 'not_done'],
    'run5_brief': ['addendum', 'original'],
    'owner_action': ['none', 'supply_materials', 'obtain_access', 'decide'],
}
checks['exact_status_schema'] = set(status) == set(enums) and all(
    type(status[k]) is bool if k in ['materials_usable', 'hashes_recorded'] else status[k] in enums[k] for k in enums)
checks['status_supported'] = status == dict(prerequisite='data', cause='source_moved', materials_usable=True,
    alternative='unverified_mirror', hashes_recorded=True, refetch='match', run5_brief='addendum', owner_action='none')
checks['published_md5_match'] = all(r['local_md5_base64'] == r['refetch_md5_base64'] == r['published_md5']
                                    for r in rows if 'published_md5' in r)
result = dict(provenance='unverified_mirror', checks=checks, all_passed=all(checks.values()), file_rows=len(rows),
              protected_files=len(protected), brief_original_bytes=len(brief),
              brief_original_sha256=hashlib.sha256(brief).hexdigest(),
              brief_run5_sha256=hashlib.sha256(enriched).hexdigest())
(OUT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
assert result['all_passed']
