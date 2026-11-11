#!/usr/bin/env python3
"""Render static teaching slides, linked Wiki and run report from audited evidence."""
from collections import Counter
from hashlib import sha256
from html import escape
from pathlib import Path
import shutil
from pipeline import ROOT, load, write, jsonout, require

E=escape
def page(title,body,root='',css=''):
 return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="從 LLM Latency Wiki 學習推論延遲"><title>{E(title)} | LLM Latency Lab</title><link rel="stylesheet" href="{root}assets/style.css"><script src="{root}assets/deck.js" defer></script></head><body class="{css}"><a class="skip" href="#main">跳到內容</a><header class="top"><a class="brand" href="{root}index.html"><b>LLM</b> Latency Lab</a><nav aria-label="主要導覽"><a href="{root}slides/">簡報</a><a href="{root}wiki/">Wiki</a><a href="{root}workflow/">流程與紀錄</a></nav></header>{body}<footer class="site-foot"><span>INFRA FIELD NOTES / LEARNING LAB</span><a href="https://github.com/seankohjs/llm-latency-wiki">完整來源 ↗</a></footer></body></html>'''

def validate(index,packet,slides,digest):
 require(packet['wiki_sha256']==digest,'Evidence packet is stale; re-run Wiki selection')
 questions={q['id']:q for q in load('lesson/brief.json')}
 known=index['claims']; counts=Counter()
 require(set(packet['questions'])==set(questions),'Missing checked question')
 for key,claims in packet['questions'].items():
  require(all(known.get(c['id'])==c for c in claims),'Packet does not match Wiki: '+key)
  require(set(questions[key]['requires'])<={c['facet'] for c in claims},'Unchecked gap: '+key)
 available={c['id'] for group in packet['questions'].values() for c in group}
 require(len(slides)==9 and len({s['id'] for s in slides})==9,'Expected nine unique lesson slides')
 require([s['kind'] for s in slides]==['cover','timeline','metrics','evidence','cache','routing','lab','quiz','recap'],'Unexpected slide order')
 for slide in slides:
  require(len(slide['claims'])==len(set(slide['claims'])),'Repeated claim in slide')
  require(set(slide['claims'])<=available,'Unknown or unchecked evidence: '+slide['id'])
  if slide['kind']!='cover': require(slide['claims'],'Missing slide evidence: '+slide['id'])
  if q:=slide.get('question'):
   counts[q]+=1
   require(set(slide['claims'])=={c['id'] for c in packet['questions'][q]},'Slide dropped or replaced checked evidence: '+slide['id'])
 require(set(counts)==set(questions) and all(n==1 for n in counts.values()),'Every teaching question needs one main slide')
 used={known[id]['source'] for s in slides for id in s['claims']}
 require(used==set(index['sources']),'Ingested source not reflected in lesson')
 return {'slides':len(slides),'source_count_in_lesson':len(used),'unique_claims':len({id for s in slides for id in s['claims']}),'verified_question_count':len(questions),'wiki_sha256':digest,'source_ids':sorted(used)}

def lab():
 return '''<div class="lab"><div class="lab-controls" hidden><label for="queue">排隊 <output id="queue-value">200 ms</output></label><input id="queue" type="range" min="0" max="1000" step="20" value="200"><label for="gap">後續 token 間隔 <output id="gap-value">30 ms</output></label><input id="gap" type="range" min="10" max="100" step="5" value="30"><label class="toggle"><input id="reuse" type="checkbox"> 教學情境：共同前綴命中</label></div><div class="lab-results"><div><small>TTFT</small><strong id="ttft-value">600 ms</strong></div><div><small>ITL</small><strong id="itl-value">30 ms</strong></div><div><small>完成時間</small><strong id="total-value">810 ms</strong></div></div><div class="timebar" aria-hidden="true"><span id="q-bar" style="flex:200"></span><span id="p-bar" style="flex:400"></span><span id="d-bar" style="flex:210"></span></div><div class="legend"><span>排隊</span><span>Prefill</span><span>後續生成</span></div><p id="lab-description" role="status">教學模型：200ms 排隊 + 400ms prefill，首 token 後還有 7 個間隔。</p><p class="fine"><b>教學假設，非實測。</b> 輸出固定 8 個 token，假設每次輸出一個 token。命中只把示意 prefill 從 400ms 調為 150ms。完成時間 = TTFT + 7 × ITL；省略網路與其他開銷。</p></div>'''

def claim_rows(ids,known,labels=None):
 rows=[]
 for i,id in enumerate(ids):
  c=known[id]
  rows.append(f'<div class="claim-row"><span class="row-label">{E(labels[i] if labels else f"{i+1:02}")}</span><div><p>{E(c["text"])}</p><small>{E(c["limit"])}</small></div></div>')
 return '<div class="claim-list">'+''.join(rows)+'</div>'

def make_slides(slides,known):
 result=[]
 for i,s in enumerate(slides,1):
  kind=s['kind'];ids=s['claims']; refs=''.join(f'<a data-evidence="{id}" href="../wiki/#{id}">{id} · {known[id]["source"]}</a>' for id in ids)
  if kind=='cover':
   inner='<div class="cover-rule"></div><p class="cover-note">給第一次想理解 LLM 推論的人。<br>一份從 Wiki 的來源證據產生的教學簡報。</p><a class="start" href="#stages">開始閱讀 <span aria-hidden="true">→</span></a>'
  elif kind=='timeline':
   inner='<div class="phase-track"><span>Queue</span><span>Prefill</span><span>Decode</span></div>'+claim_rows(ids,known,['排隊','處理輸入','接續生成'])
  elif kind=='metrics': inner=claim_rows(ids,known,['TTFT','ITL','完成時間'])
  elif kind=='evidence': inner=claim_rows(ids,known,['保留狀態','分塊管理','比對條件'])
  elif kind=='cache':
   inner='<div class="prefix-rows" aria-label="兩個請求共享手冊開頭，問題不同"><div><b>請求 A</b><span>手冊開頭</span><span>共同內容</span><em>問題 A</em></div><div><b>請求 B</b><span>手冊開頭</span><span>共同內容</span><em>問題 B</em></div></div>'+claim_rows(ids,known,['可重用','仍需生成','何時幫助小'])
  elif kind=='routing':
   inner='<div class="route-compare"><div><small>WORKER A</small><strong>有前綴，有排隊</strong></div><div><small>WORKER B</small><strong>沒前綴，較空閒</strong></div></div>'+claim_rows(ids,known,['重用','負載'])
  elif kind=='lab': inner=lab()
  elif kind=='quiz':
   inner=f'''<div class="quiz"><div class="choices" hidden><button data-answer="ttft" aria-pressed="false">A　TTFT</button><button data-answer="itl" aria-pressed="false">B　ITL</button></div><p id="quiz-feedback" role="status">選一個答案，看看理由。</p><details><summary>看原始定義與解答</summary><p><b>答案：TTFT。</b> {E(known['C04']['text'])}</p><p>{E(known['C05']['text'])}</p></details></div>'''
  else:
   inner=claim_rows(ids,known,['開始等待','輸出節奏','快取效益'])+'<div class="reading-links"><a href="../wiki/">閱讀 Wiki 來源 ↗</a><a href="../workflow/">查看生成流程與實測 ↗</a></div>'
  foot=f'<div class="slide-refs"><span>Wiki 依據</span>{refs}</div>' if refs else ''
  result.append(f'<section class="slide {kind}" id="{s["id"]}" tabindex="-1" aria-labelledby="title-{i}"><p class="eyebrow">{i:02} / {E(s["label"])}</p><h{1 if i==1 else 2} id="title-{i}">{E(s["title"])}</h{1 if i==1 else 2}><p class="lead">{E(s["lead"])}</p>{inner}{foot}</section>')
 options=''.join(f'<option value="{s["id"]}">{i:02}　{E(s["title"])}</option>' for i,s in enumerate(slides,1))
 return '<main id="main" class="deck">'+''.join(result)+f'''<nav class="deck-controls" aria-label="簡報控制" hidden><button id="prev">← 上一頁</button><label><span class="sr-only">跳到投影片</span><select id="slide-select">{options}</select></label><output id="slide-count" aria-live="polite">01 / 09</output><button id="next">下一頁 →</button></nav><p class="keys">可用 ← → 或選單換頁</p></main>'''

def wiki_page(index):
 topics=index['topics']; known=index['claims']; sources=index['sources']
 links=''.join(f'<a href="#{k}">{v[0]} {E(v[1])}</a>' for k,v in topics.items())
 content=[]
 for k,(id,title,related) in topics.items():
  units=[]
  for c in known.values():
   if c['topic']!=k:continue
   units.append(f'<article class="unit" id="{c["id"]}"><p class="eyebrow">{c["id"]} · {E(c["facet"])}</p><p class="fact">{E(c["text"])}</p><p class="fine">{E(c["limit"])}</p><a href="#{c["source"]}">{c["source"]} · {E(c["locator"])} ↘</a></article>')
  cross='　'.join(f'<a href="#{r}">{E(topics[r][1])} ↗</a>' for r in related)
  content.append(f'<section class="wiki-topic" id="{k}"><p class="eyebrow">{id}</p><h2>{E(title)}</h2>{"".join(units)}<p class="cross">相關概念：{cross}</p></section>')
 receipts=''.join(f'<article class="source" id="{id}"><p class="eyebrow">{id} / 第一手資料</p><h3>{E(s["title"])}</h3><p>{E(s["summary"])}</p><p class="fine">{E(s["scope"])} · 核對 {s["checked"]}</p><a href="{E(s["url"],quote=True)}" target="_blank" rel="noopener noreferrer">原始文件 ↗</a></article>' for id,s in sources.items())
 return f'''<main id="main" class="reader"><header class="reader-head"><p class="eyebrow">KNOWLEDGE BASE</p><h1>LLM 延遲 Wiki</h1><p>6 篇第一手資料整理成 5 個互相連結的概念頁與 14 個可引用的主張。先看概念，再沿 C 編號找到原文位置與適用範圍。</p><div class="reading-links"><a href="../slides/">教學簡報 ↗</a><a href="https://github.com/seankohjs/llm-latency-wiki/tree/codex/llm-latency-wiki/wiki">Markdown Wiki ↗</a></div></header><nav class="wiki-toc" aria-label="Wiki 概念索引">{links}<a href="#sources">原始資料</a></nav>{''.join(content)}<section id="sources"><h2>六份原始資料</h2>{receipts}</section></main>'''

def workflow_page(index):
 before=load('records/01-baseline.json');after=load('records/02-early-gate.json')
 qs={q['id']:q for q in load('lesson/brief.json')}
 rows=[]
 for first,last in zip(before['checks'],after['checks']):
  rows.append(f'<tr><th scope="row">{E(qs[first["question"]]["title"])}</th><td>{E(", ".join(first["initial_ids"]))}</td><td>{E(", ".join(first["missing"]) or "無")}</td><td>{E(", ".join(last["approved_ids"]))}</td></tr>')
 return f'''<main id="main" class="reader"><header class="reader-head"><p class="eyebrow">WORKFLOW & ACTUAL RUN</p><h1>從 Wiki 到簡報</h1><p>2026-11-11：先討論初學者需要的範圍，再 ingest、查詢、查核並生成。下方保留基線發現的缺漏與修改後的結果。</p></header><section><h2>流程圖</h2><ol class="graph"><li>取得並核對原文</li><li>Ingest，建立 Wiki</li><li>依教學問題查詢</li><li class="gate">立即檢查概念覆蓋</li><li>編排並產生 HTML</li><li>檢查主張、來源與版面</li></ol><p class="loop"><b>查詢迴圈：</b>缺少必備概念時，回到 Wiki 依缺少的分類重查，每題最多兩輪，沒有新結果便停止。還是不足，就回來源補資料，暫不產生該份簡報。</p><p class="loop"><b>產出檢查：</b>完成後確認目前 Wiki 版本、主張 ID、所有來源與連結。若失敗，修正資料或編排再重建。每份原文各自核對，每個教學問題各自查詢。</p></section><section><h2>一次實際執行</h2><div class="run-stats"><div><strong>{index['source_count']}</strong><span>份來源已 ingest</span></div><div><strong>{before['failed_questions']} / {len(before['checks'])}</strong><span>基線問題有證據缺漏</span></div><div><strong>{after['failed_questions']} / {after['questions']}</strong><span>提早檢查後仍缺漏</span></div></div><div class="table-scroll"><table><thead><tr><th>教學問題</th><th>原本前三筆</th><th>草稿發現缺少</th><th>重查／篩選後採用</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div><p>修正後實際有 {after['questions_requeried']} 題觸發重查；五題都通過才進入編排。HTML 使用 Wiki 的主張文字和錨點，不把缺少的概念交給生成器猜測。</p></section><section><h2>反思：查到了，卻沒有查齊</h2><p>這次最常出問題的是「查詢 Wiki」節點。只看關鍵字重疊，APC 的 C10 會擠掉完成時間 C06；前綴問題也會抓到一般 prefill 說明，漏了效益受限的 C11。這是實際查詢的概念缺漏，不是發現兩句假事實。</p><p>我把原本「排完草稿才查覆蓋」移到「查到 Wiki 證據後立即檢查」。加入依缺少概念重查的分支，先核對是否具備應教的內容，再產生投影片，減少帶著缺口進入寫作。最終的來源、語意與版面檢查仍保留。</p><p class="fine">結果只代表本次 5 題與固定 Wiki。規則能核對概念標籤、ID 與版本，不能保證所有摘要都正確；AI 仍要閱讀原文核對語意。互動中的時間數字是教學假設。</p><div class="reading-links"><a href="https://github.com/seankohjs/llm-latency-wiki/tree/codex/llm-latency-wiki/records">實際執行紀錄 ↗</a><a href="../slides/">閱讀簡報 ↗</a></div></section></main>'''

def main():
 index=load('wiki/index.json'); packet=load('lesson/checked-evidence.json'); slides=load('lesson/slides.json')
 digest=sha256((ROOT/'wiki/index.json').read_bytes()).hexdigest()
 report=validate(index,packet,slides,digest)
 lead='''<main id="main" class="landing"><p class="eyebrow">LLM LATENCY LAB</p><h1>LLM 為什麼回得慢？</h1><p>用一份可追溯的 Wiki，理解排隊、輸入處理與輸出節奏。</p><a class="start" href="slides/">播放教學簡報 →</a><div class="landing-index"><a href="wiki/"><small>01 / 知識庫</small><strong>閱讀 LLM Wiki</strong><span>六份來源、五個概念頁與主張索引</span></a><a href="workflow/"><small>02 / 實際執行</small><strong>查看流程與反思</strong><span>一次基線查詢、修正與重跑</span></a></div></main>'''
 outputs={'index.html':page('LLM 推論延遲',lead),'slides/index.html':page('教學簡報',make_slides(slides,index['claims']),'../','deck-page'),'wiki/index.html':page('LLM 延遲 Wiki',wiki_page(index),'../'),'workflow/index.html':page('流程與實測',workflow_page(index),'../')}
 for name,html in outputs.items(): write('docs/'+name,html+'\n')
 shutil.copytree(ROOT/'assets',ROOT/'docs/assets',dirs_exist_ok=True)
 write('docs/.nojekyll','')
 report['slide_to_wiki']=[{'slide':s['id'],'claims':s['claims'],'sources':sorted({index['claims'][id]['source'] for id in s['claims']})} for s in slides]
 jsonout('records/04-render.json',report)
 print(f"Rendered {report['slides']} slides / {report['unique_claims']} checked evidence units / {report['source_count_in_lesson']} cited documents")

if __name__=='__main__': main()
