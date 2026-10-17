"""Measured section admission. Source objects remain whole and canonical data stays durable."""
import copy
from .budget import estimate, serialized


def prune_once(value, kind):
    if kind == 'long_term':
        for key in ('shared_detail','private_detail','private_capsule'):
            if value.get(key): value[key].pop(); return True
    elif kind == 'short_term':
        if value.get('dialogue'): value['dialogue'].pop(0); return True
        if value.get('references'): value['references'].pop(); return True
        if value.get('summary'):
            words=value['summary'].split(); value['summary']=' '.join(words[:len(words)//2]); return True
    else:
        rows=[r for r in value.get('results',[]) if len(r.get('rows',[]))>1]
        long_rows=[r for r in rows if len(r['rows'])>6]
        if long_rows:
            row=max(long_rows,key=lambda r:len(r['rows']))
            row['rows'].pop()
            if row.get('row_indices'):row['row_indices'].pop()
            return True
        if value.get('evidence'): value['evidence'].pop(); return True
        if rows:
            row=max(rows,key=lambda r:len(r['rows']));row['rows'].pop()
            if row.get('row_indices'):row['row_indices'].pop()
            return True
        if value.get('results'): value['results'].pop(); return True
        if value.get('result_catalog'): value['result_catalog'].pop(); return True
        for key in ('warnings','save_receipts','summaries'):
            if value.get(key): value[key].pop(); return True
    return False


async def fit_section(value, cap, counter, kind, on_wait=None):
    value=copy.deepcopy(value);omitted=0
    if counter:
        for _ in range(3):
            try:
                measured=await counter(serialized(value),on_wait=on_wait)
                count=int(measured['count'])
            except Exception:
                break
            if count<=cap:
                return value,{'count':count,'cap':cap,'method':'google_sdk_countTokens','omitted_items':omitted}
            target=max(cap,int(estimate(value)*cap/count*.92))
            while estimate(value)>target and prune_once(value,kind):omitted+=1
    while estimate(value)>cap and prune_once(value,kind):omitted+=1
    if estimate(value)>cap:
        raise ValueError('Required context metadata cannot fit the content ceiling')
    return value,{'count':estimate(value),'cap':cap,'method':'conservative_utf8_upper_bound','omitted_items':omitted}
