"use strict";
(() => {
 const deck=document.querySelector('.deck'); if(!deck) return;
 const slides=[...deck.querySelectorAll('.slide')], select=document.querySelector('#slide-select');
 const prev=document.querySelector('#prev'), next=document.querySelector('#next'), count=document.querySelector('#slide-count');
 document.querySelector('.deck-controls').hidden=false;
 let current=0;
 function show(index,focus=false){
  current=Math.max(0,Math.min(slides.length-1,index));
  slides.forEach((s,i)=>s.hidden=i!==current);
  const slide=slides[current]; select.value=slide.id;
  count.textContent=`${String(current+1).padStart(2,'0')} / ${String(slides.length).padStart(2,'0')}`;
  prev.disabled=current===0;next.disabled=current===slides.length-1;
  if(location.hash!==`#${slide.id}`) history.replaceState(null,'',`#${slide.id}`);
  if(focus) {slide.focus({preventScroll:true});scrollTo(0,0);}
 }
 const fromHash=()=>Math.max(0,slides.findIndex(s=>s.id===location.hash.slice(1)));
 prev.addEventListener('click',()=>show(current-1,true));next.addEventListener('click',()=>show(current+1,true));
 select.addEventListener('change',()=>show(slides.findIndex(s=>s.id===select.value),true));
 addEventListener('hashchange',()=>show(fromHash(),true));
 document.querySelector('.cover .start').addEventListener('click',e=>{e.preventDefault();show(1,true);});
 addEventListener('keydown',e=>{
  if(e.altKey||e.ctrlKey||e.metaKey||e.target.matches('input,select,textarea,button,summary')) return;
  const commands={ArrowRight:current+1,PageDown:current+1,ArrowLeft:current-1,PageUp:current-1,Home:0,End:slides.length-1};
  if(Object.hasOwn(commands,e.key)){e.preventDefault();show(commands[e.key],true);}
 });
 show(fromHash());
 const queue=document.querySelector('#queue'), gap=document.querySelector('#gap'), reuse=document.querySelector('#reuse');
 document.querySelector('.lab-controls').hidden=false;
 const update=()=>{
  const q=Number(queue.value), g=Number(gap.value), p=reuse.checked?150:400, d=7*g;
  for(const [id,value] of Object.entries({'queue-value':q,'gap-value':g,'ttft-value':q+p,'itl-value':g,'total-value':q+p+d})) document.getElementById(id).textContent=`${value} ms`;
  for(const [id,value] of Object.entries({'q-bar':q,'p-bar':p,'d-bar':d})) {const bar=document.getElementById(id);bar.style.flex=String(value);bar.hidden=value===0;}
  document.querySelector('#lab-description').textContent=`教學模型：${q}ms 排隊 + ${p}ms prefill，首 token 後還有 7 個 ${g}ms 間隔。`;
 };
 for(const input of [queue,gap,reuse]) input.addEventListener('input',update);
 update();
 const choices=document.querySelector('.choices'); choices.hidden=false;
 for(const button of choices.querySelectorAll('button')) button.addEventListener('click',()=>{
  choices.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
  document.querySelector('#quiz-feedback').textContent=button.dataset.answer==='ttft'?'對。這個症狀關係到第一個 token 的等待。':'再想一下：ITL 看的是首個輸出之後的間隔。';
 });
})();
