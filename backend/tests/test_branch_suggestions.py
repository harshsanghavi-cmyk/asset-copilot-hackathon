import asyncio
import json
import httpx
import pytest
from backend.app import create_app
from backend.chains.gemma import ModelReply
from backend.chains.service import CopilotService
from backend.memory import MemoryStore
from test_api_and_provider import IndependentProvider, FixedModel

@pytest.mark.asyncio
async def test_branch_and_separate_suggestions_are_scoped(tmp_path):
    class Model(FixedModel):
        def __init__(self): self.calls=[]
        async def generate(self,purpose,system,payload,**kwargs):
            self.calls.append((purpose,system,payload))
            if purpose=='suggestions':
                return ModelReply({'suggestions':['Which well should I inspect next?','Can you show its trend?','What work is still open?']},{},live=False)
            return await super().generate(purpose,system,payload,**kwargs)
    provider=IndependentProvider();memory=MemoryStore(tmp_path/'memory.sqlite',provider.namespace);model=Model()
    memory.create_session('A','parent');memory.begin('first','parent','A','Show WELL-X status')
    memory.finish('first','parent','A',{'answer_id':'first','thread_id':'parent','narrative':'Verified status [source:record].','results':{},'blocks':[],'evidence':{},'reference_date':'2026-10-16'})
    app=create_app(provider=provider,memory=memory,model=model,runtime_dir=tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as c:
        h={'X-User-Id':'A'}
        branch=await c.post('/api/sessions/parent/branches',headers=h,json={'message_id':'first:user','mode':'edit'})
        assert branch.status_code==201,branch.text
        b=branch.json();assert b['session']['id']!='parent' and b['messages']==[]
        assert b['source_message']['content']=='Show WELL-X status'
        assert (await c.post('/api/sessions/parent/branches',headers={'X-User-Id':'B'},json={'message_id':'first:user','mode':'edit'})).status_code==404
        assert model.calls==[]
        queued=await c.post('/api/answers/first/suggestions',headers=h,json={})
        assert queued.status_code==202
        await asyncio.sleep(.03)
        ready=(await c.get('/api/answers/first/suggestions',headers=h)).json()
        assert ready['status']=='ready' and len(ready['suggestions'])==3
        await c.post('/api/answers/first/suggestions',headers=h,json={})
        assert len(model.calls)==1
        purpose,system,payload=model.calls[0]
        assert purpose=='suggestions' and set(payload)=={'question','displayed_answer','visible_conversation'}
        assert 'source:record' not in json.dumps(payload)
        assert 'practical oil-field asset intelligence specialist' not in system
        assert (await c.get('/api/answers/first/suggestions',headers={'X-User-Id':'B'})).status_code==404
        assert (await c.post('/api/answers/first/suggestions',headers=h,json={'memory':'not allowed'})).status_code==400

@pytest.mark.asyncio
async def test_layout_reuses_exact_own_data_without_model(tmp_path):
    class NoModel:
        configured=True
        async def generate(self,*a,**kw):raise AssertionError('layout must not call model')
    p=IndependentProvider();m=MemoryStore(tmp_path/'memory.sqlite',p.namespace);m.create_session('A','layout')
    m.begin('data','layout','A','Show assets')
    source={'answer_id':'data','thread_id':'layout','user_id':'A','narrative':'Original answer','reference_date':'2026-10-16','results':{'r':{'rows':[{'asset_id':'W1'},{'asset_id':'W2'}]}},'evidence':{'e':{'id':'e'}},'blocks':[{'id':'old','type':'table','result_set_id':'r','evidence_ids':['e'],'encoding':{},'span':3}]}
    m.finish('data','layout','A',source)
    answer=await CopilotService(p,m,NoModel()).answer(user_id='A',session_id='layout',run_id='change',message='show me in a single row instead of single column')
    assert answer['results']==source['results'] and answer['evidence']==source['evidence']
    assert answer['layout']['mode']=='single_row' and answer['generation']['calls']==[]
    assert m.head()==0 and m.private_head('A')==0


def test_captured_bad_search_is_a_typed_record_query_not_empty_lexical_search():
    from backend.contracts import PlannerOutput
    p=PlannerOutput.model_validate({'queries':[],'evidence_searches':[{'description':'Look up inspections','query_params':{'collection':'inspections','metric':'records','filters':{'asset_id':'WELL-0001'}}}]})
    assert p.evidence_searches==[] and p.queries[0]['collection']=='inspections'
    with pytest.raises(ValueError):PlannerOutput.model_validate({'evidence_searches':[{'description':'no terms'}]})
