/* ---- 添加新菜: dishes stored in the Google Sheet (Apps Script web app) ---- */
(function(){
 const normN=t=>String(t||'').replace(/（/g,'(').replace(/）/g,')').replace(/\s+/g,'').toLowerCase();
 const seen=new Set(ADD.known);
 const SKIP=' [skip]', unSkip=v=>{v=String(v||'').trim();const k=v.endsWith(SKIP.trim());return [k?v.slice(0,-SKIP.trim().length).trim():v,k];};
 const cleanName=v=>String(v||'').replace(/[\[\]\u0000-\u001f]/g,' ').replace(/\s+/g,' ').trim().slice(0,40);
 const parseIng=v=>{const [a,k]=unSkip(v);const m=a.match(/\s*\[name:([^\]]{1,60})\]$/);return [m?a.slice(0,m.index).trim():a,k,m?cleanName(m[1]):''];};
 const ORIGN={};
 const EB=ADD.base, EDIT='✏️', isEdit=r=>String(r&&r.name||'').startsWith(EDIT);
 const DAY='📅',isDay=r=>String(r&&r.name||'').startsWith(DAY),isMeta=r=>isEdit(r)||isDay(r);
 const OKPH=/^(https:\/\/(lh\d\.googleusercontent\.com|drive\.google\.com)\/|data:image\/jpeg;base64,)/;
 const okUrl=u=>/^https?:\/\//i.test(u||'');
 const el=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;};
 const yes=v=>v===true||/^(yes|y|true|1|是|✓)$/i.test(String(v||'').trim());
 function photoEl(r,cls){const im=el('img',cls);im.alt='';im.loading='lazy';im.src=r.photo;
  im.addEventListener('error',()=>{if(r.photo_id&&!im.dataset.fb){im.dataset.fb=1;im.src='https://drive.google.com/thumbnail?id='+encodeURIComponent(r.photo_id)+'&sz=w1200';}else im.remove();});return im;}
 function addRow(r){
  const name=String(r.name||'').trim().slice(0,60),id=String(r.id||'');
  if(!name||!/^g\d+$/.test(id)||document.getElementById(id))return null;
  const key=normN(name);if(seen.has(key))return null;seen.add(key);ADDED[id]=key;
  const todo=r.where==='todo',sec=todo?null:(ADD.secs[r.section]?r.section:'other');
  const S=todo?null:ADD.secs[sec];
  const prot=ADD.canon[r.protein]||String(r.protein||'');
  const recent=yes(r.recent),link=okUrl(r.link)?String(r.link):'',[ing,skip]=unSkip(String(r.ingredients||'').slice(0,500));
  const photo=OKPH.test(r.photo||'')?r.photo:'';
  const has=!!(link||ing||photo);
  const icon=todo?'🌸':S[0];
  const d=el('div','dish'+(has?'':' empty bare'));d.id=id;d.dataset.cat=todo?'todo':sec;
  d.dataset.s=(name+' '+ing+(recent?' 最近':'')).toLowerCase();
  const row=el('div','row');
  if(photo&&!todo){const im=photoEl({photo,photo_id:r.photo_id},'dth');row.appendChild(im);im.addEventListener('error',()=>{if(!row.querySelector('.dth')){const ic=el('span','dth ic',icon);row.insertBefore(ic,row.firstChild);}});}
  else row.appendChild(el('span','dth ic',icon));
  row.appendChild(el('span','name',name));
  if(recent)row.appendChild(el('span','recent','最近'));
  if(skip)row.appendChild(el('span','skp','skip'));
  if(!has)row.appendChild(el('span','tbd','待补充'));
  d.appendChild(row);
  if(has){const src=el('div','rcp-src');src.dataset.ic=todo?'📝':icon;src.dataset.cat=todo?'待做 · To try':S[1]+' · '+S[2];
   if(link){const w=el('div','srcs'),a=el('a','lnk',(/xhslink|xiaohongshu/.test(link)?'📕 小红书':/youtu/.test(link)?'▶ YouTube':'🔗 食谱'));a.href=link;a.target='_blank';a.rel='noopener';w.appendChild(a);src.appendChild(w);}
   if(ing){const w=el('div','sh-sum');w.appendChild(el('div','ing',ing));src.appendChild(w);}
   if(photo)src.appendChild(photoEl({photo,photo_id:r.photo_id},'ph'));
   src.appendChild(el('p','tbd-steps','做法步骤 待补充'));d.appendChild(src);}
  const box=todo?document.querySelector('#todo .todo-list'):document.getElementById(sec);if(!box)return null;
  box.appendChild(d);bindDish(d);
  const n=(todo?document.getElementById('todo'):box).querySelector('h2 .n');if(n)n.textContent=+n.textContent+1;
  /* picker: same rules as built-in dishes */
  const meat=prot&&prot!=='素'&&prot!=='甜品',soup=yes(r.soup)||r.section==='soup'||name.includes('汤');
  let k=null,t=recent;
  if(todo){if(recent&&meat){k='main';t=true;}}
  else if(!ADD.noPick.includes(sec)){k=sec==='cold'?'cold':(meat?'main':null);}
  if(k&&!skip)PK.push({id,n:name,k,m:prot||'素',s:soup,t,r:false,o:has,p:todo?'':photo,i:icon,c:todo?'todo':sec,l:ADD.hist[key]||''});
  EB[id]={w:todo?'todo':'menu',sec:todo?'':sec,m:prot,r:recent,s:soup,link,ing,photo,photo_id:r.photo_id||'',tbd:false,rb:false,dess:false,k:skip,l:ADD.hist[key]||''};
  return d;}
 window.__addRow=addRow;
 const ADDED={};
 /* form */
 const f=document.getElementById('addf');if(!f)return;
 const ob=document.getElementById('add-open'),msg=document.getElementById('af-msg'),go=document.getElementById('af-go');
 ob.addEventListener('click',()=>{const o=f.classList.toggle('hide');ob.setAttribute('aria-expanded',String(!o));if(!o)document.getElementById('af-name').focus();});
 const secw=document.getElementById('af-secw');
  function shrink(file){return new Promise((res,rej)=>{const u=URL.createObjectURL(file),im=new Image();
  im.onload=()=>{const s=Math.min(1,1000/Math.max(im.naturalWidth,im.naturalHeight)),c=document.createElement('canvas');
   c.width=Math.round(im.naturalWidth*s);c.height=Math.round(im.naturalHeight*s);const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);
   g.drawImage(im,0,0,c.width,c.height);URL.revokeObjectURL(u);res(c.toDataURL('image/jpeg',0.8));};
  im.onerror=()=>{URL.revokeObjectURL(u);rej(new Error('photo'));};im.src=u;});}
 f.addEventListener('submit',async e=>{e.preventDefault();
  if(editId)return saveEdit();
  const name=document.getElementById('af-name').value.trim();if(!name){msg.textContent='请填菜名';return;}
  const where=f.querySelector('input[name=af-where]:checked').value;
  const p={name,where,section:document.getElementById('af-sec').value,protein:document.getElementById('af-prot').value,
   recent:document.getElementById('af-recent').checked,soup:false,
   link:document.getElementById('af-link').value.trim(),ingredients:document.getElementById('af-ing').value.trim().slice(0,490)+(document.getElementById('af-skip').checked?SKIP:''),website:document.getElementById('af-hp').value};
  if(p.link&&!okUrl(p.link)){msg.textContent='链接要以 http 开头';return;}
  go.disabled=true;
  try{const file=document.getElementById('af-photo').files[0];if(file){msg.textContent='压缩照片…';p.photo=await shrink(file);}}
  catch(err){msg.textContent='照片读不了，换一张试试';go.disabled=false;return;}
  go.disabled=false;msg.textContent='';
  const tid='g'+Date.now(),it={cid:'c'+Date.now(),kind:'add',tid,p,t:Date.now()};
  const d=addRow(localRow(it));if(d)d.dataset.pend=1;
  PEND.push(it);savePend();f.reset();f.classList.add('hide');ob.setAttribute('aria-expanded','false');
  if(d){d.scrollIntoView({behavior:'smooth',block:'center'});d.classList.remove('flash');void d.offsetWidth;d.classList.add('flash');}
  flush();});

 /* ---- ✏️ 编辑: edit rows are normal sheet rows whose name is "✏️<dish id>" (a full snapshot of the form; empty photo = keep);
    "✏️<dish id>!" resets the dish to menu.json. Latest row wins; menu.json is never touched. ---- */
 const EDITS=[];
 const PROTS=['','牛','猪','羊','鸡','鸭','鱼','龙虾/虾','蟹','蛤蜊/贝','豆腐/蛋','素'];
 function stateFor(id){const b=EB[id];if(!b)return null;let st=null,photo=b.photo,pid=b.photo_id||'';
  let del=false;
  for(const r of EDITS){const nm=String(r.name);if(nm===EDIT+id+'!'){st=null;del=false;photo=b.photo;pid=b.photo_id||'';continue;}
   if(nm===EDIT+id+'✕'){del=true;continue;}
   if(nm!==EDIT+id)continue;const todo=r.where==='todo';
   st={w:todo?'todo':'menu',sec:todo?'':(ADD.secs[r.section]?r.section:'other'),m:ADD.canon[r.protein]||String(r.protein||''),r:yes(r.recent),s:yes(r.soup)||r.section==='soup',
    link:okUrl(r.link)?String(r.link):''};[st.ing,st.k,st.n]=parseIng(r.ingredients);
   if(OKPH.test(r.photo||'')){photo=r.photo;pid=r.photo_id||'';}}
  return Object.assign({},b,st||{},{photo,photo_id:pid,edited:!!st||photo!==b.photo,del});}
 const ORIG={};
 function boxOf(st){return st.w==='todo'?document.querySelector('#todo .todo-list'):document.getElementById(st.sec);}
 function bump(box,n){const c=box&&(box.closest('.card')||box);const e=c&&c.querySelector('h2 .n');if(e)e.textContent=+e.textContent+n;}
 function apply(id){const d=document.getElementById(id),b=EB[id];if(!d||!b)return;
  if(d._del){d._del=false;d.classList.remove('del');bump(d.parentElement,1);}
  if(!(id in ORIG)){const s0=d.querySelector('.rcp-src');ORIG[id]=s0&&!s0.dataset.ph?s0.cloneNode(true):null;}
  if(!(id in ORIGN))ORIGN[id]=d.querySelector('.name').textContent;
  const st=stateFor(id);d._st=st;const todo=st.w==='todo',S=todo?null:ADD.secs[st.sec],icon=todo?'🌸':S[0],name=st.n||ORIGN[id];d.querySelector('.name').textContent=name;
  /* move to the right section */
  const box=boxOf(st),cur=d.parentElement;if(box&&cur!==box){bump(cur,-1);box.appendChild(d);bump(box,1);}
  d.dataset.cat=todo?'todo':st.sec;
  /* sheet content: start from the built-in sheet and swap only what changed */
  const old=d.querySelector('.rcp-src');if(old)old.remove();
  let src=ORIG[id]?ORIG[id].cloneNode(true):null;
  const has=!!(st.link||st.ing||st.photo)||!!src;
  if(!src&&has){src=el('div','rcp-src');src.appendChild(el('p','tbd-steps','做法步骤 待补充'));}
  if(src){
   const top=sel=>[...src.children].filter(x=>x.matches(sel));
   if(st.link!==b.link){top('.srcs').forEach(x=>x.remove());
    if(st.link){const w=el('div','srcs'),a=el('a','lnk',(/xhslink|xiaohongshu/.test(st.link)?'📕 小红书':/youtu/.test(st.link)?'▶ YouTube':'🔗 食谱'));a.href=st.link;a.target='_blank';a.rel='noopener';w.appendChild(a);src.insertBefore(w,src.firstChild);}}
   if(st.ing!==b.ing){let sm=top('.sh-sum')[0];
    if(sm)sm.querySelectorAll('.ing').forEach(x=>x.remove());
    if(st.ing){if(!sm){sm=el('div','sh-sum');const s1=top('.srcs')[0];src.insertBefore(sm,s1?s1.nextSibling:src.firstChild);}sm.insertBefore(el('div','ing',st.ing),sm.firstChild);}
    else if(sm&&!sm.children.length)sm.remove();}
   if(st.photo!==b.photo){top('img.ph,.phc').forEach(x=>x.remove());
    if(st.photo){const im=photoEl({photo:st.photo,photo_id:st.photo_id},'ph');const a=top('.sh-sum')[0]||top('.srcs')[0];src.insertBefore(im,a?a.nextSibling:src.firstChild);}}
   src.dataset.ic=todo?'📝':icon;src.dataset.cat=todo?'待做 · To try':S[1]+' · '+S[2];d.appendChild(src);}
  /* card row */
  const row=d.querySelector('.row'),th=row.querySelector('.dth');let nt;
  if(st.photo&&!todo){nt=photoEl({photo:st.photo,photo_id:st.photo_id},'dth');nt.addEventListener('error',()=>{if(!row.querySelector('.dth'))row.insertBefore(el('span','dth ic',icon),row.firstChild);});}
  else nt=el('span','dth ic',icon);
  if(th)th.replaceWith(nt);else row.insertBefore(nt,row.firstChild);
  row.querySelectorAll('.recent,.tbd,.skp').forEach(x=>x.remove());
  if(st.r)row.appendChild(el('span','recent','最近'));
  if(st.k)row.appendChild(el('span','skp','skip'));
  if(b.tbd||!has)row.appendChild(el('span','tbd','待补充'));
  d.classList.toggle('bare',!has);
  d.dataset.s=(name+' '+st.ing+' '+(src?src.textContent:'')+(st.r?' 最近':'')).toLowerCase();
  /* picker entry: same rules as build.py */
  const i0=PK.findIndex(x=>x.id===id);const old0=i0>=0?PK.splice(i0,1)[0]:null;
  const meat=st.m&&st.m!=='素'&&st.m!=='甜品';let k=null,t=st.r;
  const soup=st.s||st.sec==='soup'||name.includes('汤');
  if(todo){if(st.r&&meat){k='main';t=true;}}
  else if(!ADD.noPick.includes(st.sec)&&!b.dess){k=st.sec==='cold'?'cold':(meat?'main':null);}
  if(k&&!st.k)PK.push({id,n:name,k,m:st.m||'素',s:soup,t,r:b.rb,o:has,p:todo?'':st.photo,i:icon,c:todo?'todo':st.sec,l:b.l||(old0&&old0.l)||''});
  /* deleted (✏️<id>✕ row): hidden everywhere — card, count, search, picker */
  if(st.del){d._del=true;d.classList.add('del');bump(d.parentElement,-1);const j=PK.findIndex(x=>x.id===id);if(j>=0)PK.splice(j,1);
   if(location.hash==='#'+id&&ov.classList.contains('on'))closeDish();}}
 function applyAll(){const ids=new Set();EDITS.forEach(r=>{const m=String(r.name).match(/^✏️([dtg]\d+)[!✕]?$/);if(m)ids.add(m[1]);});ids.forEach(id=>{try{apply(id)}catch(e){}});
  window.__edits=EDITS.length;}
 window.__applyEdit=r=>{EDITS.push(r);applyAll();};
 /* every card opens; sheets without content get a placeholder so they can be edited */
 document.querySelectorAll('.dish.empty').forEach(d=>d.classList.remove('empty'));
 const _open=openDish,_close=closeDish;let editId=null;const home=f.parentElement;
 openDish=function(d){if(!d.querySelector('.rcp-src')){const card=d.closest('.card'),s=el('div','rcp-src');s.dataset.ph=1;
   const todo=d.dataset.cat==='todo',S=ADD.secs[d.dataset.cat];s.dataset.ic=todo?'📝':(S?S[0]:'🍽');s.dataset.cat=todo?'待做 · To try':(S?S[1]+' · '+S[2]:'');
   s.appendChild(el('p','tbd-steps','做法步骤 待补充'));d.appendChild(s);}
  stopEdit();_open(d);
  if(EB[d.id]){const r=document.getElementById('sh-r'),bar=el('div','ed-bar'),b=el('button','add-btn ed-btn','✏️ 编辑'),x=el('button','add-btn ed-btn ed-del','🗑 删除');
   b.type=x.type='button';b.id='ed-open';x.id='ed-del';bar.id='ed-bar';
   b.addEventListener('click',()=>startEdit(d));x.addEventListener('click',()=>askDelete(d));bar.append(x,b);r.insertBefore(bar,r.firstChild);}};
 function askDelete(d){const name=d.querySelector('.name').textContent,ov2=el('div','cfm'),box=el('div','cfm-box');ov2.setAttribute('role','alertdialog');
  box.appendChild(el('p','cfm-t','确定删除「'+name+'」吗？'));box.appendChild(el('p','cfm-s','删除后菜单和随机选菜里都不会再出现'));
  const act=el('div','cfm-act'),no=el('button','cfm-no','取消'),yes2=el('button','cfm-yes','删除');no.type=yes2.type='button';act.append(no,yes2);box.appendChild(act);ov2.appendChild(box);
  const close=()=>ov2.remove();no.addEventListener('click',close);ov2.addEventListener('click',e=>{if(e.target===ov2)close();});
  yes2.addEventListener('click',()=>{close();doDelete(d.id);});document.body.appendChild(ov2);no.focus();}
 function doDelete(id){const it={cid:'c'+Date.now(),kind:'edit',p:{name:EDIT+id+'✕',where:'menu',section:'other',protein:'',recent:false,soup:false,link:'',ingredients:'',website:''},t:Date.now()};
  PEND.push(it);savePend();closeDish();EDITS.push(localRow(it));apply(id);flush();}
 window.__askDelete=askDelete;
 closeDish=function(){stopEdit();_close();};
 document.querySelectorAll('.dish').forEach(d=>d.querySelector('.rcp-src')||0);
 function setWhere(v){f.querySelector('input[name=af-where][value='+v+']').checked=true;}
 function startEdit(d){const st=d._st||stateFor(d.id);if(!st)return;editId=d.id;
  const r=document.getElementById('sh-r');f.reset();msg.textContent='';
  document.getElementById('ed-bar').style.display='none';r.insertBefore(f,r.children[1]||null);f.classList.remove('hide');f.classList.add('edf');
  const nm=document.getElementById('af-name');nm.value=d.querySelector('.name').textContent;nm.disabled=false;if(!(d.id in ORIGN))ORIGN[d.id]=nm.value;
  setWhere(st.w);document.getElementById('af-sec').value=st.w==='todo'?(st.s?'soup':'other'):(st.sec||'other');
  const ps=document.getElementById('af-prot');ps.value=PROTS.includes(st.m)?st.m:'';
  document.getElementById('af-recent').checked=!!st.r;document.getElementById('af-skip').checked=!!st.k;
  document.getElementById('af-link').value=st.link||'';document.getElementById('af-ing').value=st.ing||'';
  document.getElementById('af-photo').parentElement.firstChild.textContent=st.photo?'换照片（不选就保留原来的）':'照片';
  go.textContent='保存修改';f.scrollIntoView({block:'nearest'});}
 function stopEdit(){if(!editId)return;editId=null;f.reset();f.classList.add('hide');f.classList.remove('edf');home.appendChild(f);
  document.getElementById('af-name').disabled=false;secw.style.display='';go.textContent='保存';msg.textContent='';
  document.getElementById('af-photo').parentElement.firstChild.textContent='照片';ob.setAttribute('aria-expanded','false');}
 async function saveEdit(){const id=editId,where=f.querySelector('input[name=af-where]:checked').value;
  const nn=cleanName(document.getElementById('af-name').value);if(!nn){msg.textContent='请填菜名';return;}
  const nmk=nn!==ORIGN[id]?' [name:'+nn+']':'';
  const p={name:EDIT+id,where,section:document.getElementById('af-sec').value,protein:document.getElementById('af-prot').value,
   recent:document.getElementById('af-recent').checked,soup:false,
   link:document.getElementById('af-link').value.trim(),ingredients:document.getElementById('af-ing').value.replace(/\[(name:|skip)/g,'(').trim().slice(0,430)+nmk+(document.getElementById('af-skip').checked?SKIP:''),website:document.getElementById('af-hp').value};
  if(p.link&&!okUrl(p.link)){msg.textContent='链接要以 http 开头';return;}
  go.disabled=true;
  try{const file=document.getElementById('af-photo').files[0];if(file){msg.textContent='压缩照片…';p.photo=await shrink(file);}}
  catch(err){msg.textContent='照片读不了，换一张试试';go.disabled=false;return;}
  go.disabled=false;
  const it={cid:'c'+Date.now(),kind:'edit',p,t:Date.now()};PEND.push(it);savePend();
  EDITS.push(localRow(it));apply(id);
  const d=document.getElementById(id);if(d)openDish(d);else closeDish();
  flush();}
 /* ---- optimistic saves: pending queue (localStorage) + cached sheet rows ---- */
 const LS_P='fm-pending',LS_R='fm-rows';
 const lsGet=(k,dflt)=>{try{return JSON.parse(localStorage.getItem(k))||dflt}catch(e){return dflt}};
 const lsSet=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v));return true}catch(e){return false}};
 let PEND=lsGet(LS_P,[]).filter(x=>x&&x.p&&x.cid),ROWS=lsGet(LS_R,[]);if(!Array.isArray(ROWS))ROWS=[];
 function savePend(){if(!lsSet(LS_P,PEND)){/* quota: keep entries but drop local photo copies of the oldest */
   for(const x of PEND){if(x.p.photo){x.p.photo='';if(lsSet(LS_P,PEND))break;}}}}
 function localRow(it){const p=it.p;return {id:it.kind==='add'?it.tid:'',name:p.name,where:p.where==='todo'?'todo':'menu',section:p.section||'',protein:p.protein||'',
   recent:p.recent?'yes':'',soup:'',link:p.link||'',ingredients:p.ingredients||'',photo:p.photo||'',photo_id:'',_cid:it.cid};}
 const sig=r=>[r.name,r.where==='todo'?'todo':'menu',r.section||'',r.protein||'',yes(r.recent)?1:0,r.link||'',String(r.ingredients||'').trim()].join('\u0001');
 /* toast */
 const T=el('div','svt hide');T.setAttribute('role','status');T.setAttribute('aria-live','polite');document.body.appendChild(T);let tHide=0;
 function toast(state){clearTimeout(tHide);T.className='svt '+state;T.innerHTML='';
  if(state==='busy')T.textContent='保存中…';
  else if(state==='ok'){T.textContent='✓ 已保存';tHide=setTimeout(()=>T.classList.add('hide'),1800);}
  else if(state==='fail'){T.appendChild(document.createTextNode('保存失败 · '));const b=el('button','svt-r','重试');b.type='button';b.addEventListener('click',()=>flush(true));T.appendChild(b);}}
 function renameId(o,n){if(o===n)return;const d=document.getElementById(o);if(!d||document.getElementById(n))return;d.id=n;delete d.dataset.pend;
  PK.forEach(x=>{if(x.id===o)x.id=n;});if(EB[o]){EB[n]=EB[o];delete EB[o];}if(o in ORIG){ORIG[n]=ORIG[o];delete ORIG[o];}if(ADDED[o]){ADDED[n]=ADDED[o];delete ADDED[o];}
  const fix=r=>{if(r.name===EDIT+o)r.name=EDIT+n;else if(r.name===EDIT+o+'!')r.name=EDIT+n+'!';};EDITS.forEach(fix);PEND.forEach(x=>fix(x.p));savePend();
  if(location.hash==='#'+o)history.replaceState(null,'','#'+n);}
 let busy=false;
 async function flush(manual){if(busy||!PEND.length)return;busy=true;toast('busy');let fail=false;
  while(PEND.length){const it=PEND[0];
   try{const r=await fetch(ADD.url,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(it.p)});
    const j=await r.json();if(!j.ok)throw new Error(j.error||'error');
    const row=j.row||localRow(it);PEND.shift();savePend();
    if(it.kind==='add'&&j.row)renameId(it.tid,j.row.id);
    if(it.kind==='edit'){const k=EDITS.findIndex(x=>x._cid===it.cid);if(k>=0)EDITS[k]=row;}
    if(it.kind==='day'){const k=DAYROWS.findIndex(x=>x._cid===it.cid);if(k>=0)DAYROWS[k]=row;}
    if(j.row){ROWS.push(j.row);lsSet(LS_R,ROWS);}window.__lastEdit=row;
   }catch(e){fail=true;break;}}
  busy=false;toast(fail?'fail':'ok');window.__saveState=fail?'fail':'ok';}
 window.__flush=flush;window.__pending=()=>PEND.length;
 window.addEventListener('online',()=>flush());
 /* render: cached rows + pending immediately, then refresh from the sheet */
 function render(rows,first){
  /* pending items already in the sheet are confirmed: drop them */
  const names=new Map(),sigs=new Set();
  rows.forEach(r=>{if(isMeta(r))sigs.add(sig(r));else names.set(normN(r.name)+'|'+(r.where==='todo'?'todo':'menu'),r);});
  if(!busy){const keep=[];for(const it of PEND){const lr=localRow(it);
    if(it.kind==='add'){const m=names.get(normN(lr.name)+'|'+lr.where);if(m){renameId(it.tid,m.id);continue;}}
    else if(sigs.has(sig(lr)))continue;
    keep.push(it);}
   if(keep.length!==PEND.length){PEND=keep;savePend();}}
  const live=new Set(rows.filter(r=>!isMeta(r)).map(r=>String(r.id)));PEND.forEach(it=>{if(it.kind==='add')live.add(it.tid);});
  /* rows hidden in the sheet since the cache: remove their cards */
  Object.keys(ADDED).forEach(id=>{if(live.has(id))return;const d=document.getElementById(id);
   if(d){bump(d.parentElement,-1);d.remove();}const i=PK.findIndex(x=>x.id===id);if(i>=0)PK.splice(i,1);seen.delete(ADDED[id]);delete ADDED[id];delete EB[id];});
  rows.forEach(r=>{if(!isMeta(r))try{addRow(r)}catch(e){}});
  PEND.forEach(it=>{if(it.kind==='add'&&!document.getElementById(it.tid)){const d=addRow(localRow(it));if(d)d.dataset.pend=1;}});
  const before=new Set(EDITS.map(r=>r.name));EDITS.length=0;
  rows.forEach(r=>{if(isEdit(r))EDITS.push(r)});PEND.forEach(it=>{if(it.kind==='edit')EDITS.push(localRow(it));});
  EDITS.forEach(r=>before.add(r.name));
  before.forEach(nm=>{const m=String(nm).match(/^✏️([dtg]\d+)[!✕]?$/);if(m)try{apply(m[1])}catch(e){}});
  DAYROWS.length=0;rows.forEach(r=>{if(isDay(r))DAYROWS.push(r)});PEND.forEach(it=>{if(it.kind==='day')DAYROWS.push(localRow(it));});renderDays();
  window.__edits=EDITS.length;}
 /* ---- 📅 加入菜单: a day's meal is a sheet row named "📅YYYY-MM-DD" (dish ids, space-separated, in the ingredients column);
    "📅YYYY-MM-DD!" replaces that day's earlier rows. Merged into 最近每周菜单 and the picker's 2-week history. ---- */
 const DAYROWS=[],WDZ='一二三四五六日';
 const iso=x=>x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0');
 const pdate=s=>{const p=s.split('-').map(Number);return new Date(p[0],p[1]-1,p[2]);};
 const dayLab=s=>{const x=pdate(s);return '周'+WDZ[(x.getDay()+6)%7]+' '+(x.getMonth()+1)+'/'+x.getDate();};
 function dayMap(){const m={};for(const r of DAYROWS){const g=String(r.name).match(/^📅(\d{4}-\d{2}-\d{2})(!?)$/);if(!g)continue;
   const ids=String(r.ingredients||'').split(/[\s,]+/).filter(x=>/^[dtg]\d+$/.test(x));m[g[1]]=g[2]?ids:(m[g[1]]||[]).concat(ids.filter(i=>!(m[g[1]]||[]).includes(i)));}
  return m;}
 const L0={};
 function renderDays(){document.querySelectorAll('.wk .l.sl,.wk.wk-new').forEach(e=>{const w=e.closest('.wk');e.remove();if(w&&!w.querySelector('.l'))w.remove();});
  /* reset picker history to the build-time value, then fold in sheet days */
  PK.forEach(x=>{if(!(x.id in L0))L0[x.id]=x.l||'';x.l=L0[x.id];});Object.keys(EB).forEach(id=>{if(!(('e'+id) in L0))L0['e'+id]=EB[id].l||'';EB[id].l=L0['e'+id];});
  const m=dayMap(),box=document.querySelector('#weeks .weeks');window.__days=m;
  Object.keys(m).sort().forEach(ds=>{const ids=m[ds];if(!ids.length)return;
   ids.forEach(id=>{const p=PK.find(x=>x.id===id);if(p&&ds>(p.l||''))p.l=ds;if(EB[id]&&ds>(EB[id].l||''))EB[id].l=ds;});
   if(!box)return;const x=pdate(ds),mon=new Date(x);mon.setDate(x.getDate()-(x.getDay()+6)%7);const lab=(mon.getMonth()+1)+'.'+mon.getDate()+'.'+(mon.getFullYear()%100);
   let wk=[...box.querySelectorAll('.wk')].find(w=>(w.querySelector('.d')||{}).textContent===lab);
   if(!wk){wk=el('div','wk wk-new');wk.appendChild(el('div','d',lab));wk.dataset.mon=iso(mon);
    const after=[...box.querySelectorAll('.wk')].find(w=>{const t=(w.querySelector('.d')||{}).textContent||'';const q=t.split('.').map(Number);return q.length===3&&new Date(2000+q[2],q[0]-1,q[1])<mon;});
    box.insertBefore(wk,after||null);}
   const line=el('div','l sl');line.dataset.ds=ds;line.appendChild(el('span',null,dayLab(ds)));const sp=el('span');
   ids.forEach((id,i)=>{const d=document.getElementById(id);if(!d)return;if(sp.childNodes.length)sp.appendChild(document.createTextNode(' · '));
    const a=el('a','wkd',d.querySelector('.name').textContent);a.href='#'+id;a.dataset.d=id;
    a.addEventListener('click',e=>{e.preventDefault();if(d.classList.contains('del'))return;openDish(d);});sp.appendChild(a);});
   line.appendChild(sp);
   /* keep lines in date order inside the week */
   const nx=[...wk.querySelectorAll('.l.sl')].find(l=>l.dataset.ds>ds);wk.insertBefore(line,nx||null);});}
 function dlg(title,sub,btns){const o=el('div','cfm'),b=el('div','cfm-box');o.setAttribute('role','dialog');b.appendChild(el('p','cfm-t',title));if(sub)b.appendChild(el('p','cfm-s',sub));
  const act=el('div','cfm-act');btns.forEach(x=>{const k=el('button',x.cls||'cfm-no',x.t);k.type='button';k.addEventListener('click',()=>{o.remove();if(x.fn)x.fn();});act.appendChild(k);});
  b.appendChild(act);o.appendChild(b);o.addEventListener('click',e=>{if(e.target===o)o.remove();});document.body.appendChild(o);return o;}
 function nextDays(){const t=new Date();t.setHours(0,0,0,0);const out=[];for(const wd of [2,4]){const x=new Date(t);x.setDate(t.getDate()+((wd-t.getDay()+7)%7));out.push(iso(x));}return out.sort();}
 function saveDay(ds,ids,replace){const it={cid:'c'+Date.now(),kind:'day',p:{name:DAY+ds+(replace?'!':''),where:'menu',section:'other',protein:'',recent:false,soup:false,link:'',ingredients:ids.join(' '),website:''},t:Date.now()};
  PEND.push(it);savePend();DAYROWS.push(localRow(it));renderDays();flush();}
 function addToDay(){if(typeof cur==='undefined'||!cur||!cur.length)return;const ids=cur.map(x=>x.id);
  const btns=nextDays().map(ds=>({t:'📅 '+dayLab(ds),cls:'cfm-yes cfm-day',fn:()=>{
   const ex=(dayMap()[ds]||[]);if(!ex.length)return saveDay(ds,ids,false);
   dlg(dayLab(ds)+' 已经有菜单了','现在是：'+ex.map(i=>{const d=document.getElementById(i);return d?d.querySelector('.name').textContent:i;}).join('、'),
    [{t:'取消'},{t:'加上',cls:'cfm-no cfm-add',fn:()=>saveDay(ds,ids,false)},{t:'替换',cls:'cfm-yes',fn:()=>saveDay(ds,ids,true)}]);}}));
  btns.push({t:'取消'});dlg('加入哪天的菜单？','厨师周二、周四来 · 记入每周菜单和「近 2 周」',btns);}
 const ab=document.getElementById('pick-day');if(ab)ab.addEventListener('click',addToDay);
 window.__nextDays=nextDays;
 render(ROWS,true);
 fetch(ADD.url,{cache:'no-store'}).then(r=>r.json()).then(j=>{if(j&&j.ok&&Array.isArray(j.rows)){ROWS=j.rows;lsSet(LS_R,ROWS);render(ROWS);}
  window.__sheetRows=(j&&j.rows||[]).length;if(/^#g\d+$/.test(location.hash)&&!ov.classList.contains('on'))openFromHash();}).catch(()=>{window.__sheetRows=-1;});
 if(PEND.length)flush();
})();
