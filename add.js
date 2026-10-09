/* ---- 添加新菜: dishes stored in the Google Sheet (Apps Script web app) ---- */
(function(){
 const normN=t=>String(t||'').replace(/（/g,'(').replace(/）/g,')').replace(/\s+/g,'').toLowerCase();
 const seen=new Set(ADD.known);
 const SKIP=' [skip]', unSkip=v=>{v=String(v||'').trim();const k=v.endsWith(SKIP.trim());return [k?v.slice(0,-SKIP.trim().length).trim():v,k];};
 const EB=ADD.base, EDIT='✏️', isEdit=r=>String(r&&r.name||'').startsWith(EDIT);
 const okUrl=u=>/^https?:\/\//i.test(u||'');
 const el=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;};
 const yes=v=>v===true||/^(yes|y|true|1|是|✓)$/i.test(String(v||'').trim());
 function photoEl(r,cls){const im=el('img',cls);im.alt='';im.loading='lazy';im.src=r.photo;
  im.addEventListener('error',()=>{if(r.photo_id&&!im.dataset.fb){im.dataset.fb=1;im.src='https://drive.google.com/thumbnail?id='+encodeURIComponent(r.photo_id)+'&sz=w1200';}else im.remove();});return im;}
 function addRow(r){
  const name=String(r.name||'').trim().slice(0,60),id=String(r.id||'');
  if(!name||!/^g\d+$/.test(id)||document.getElementById(id))return null;
  const key=normN(name);if(seen.has(key))return null;seen.add(key);
  const todo=r.where==='todo',sec=todo?null:(ADD.secs[r.section]?r.section:'other');
  const S=todo?null:ADD.secs[sec];
  const prot=ADD.canon[r.protein]||String(r.protein||'');
  const recent=yes(r.recent),link=okUrl(r.link)?String(r.link):'',[ing,skip]=unSkip(String(r.ingredients||'').slice(0,500));
  const photo=/^https:\/\/(lh\d\.googleusercontent\.com|drive\.google\.com)\//.test(r.photo||'')?r.photo:'';
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
 fetch(ADD.url,{cache:'no-store'}).then(r=>r.json()).then(j=>{if(j&&j.ok&&Array.isArray(j.rows)){j.rows.forEach(r=>{if(!isEdit(r))try{addRow(r)}catch(e){}});
   j.rows.forEach(r=>{if(isEdit(r))EDITS.push(r)});applyAll();}
  window.__sheetRows=(j&&j.rows||[]).length;if(/^#g\d+$/.test(location.hash))openFromHash();}).catch(()=>{window.__sheetRows=-1;});
 /* form */
 const f=document.getElementById('addf');if(!f)return;
 const ob=document.getElementById('add-open'),msg=document.getElementById('af-msg'),go=document.getElementById('af-go');
 ob.addEventListener('click',()=>{const o=f.classList.toggle('hide');ob.setAttribute('aria-expanded',String(!o));if(!o)document.getElementById('af-name').focus();});
 const secw=document.getElementById('af-secw');
  function shrink(file){return new Promise((res,rej)=>{const u=URL.createObjectURL(file),im=new Image();
  im.onload=()=>{const s=Math.min(1,1200/Math.max(im.naturalWidth,im.naturalHeight)),c=document.createElement('canvas');
   c.width=Math.round(im.naturalWidth*s);c.height=Math.round(im.naturalHeight*s);const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);
   g.drawImage(im,0,0,c.width,c.height);URL.revokeObjectURL(u);res(c.toDataURL('image/jpeg',0.82));};
  im.onerror=()=>{URL.revokeObjectURL(u);rej(new Error('photo'));};im.src=u;});}
 f.addEventListener('submit',async e=>{e.preventDefault();
  if(editId)return saveEdit();
  const name=document.getElementById('af-name').value.trim();if(!name){msg.textContent='请填菜名';return;}
  const where=f.querySelector('input[name=af-where]:checked').value;
  const p={name,where,section:document.getElementById('af-sec').value,protein:document.getElementById('af-prot').value,
   recent:document.getElementById('af-recent').checked,soup:false,
   link:document.getElementById('af-link').value.trim(),ingredients:document.getElementById('af-ing').value.trim().slice(0,490)+(document.getElementById('af-skip').checked?SKIP:''),website:document.getElementById('af-hp').value};
  if(p.link&&!okUrl(p.link)){msg.textContent='链接要以 http 开头';return;}
  go.disabled=true;msg.textContent='保存中…';
  try{const file=document.getElementById('af-photo').files[0];if(file){msg.textContent='压缩照片…';p.photo=await shrink(file);msg.textContent='上传中…';}
   const r=await fetch(ADD.url,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(p)});
   const j=await r.json();if(!j.ok)throw new Error(j.error||'error');
   const d=j.row&&addRow(j.row);f.reset();secw.style.display='';msg.textContent='已添加 ✓';
   if(d){d.scrollIntoView({behavior:'smooth',block:'center'});d.classList.remove('flash');void d.offsetWidth;d.classList.add('flash');}
   else if(j.row)msg.textContent='已保存 ✓（菜单里已有同名的菜）';
  }catch(err){msg.textContent='没保存成功，请稍后再试';}
  finally{go.disabled=false;}});

 /* ---- ✏️ 编辑: edit rows are normal sheet rows whose name is "✏️<dish id>" (a full snapshot of the form; empty photo = keep);
    "✏️<dish id>!" resets the dish to menu.json. Latest row wins; menu.json is never touched. ---- */
 const EDITS=[];
 const PROTS=['','牛','猪','羊','鸡','鸭','鱼','龙虾/虾','蟹','蛤蜊/贝','豆腐/蛋','素'];
 function stateFor(id){const b=EB[id];if(!b)return null;let st=null,photo=b.photo,pid=b.photo_id||'';
  for(const r of EDITS){const nm=String(r.name);if(nm===EDIT+id+'!'){st=null;photo=b.photo;pid=b.photo_id||'';continue;}
   if(nm!==EDIT+id)continue;const todo=r.where==='todo';
   st={w:todo?'todo':'menu',sec:todo?'':(ADD.secs[r.section]?r.section:'other'),m:ADD.canon[r.protein]||String(r.protein||''),r:yes(r.recent),s:yes(r.soup)||r.section==='soup',
    link:okUrl(r.link)?String(r.link):''};[st.ing,st.k]=unSkip(r.ingredients);
   if(/^https:\/\/(lh\d\.googleusercontent\.com|drive\.google\.com)\//.test(r.photo||'')){photo=r.photo;pid=r.photo_id||'';}}
  return Object.assign({},b,st||{},{photo,photo_id:pid,edited:!!st||photo!==b.photo});}
 const ORIG={};
 function boxOf(st){return st.w==='todo'?document.querySelector('#todo .todo-list'):document.getElementById(st.sec);}
 function bump(box,n){const c=box&&(box.closest('.card')||box);const e=c&&c.querySelector('h2 .n');if(e)e.textContent=+e.textContent+n;}
 function apply(id){const d=document.getElementById(id),b=EB[id];if(!d||!b)return;
  if(!(id in ORIG)){const s0=d.querySelector('.rcp-src');ORIG[id]=s0&&!s0.dataset.ph?s0.cloneNode(true):null;}
  const st=stateFor(id);d._st=st;const todo=st.w==='todo',S=todo?null:ADD.secs[st.sec],icon=todo?'🌸':S[0],name=d.querySelector('.name').textContent;
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
  if(k&&!st.k)PK.push({id,n:name,k,m:st.m||'素',s:soup,t,r:b.rb,o:has,p:todo?'':st.photo,i:icon,c:todo?'todo':st.sec,l:b.l||(old0&&old0.l)||''});}
 function applyAll(){const ids=new Set();EDITS.forEach(r=>{const m=String(r.name).match(/^✏️([dtg]\d+)!?$/);if(m)ids.add(m[1]);});ids.forEach(id=>{try{apply(id)}catch(e){}});
  window.__edits=EDITS.length;}
 window.__applyEdit=r=>{EDITS.push(r);applyAll();};
 /* every card opens; sheets without content get a placeholder so they can be edited */
 document.querySelectorAll('.dish.empty').forEach(d=>d.classList.remove('empty'));
 const _open=openDish,_close=closeDish;let editId=null;const home=f.parentElement;
 openDish=function(d){if(!d.querySelector('.rcp-src')){const card=d.closest('.card'),s=el('div','rcp-src');s.dataset.ph=1;
   const todo=d.dataset.cat==='todo',S=ADD.secs[d.dataset.cat];s.dataset.ic=todo?'📝':(S?S[0]:'🍽');s.dataset.cat=todo?'待做 · To try':(S?S[1]+' · '+S[2]:'');
   s.appendChild(el('p','tbd-steps','做法步骤 待补充'));d.appendChild(s);}
  stopEdit();_open(d);
  if(EB[d.id]){const r=document.getElementById('sh-r'),b=el('button','add-btn ed-btn','✏️ 编辑');b.type='button';b.id='ed-open';
   b.addEventListener('click',()=>startEdit(d));r.insertBefore(b,r.firstChild);}};
 closeDish=function(){stopEdit();_close();};
 document.querySelectorAll('.dish').forEach(d=>d.querySelector('.rcp-src')||0);
 function setWhere(v){f.querySelector('input[name=af-where][value='+v+']').checked=true;}
 function startEdit(d){const st=d._st||stateFor(d.id);if(!st)return;editId=d.id;
  const r=document.getElementById('sh-r');f.reset();msg.textContent='';
  document.getElementById('ed-open').style.display='none';r.insertBefore(f,r.children[1]||null);f.classList.remove('hide');f.classList.add('edf');
  const nm=document.getElementById('af-name');nm.value=d.querySelector('.name').textContent;nm.disabled=true;
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
  const p={name:EDIT+id,where,section:document.getElementById('af-sec').value,protein:document.getElementById('af-prot').value,
   recent:document.getElementById('af-recent').checked,soup:false,
   link:document.getElementById('af-link').value.trim(),ingredients:document.getElementById('af-ing').value.trim().slice(0,490)+(document.getElementById('af-skip').checked?SKIP:''),website:document.getElementById('af-hp').value};
  if(p.link&&!okUrl(p.link)){msg.textContent='链接要以 http 开头';return;}
  go.disabled=true;msg.textContent='保存中…';
  try{const file=document.getElementById('af-photo').files[0];if(file){msg.textContent='压缩照片…';p.photo=await shrink(file);msg.textContent='上传中…';}
   const r=await fetch(ADD.url,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(p)});
   const j=await r.json();if(!j.ok)throw new Error(j.error||'error');
   EDITS.push(j.row||Object.assign({},p,{photo:''}));apply(id);window.__lastEdit=j.row;
   const d=document.getElementById(id);openDish(d);const m2=el('p','tbd-steps','已保存修改 ✓');m2.id='ed-ok';document.getElementById('sh-r').insertBefore(m2,document.getElementById('sh-r').firstChild);
  }catch(err){msg.textContent='没保存成功，请稍后再试';}
  finally{go.disabled=false;}}
})();
