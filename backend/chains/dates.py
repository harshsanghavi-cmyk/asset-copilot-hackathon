"""Deterministic relative query windows, anchored to the supplied reference date."""
import calendar
from datetime import date,timedelta
import re


def normalize_relative_window(query,message,reference_date):
    match=re.search(r'\blast\s*(\d+)\s*(days?|weeks?|months?|years?)\b',message,re.I)
    if not match:return query
    count=int(match[1]);unit=match[2].casefold();end=date.fromisoformat(reference_date)
    if not 0<count<=10000:return query
    query=dict(query)
    if query.get('metric')=='status':
        for key in ('start','date_from'):query.pop(key,None)
        query['end']=reference_date
        return query
    if query.get('collection') not in {'inspections','maintenance','regulatory_events','context_notes'}:return query
    if unit.startswith('day'):start=end-timedelta(days=count)
    elif unit.startswith('week'):start=end-timedelta(weeks=count)
    else:
        months=count*(12 if unit.startswith('year') else 1)
        index=end.year*12+end.month-1-months;year,month=divmod(index,12);month+=1
        if year<1:return query
        start=date(year,month,min(end.day,calendar.monthrange(year,month)[1]))
    query.update(start=start.isoformat(),end=end.isoformat())
    for key in ('date_from','date_to','window'):query.pop(key,None)
    return query
