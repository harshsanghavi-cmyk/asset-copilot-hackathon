import copy
from datetime import date,timedelta
import pytest
from backend.chains.dates import normalize_relative_window
from backend.chains.service import CopilotService
from backend.memory import MemoryStore
from backend.memory.token_packing import fit_section
from test_api_and_provider import IndependentProvider,FixedModel

class CatalogProvider(IndependentProvider):
    def __init__(self):self.plans=[]
    def query(self,plan,context,authority=None):
        self.plans.append(copy.deepcopy(plan));r=super().query(plan,context,authority)
        if plan.get('collection')=='assets' and plan.get('metric')=='records':
            r['rows']=[{'asset_id':'WELL-0001','name':'First well'},{'asset_id':'WELL-0002','name':'Second well'}]
            r['total_rows']=2
        elif plan.get('collection')=='assets':
            for row in r['rows']:row['asset_id']=(plan.get('filters',{}).get('asset_ids') or ['UNSCOPED'])[0]
        return r

@pytest.mark.asyncio
async def test_failed_explicit_alias_retains_private_focus_for_dashboard(tmp_path):
    class Fails(FixedModel):
        async def generate(self,*a,**kw):raise RuntimeError('Injected planner failure')
    p=CatalogProvider();m=MemoryStore(tmp_path/'memory.sqlite',p.namespace);m.create_session('A','thread');m.create_session('B','other')
    s=CopilotService(p,m,Fails())
    assert s.asset_references('well1 well-1 WELL 0001',s.context('A'))==(['WELL-0001'],[],[])
    with pytest.raises(RuntimeError):await s.answer(user_id='A',session_id='thread',run_id='explicit',message='show the dashboard and trend of well1')
    assert m.focus('thread','A')['asset_ids']==['WELL-0001']
    assert m.focus('other','B')['asset_ids']==[] and m.head()==0
    s.model=FixedModel()
    a=await s.answer(user_id='A',session_id='thread',run_id='followup',message='i want a dasbhbaord')
    assert {row['asset_id'] for r in a['results'].values() for row in r['rows']}=={'WELL-0001'}
    assert all(q.get('filters',{}).get('asset_ids')==['WELL-0001'] for q in p.plans if q.get('metric')=='status')


def test_relative_weeks_use_calendar_reference_not_model_arithmetic():
    q=normalize_relative_window({'collection':'inspections','metric':'temperature_series','start':'2026-07-24'},'last13weeks','2026-10-16')
    assert q['start']==(date(2026,10,16)-timedelta(weeks=13)).isoformat()
    assert q['end']=='2026-10-16'

@pytest.mark.asyncio
async def test_measured_token_slot_uses_allowance_without_mutating_facts():
    value={'result_catalog':[],'results':[{'id':'r','rows':[{'protocol_id':str(i),'detail':'source fact '*70} for i in range(5)]}],'evidence':[]}
    original=copy.deepcopy(value)
    async def synthetic_counter(text,**kwargs):return {'count':(len(text.encode())+3)//4}
    fitted,info=await fit_section(value,2000,synthetic_counter,'evidence')
    assert len(str(fitted).encode())>2000 and info['count']<=2000
    assert len(fitted['results'][0]['rows'])==5 and value==original


def test_private_currency_and_sort_preserve_raw_values_and_other_user(tmp_path):
    p=CatalogProvider();m=MemoryStore(tmp_path/'memory.sqlite',p.namespace);s=CopilotService(p,m,FixedModel())
    result={'r':{'columns':[{'key':'asset_id'},{'key':'area_name'},{'key':'installation_cost_usd','label':'Cost','unit':'USD'}],'rows':[{'asset_id':'W2','area_name':'Z','installation_cost_usd':2500},{'asset_id':'W1','area_name':'A','installation_cost_usd':1234}]}}
    baseline=copy.deepcopy(result)
    preference={'long_term':{'private_capsule':[{'kind':'preference','statement':'Show costs in thousand dollars and sort by area and well ID.'}],'private_detail':[]}}
    s._private_presentation(result,preference)
    assert [r['asset_id'] for r in result['r']['rows']]==['W1','W2']
    assert result['r']['rows'][0]['installation_cost_usd']==1234
    assert result['r']['rows'][0]['installation_cost_usd_thousands']==1.234
    other=copy.deepcopy(baseline);s._private_presentation(other,{'long_term':{'private_capsule':[],'private_detail':[]}})
    assert other==baseline
