#!/usr/bin/env python3
"""Rebuild the provenance-preserving Wiki and teach from it."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
TOPICS={
 'stages':('W01','一次請求的階段',['metrics','kv']),
 'metrics':('W02','量測邊界與延遲指標',['stages','prefix']),
 'kv':('W03','KV cache 與區塊',['stages','prefix']),
 'prefix':('W04','共同前綴的重用',['kv','routing']),
 'routing':('W05','快取和負載的取捨',['prefix','metrics'])}

def load(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def write(name,value):
 path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value,encoding='utf-8')
def jsonout(name,value): write(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def require(condition,message):
 if not condition: raise ValueError(message)

def ingest():
 sources=load('sources/intake.json'); fetch=load('records/source-fetch.json')
 require(len(sources)>=5,'At least five distinct sources are required')
 require(len({s['url'] for s in sources})==len(sources),'Duplicate source URLs')
 require(len({s['id'] for s in sources})==len(sources),'Duplicate source IDs')
 require(len({r['final_url'] for r in fetch})==len(sources),'Sources redirected to duplicate documents')
 seen=set(); claims={}; overview=['# LLM 延遲 Wiki','',f'已 ingest {len(sources)} 篇第一手文件；公開內容為原創繁中整理。','', '## 概念頁','']
 for key,(id,title,_) in TOPICS.items(): overview.append(f'- [{id} {title}](topics/{key}.md)')
 overview+=['','## 原始資料','']
 for s in sources:
  url=urlparse(s['url']); require(url.scheme=='https' and url.netloc,'Invalid source URL')
  date.fromisoformat(s['checked'])
  receipt=next((r for r in fetch if r['id']==s['id'] and r['url']==s['url']),None)
  require(receipt and receipt['http_status']==200 and receipt['bytes']>500,'Source fetch missing: '+s['id'])
  require(s['scope'] and s['summary'] and s['facts'],'Incomplete source record')
  overview.append(f'- [{s["id"]} {s["title"]}](sources/{s["id"].lower()}.md)')
  body=[f'# {s["id"]} {s["title"]}','',f'[第一手原文]({s["url"]})',f'範圍：{s["scope"]}。核對：{s["checked"]}。','',s['summary'],'','## 整理的主張','']
  for c in s['facts']:
   require(c['id'] not in seen,'Duplicate evidence ID: '+c['id']);seen.add(c['id'])
   require(c['topic'] in TOPICS and all(c[k] for k in ['facet','text','limit','locator','keywords']),'Invalid evidence')
   claims[c['id']]={**c,'source':s['id']}
   body += [f'- [{c["id"]}](../topics/{c["topic"]}.md#{c["id"].lower()})：{c["text"]}（定位：{c["locator"]}）']
  write(f'wiki/sources/{s["id"].lower()}.md','\n'.join(body)+'\n')
 for key,(id,title,related) in TOPICS.items():
  body=[f'# {id} {title}','', '[回 Wiki](../README.md) · '+' · '.join(f'[{TOPICS[k][1]}]({k}.md)' for k in related),'']
  for c in claims.values():
   if c['topic']!=key: continue
   body += [f'## {c["id"].lower()}','',c['text'],'',f'**限制：** {c["limit"]}',f'**來源：** [{c["source"]}](../sources/{c["source"].lower()}.md)，{c["locator"]}。','']
  write(f'wiki/topics/{key}.md','\n'.join(body))
 write('wiki/README.md','\n'.join(overview)+'\n')
 jsonout('wiki/index.json',{'source_count':len(sources),'sources':{s['id']:{k:v for k,v in s.items() if k!='facts'} for s in sources},'topics':TOPICS,'claims':claims})
 jsonout('records/00-ingest.json',{'sources':len(sources),'topics':len(TOPICS),'evidence_units':len(claims),'source_ids':[s['id'] for s in sources],'wiki_index_sha256':hashlib.sha256((ROOT/'wiki/index.json').read_bytes()).hexdigest()})
 print(f'Ingested {len(sources)} documents into {len(TOPICS)} linked topics / {len(claims)} evidence units')

def ranked(index,terms):
 terms=set(t.lower() for t in terms)
 candidates=[(len(terms.intersection(c['keywords'])),c['id']) for c in index['claims'].values()]
 return [id for score,id in sorted(candidates,key=lambda x:(-x[0],x[1])) if score>0]

def missing(index,question,ids):
 actual={index['claims'][id]['facet'] for id in ids}
 return [facet for facet in question['requires'] if facet not in actual]

def baseline():
 index=load('wiki/index.json'); checks=[]; draft=[]
 for q in load('lesson/brief.json'):
  selected=ranked(index,q['terms'])[:3]
  draft.append({'question':q['id'],'outline':[{'id':id,'text':index['claims'][id]['text']} for id in selected]})
  gaps=missing(index,q,selected)
  checks.append({'question':q['id'],'terms':q['terms'],'initial_ids':selected,'initial_facets':[index['claims'][id]['facet'] for id in selected],'required':q['requires'],'missing':gaps,'status':'failed' if gaps else 'passed'})
 # Initial design audits only after assembling an outline. Never publish this outline as the lesson.
 jsonout('records/01-baseline-outline.json',draft)
 jsonout('records/01-baseline.json',{'method':'keyword overlap top 3; coverage checked after draft outline','checks':checks,'failed_questions':sum(bool(c['missing']) for c in checks)})
 for c in checks: print(c['question'],c['initial_ids'],'missing:',c['missing'])

def select():
 index=load('wiki/index.json'); checks=[]; packets={}
 for q in load('lesson/brief.json'):
  ranking=ranked(index,q['terms']); initial=ranking[:3]
  # Keep at most one verified claim for each requested concept. Other hits do not count.
  by_facet={}
  for id in initial:
   facet=index['claims'][id]['facet']
   if facet in q['requires']: by_facet.setdefault(facet,id)
  retries=[]
  for attempt in range(1,3):
   gaps=[f for f in q['requires'] if f not in by_facet]
   if not gaps: break
   returned={}
   for facet in gaps:
    # Same Wiki snapshot; narrow the query using the lesson requirement, not a guessed answer.
    eligible=[c['id'] for c in index['claims'].values() if c['facet']==facet]
    ordered=[id for id in ranking if id in eligible]+[id for id in sorted(eligible) if id not in ranking]
    if ordered: returned[facet]=ordered[0]
   by_facet.update(returned)
   retries.append({'round':attempt,'targeted_facets':gaps,'returned':returned})
   if not returned: break
  selected=[by_facet[f] for f in q['requires'] if f in by_facet]
  gaps=missing(index,q,selected)
  checks.append({'question':q['id'],'initial_ids':initial,'initial_missing':missing(index,q,initial),'retrieval_retries':retries,'approved_ids':selected,'remaining_missing':gaps,'passed':not gaps})
  packets[q['id']]=[index['claims'][id] for id in selected]
 record={'method':'coverage check immediately after Wiki lookup, targeted requery before drafting','questions':len(checks),'checks':checks,'questions_requeried':sum(bool(c['retrieval_retries']) for c in checks),'failed_questions':sum(not c['passed'] for c in checks),'wiki_sha256':hashlib.sha256((ROOT/'wiki/index.json').read_bytes()).hexdigest()}
 jsonout('records/02-early-gate.json',record)
 require(not record['failed_questions'],'Missing Wiki evidence; return to sources before drafting')
 jsonout('lesson/checked-evidence.json',{'wiki_sha256':record['wiki_sha256'],'questions':packets})
 print(f"Early coverage check: {record['questions']} questions, {record['questions_requeried']} targeted requeries, {record['failed_questions']} unresolved")

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['ingest','baseline','select']);args=parser.parse_args()
 {'ingest':ingest,'baseline':baseline,'select':select}[args.stage]()
