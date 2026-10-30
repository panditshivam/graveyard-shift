const $=id=>document.getElementById(id);
let catalog, selected, busy=false, audio, sound=false, timer, reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const text=(tag,value,cls)=>{const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;return el;};
async function api(url, data){const r=await fetch(url,data?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}:{});const value=await r.json();if(!r.ok)throw Error(value.error||'The server could not complete this request.');return value;}
function tone(kind='open'){
  if(!sound||!audio||document.hidden)return;
  const notes=kind==='win'?[261.63,329.63,392,523.25]:kind==='fail'?[146.83,138.59]:[220,329.63,440];
  notes.forEach((f,i)=>{let o=audio.createOscillator(),g=audio.createGain();o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(0,audio.currentTime+i*.12);g.gain.linearRampToValueAtTime(.055,audio.currentTime+i*.12+.02);g.gain.exponentialRampToValueAtTime(.001,audio.currentTime+i*.12+1.2);o.connect(g).connect(audio.destination);o.start(audio.currentTime+i*.12);o.stop(audio.currentTime+i*.12+1.25);});
}
$('sound').onclick=async()=>{if(!audio)audio=new AudioContext();await audio.resume();sound=!sound;$('sound').textContent=sound?'Sound on':'Sound off';$('sound').setAttribute('aria-pressed',String(sound));tone();};
$('motion').onclick=()=>{document.body.classList.toggle('paused');$('motion').setAttribute('aria-pressed',String(document.body.classList.contains('paused')));$('motion').textContent=document.body.classList.contains('paused')?'Resume motion':'Pause motion';};
document.addEventListener('visibilitychange',()=>{if(document.hidden){sound=false;$('sound').textContent='Sound off';$('sound').setAttribute('aria-pressed','false');audio?.suspend();speechSynthesis?.cancel();}});
function status(s){$('status').textContent=s;}
function setBusy(value){busy=value;document.body.classList.toggle('busy',value);for(const id of ['mine','ask','challenge','ritual'])$(id).disabled=value;}
async function job(action,extra={}){
  if(busy)return null;setBusy(true);let seen=0;const start=Date.now();$('elapsed').textContent='';
  timer=setInterval(()=>$('elapsed').textContent=`${Math.floor((Date.now()-start)/1000)}s elapsed`,1000);
  status(action==='ask'?'The ghost is thinking. Qwen is loading or generating on CPU…':action==='ritual'?'Running the real regression tests…':'Reading the repository…');
  try{
    const {id}=await api('/api/jobs',{action,...extra});
    for(let polls=0;polls<150;polls++){
      const state=await api(`/api/jobs/${id}`);
      for(const e of state.events.slice(seen))$('events').append(text('li',`${e.elapsed}s · ${e.text}`));seen=state.events.length;
      if(state.status==='failed')throw Error(state.error);
      if(state.status==='completed'){status(action==='ask'?'The answer is here. Check its evidence.':action==='ritual'?'The tests have spoken. Read both results.':'The record is ready.');$('elapsed').textContent=`${state.elapsed}s server run`;return state.result;}
      await new Promise(resolve=>setTimeout(resolve,700));
    }throw Error('The response is taking too long. A job may still be running; wait before trying again.');
  }catch(e){status(e.message);tone('fail');return null;}finally{clearInterval(timer);setBusy(false);}
}
function renderGraves(){
  $('graves').replaceChildren();$('commit-count').textContent=`${catalog.commits} commits inspected`;
  for(const g of catalog.ghosts){const b=text('button','',`grave${g.id===selected?.id?' selected':''}`);b.append(text('span','DISAPPEARED FROM ITS OLD NAME','name'),text('strong',g.name),text('small',g.disappearance.slice(0,8)),text('small','Open this grave ↗'));b.onclick=()=>openGhost(g.id);b.dataset.ghost=g.id;$('graves').append(b);}
}
async function openGhost(id){
  if(busy)return;try{selected=await api(`/api/ghost/${id}`);renderGraves();$('chamber').hidden=false;$('ghost-name').textContent=selected.name;$('lineage').textContent='Disappearance observed · explanation pending';$('welcome').textContent=selected.name==='legacy_retry'?'“I remember getting one more chance.”':'“Are you sure you found the right grave?”';$('question').value='What changed when you disappeared?';$('answer-box').hidden=true;$('challenge-result').replaceChildren();$('test-stage').replaceChildren(text('p','The tests haven’t spoken yet.','awaiting'));$('ritual-section').hidden=selected.name!=='legacy_retry';$('evidence').replaceChildren();
    for(const e of selected.evidence){let box=text('div','','evidence-card');box.append(text('h3',`${e.id} / ${e.fact}`));let d=document.createElement('details');d.append(text('summary','Inspect exact source ↗'),text('pre',e.quote));box.append(d,text('p',`${e.revision.slice(0,12)} · ${e.path}${e.start?`:${e.start}–${e.end}`:' · deletion diff'}`,'evidence-meta'));let link=text('a','Open immutable evidence ↗');link.href=`/evidence/${id}/${e.id}`;link.target='_blank';link.rel='noopener';box.append(link);$('evidence').append(box);}
    tone();$('chamber').scrollIntoView({behavior:reduced?'instant':'smooth',block:'start'});
  }catch(e){status(e.message);}
}
$('mine').onclick=async()=>{let result=await job('mine');if(result){catalog=result;renderGraves();tone();}};
for(const button of document.querySelectorAll('[data-question]'))button.onclick=()=>$('question').value=button.dataset.question;
$('question-form').onsubmit=async e=>{e.preventDefault();if(!selected)return;const result=await job('ask',{ghost:selected.id,question:$('question').value});if(!result)return;
  $('answer-box').hidden=false;$('answer').textContent=result.citation_ids_valid?result.text:`Citation check failed. The model returned: ${result.text}`;$('citation-links').replaceChildren();for(const ref of result.citations.filter(x=>selected.evidence.some(e=>e.id===x))){let a=text('a',ref+' ↗');a.href=`/evidence/${selected.id}/${ref}`;a.target='_blank';a.rel='noopener';$('citation-links').append(a);}
  $('model-meta').textContent=`${result.seconds}s · ${result.output_tokens} generated tokens · ${result.citation_ids_valid?'Citation IDs exist; support still needs inspection.':'Do not treat this answer as grounded.'}`;
  let localVoice=speechSynthesis?.getVoices().find(v=>v.localService&&v.lang.startsWith('en'));$('speak').hidden=!localVoice;$('speak').onclick=()=>{if(!localVoice)return;let u=new SpeechSynthesisUtterance(result.text);u.voice=localVoice;u.rate=.86;u.pitch=.75;speechSynthesis.cancel();speechSynthesis.speak(u);};tone();};
$('challenge').onclick=async()=>{if(!selected)return;let result=await job('challenge',{ghost:selected.id});if(!result)return;let message=result.verified_body_match?`Not dead. ${selected.name} has an exact normalized body match in ${result.descendant.name}. This supports a rename candidate; the grave becomes a bridge.`:'The old symbol is absent and no exact body match was found. Removal is observed; the author’s intent is not established.';$('challenge-result').textContent=message;$('lineage').textContent=result.verified_body_match?'RENAMED / EXACT BODY MATCH':'REMOVED / NO EXACT BODY MATCH';if(result.verified_body_match)document.querySelector(`[data-ghost="${selected.id}"]`).classList.add('bridge');tone(result.verified_body_match?'win':'open');};
$('ritual').onclick=async()=>{let result=await job('ritual',{ghost:selected.id});if(!result)return;$('test-stage').replaceChildren();for(const run of result.results){let box=text('div','','test-result');box.append(text('h3',`${run.stage==='before'?'THE REWRITE':'THE RECOVERED FIX'} / EXIT ${run.returncode}`,run.returncode?'fail':'pass'),text('pre',run.output));$('test-stage').append(box);}if(result.verified){$('test-stage').append(text('p','The ghost remembered the missing attempt. All three tests now pass.','victory'));document.body.classList.add('restored');tone('win');}else{$('test-stage').append(text('p','The expected result was not verified. Inspect the output.','fail'));tone('fail');}};
try{catalog=await api('/api/catalog');renderGraves();status(`${catalog.commits} real demo commits read. Choose a ghost.`);}catch(e){status(e.message);}
const canvas=$('sky'),ctx=canvas.getContext('2d');let frame=0;function draw(){const box=canvas.getBoundingClientRect();canvas.width=box.width*devicePixelRatio;canvas.height=box.height*devicePixelRatio;ctx.scale(devicePixelRatio,devicePixelRatio);ctx.clearRect(0,0,box.width,box.height);const paused=reduced||document.body.classList.contains('paused')||document.hidden;if(!paused)frame++;for(let i=0;i<35;i++){let x=(i*91.7)%box.width,y=(i*51.3)%box.height;ctx.fillStyle=`rgba(203,192,245,${.15+.2*Math.sin(frame*.014+i)})`;ctx.beginPath();ctx.arc(x,y,1,0,Math.PI*2);ctx.fill();}for(let i=0;i<6;i++){let x=(i*153+frame*.18)%box.width,y=100+Math.sin(frame*.018+i)*35;ctx.fillStyle='#b6a1ef20';ctx.beginPath();ctx.ellipse(x,y,13,20,0,0,Math.PI*2);ctx.fill();}requestAnimationFrame(draw);}draw();
