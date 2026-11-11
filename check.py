#!/usr/bin/env python3
"""Verify the actual generated site and test evidence gates with labelled fixtures."""
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
from pipeline import ROOT,load,jsonout,require
from render import validate

class Page(HTMLParser):
 def __init__(self,text):
  super().__init__(); self.ids=set();self.links=[];self.evidence=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if id:=attrs.get('id'):
   require(id not in self.ids,'Duplicate HTML ID '+id);self.ids.add(id)
  for field in ('href','src'):
   if attrs.get(field): self.links.append(attrs[field])
  if attrs.get('data-evidence'): self.evidence.append((attrs['data-evidence'],attrs.get('href')))

def main():
 dist=(ROOT/'docs').resolve(); pages={p.resolve():Page(p.read_text()) for p in dist.rglob('*.html')}
 require(len(pages)==4,'Expected four public routes')
 for path,page in pages.items():
  for link in page.links:
   url=urlsplit(link)
   if url.scheme=='https': continue
   require(not url.scheme and not url.netloc,'Unexpected URL: '+link)
   target=(path.parent/unquote(url.path)).resolve() if url.path else path
   if target.is_dir(): target=target/'index.html'
   require(target.is_relative_to(dist) and target.is_file(),f'Broken local link {path.name} -> {link}')
   if url.fragment: require(target in pages and unquote(url.fragment) in pages[target].ids,'Broken anchor: '+link)
 index=load('wiki/index.json');packet=load('lesson/checked-evidence.json');slides=load('lesson/slides.json')
 digest=sha256((ROOT/'wiki/index.json').read_bytes()).hexdigest()
 verified=validate(index,packet,slides,digest)
 deck=pages[dist/'slides/index.html']
 require(set(id for id,_ in deck.evidence)==set(index['claims']),'Missing Wiki reference in rendered deck')
 require(all(link=='../wiki/#'+id for id,link in deck.evidence),'Incorrect rendered reference')
 require(all(s['id'] in deck.ids for s in slides),'Missing rendered slide')
 fixtures=[]
 def reject(name,mutate):
  p=deepcopy(packet);s=deepcopy(slides);mutate(p,s)
  try: validate(index,p,s,digest)
  except ValueError: fixtures.append(name)
  else: raise AssertionError('Expected rejection: '+name)
 reject('synthetic stale Wiki hash',lambda p,s:p.update(wiki_sha256='obsolete'))
 reject('synthetic nonexistent citation',lambda p,s:s[1]['claims'].append('C99'))
 reject('synthetic dropped completion definition',lambda p,s:s[2]['claims'].remove('C06'))
 reject('synthetic modified evidence text',lambda p,s:p['questions']['metrics'][0].update(text='fixture only'))
 jsonout('records/05-check.json',{'html_routes':len(pages),'links_and_anchors':'passed','slide_mapping':verified,'synthetic_negative_cases_rejected':fixtures,'note':'The four intentional fixture cases are not observed baseline errors.'})
 print(f"Checked {len(pages)} HTML routes, all local anchors, {verified['slides']} slides, and {len(fixtures)} labelled negative fixtures")

if __name__=='__main__': main()
