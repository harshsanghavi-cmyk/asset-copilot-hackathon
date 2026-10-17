#!/usr/bin/env python3
"""Package the actual completed serving run without regenerating any answers."""
import collections
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'experiments/06-evaluation/final-sessions/all11-final-accepted'
OUT = ROOT / 'submission/results/all11'
OUT.mkdir(parents=True, exist_ok=True)
manifest = json.loads((RUN / 'manifest.json').read_text())
assert manifest['status'] == 'finished' and len(manifest['turns']) == 21
parts = []
def add(text, style='body'):
    parts.append({'text': text, 'style': style})
add('Final run: all 11 scenarios / 21 saved replies / 14 sessions. '
    '10 replies completed generation; 11 delivered partial records. These are delivery outcomes, '
    'not a claim that 10 answers passed semantic QA. No request ended with a fatal error. '
    'Missing reservoir-pressure and measured-production data are reported as unavailable rather than invented.\n\n')
add('JSON below retains the saved narrative, component specifications, result columns and every returned row. '
    'Repeated source excerpts are omitted from this document; evidence handles remain. '
    'The accompanying ui-json-results.zip contains the complete, unchanged envelopes, including evidence and generation metadata.\n\n')
for q in range(1, 12):
    add(f'Question {q}\n', 'heading')
    for t in sorted((t for t in manifest['turns'] if t['scenario'] == q), key=lambda t:t['turn']):
        record = json.loads((RUN / t['file']).read_text())
        answer = record['answer']
        (OUT / t['file']).write_text(json.dumps({'question':record['question'], 'user':record['user'],
            'session_id':record['session_id'], 'status':record['status'], 'answer':answer}, ensure_ascii=False, indent=2)+'\n')
        add(f"{record['user']} · Turn {t['turn']} · {record['status']}\n{record['question']}\n")
        projection = {k:answer[k] for k in ('schema_version','answer_id','thread_id','user_id',
            'dataset_namespace','reference_date','narrative','blocks','results','warnings','generation') if k in answer}
        projection['evidence'] = {k:{key:v[key] for key in ('id','source_id','source_kind','title','path','url') if key in v}
                                  for k,v in answer.get('evidence',{}).items()}
        # One line per top-level value preserves valid JSON while keeping result rows compact.
        code = '{\n' + ',\n'.join('  '+json.dumps(k)+': '+json.dumps(v,ensure_ascii=False,separators=(',',':'))
                                  for k,v in projection.items()) + '\n}'
        add('```json\n'+code+'\n```\n\n', 'code')
(ROOT / 'submission/google-doc-results-parts.json').write_text(json.dumps(parts, ensure_ascii=False))
(ROOT / 'submission/ALL_11_RESULTS.md').write_text(''.join(p['text'] for p in parts))
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
with zipfile.ZipFile(ROOT / 'submission/ui-json-results.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.glob('*.json')): z.write(f, 'all11/'+f.name)
summary = {'run':manifest['run_tag'], 'scenarios':11, 'replies':21, 'sessions':14,
           'delivery':dict(collections.Counter(t['status'] for t in manifest['turns'])),
           'fatal_request_errors':sum(bool(t.get('error')) for t in manifest['turns']),
           'semantic_accuracy':'Not established for the complete final batch; partials remain visible.'}
(ROOT / 'submission/FINAL_RUN_STATUS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary)); print('Document result characters:', sum(len(p['text']) for p in parts))
