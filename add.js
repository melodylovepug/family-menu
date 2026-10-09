/* ---- 添加新菜: dishes stored in the Google Sheet (Apps Script web app) ---- */
(function(){
 const normN=t=>String(t||'').replace(/（/g,'(').replace(/）/g,')').replace(/\s+/g,'').toLowerCase();
 const seen=new Set(ADD.known);
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
  const recent=yes(r.recent),link=okUrl(r.link)?String(r.link):'',ing=String(r.ingredients||'').trim().slice(0,500);
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
  const meat=prot&&prot!=='素'&&prot!=='甜品',soup=yes(r.soup)||sec==='soup'||name.includes('汤');
  let k=null,t=recent;
  if(todo){if(recent&&meat){k='main';t=true;}}
  else if(!ADD.noPick.includes(sec)){k=sec==='cold'?'cold':(meat?'main':null);}
  if(k)PK.push({id,n:name,k,m:prot||'素',s:soup,t,r:false,o:has,p:todo?'':photo,i:icon,c:todo?'todo':sec,l:ADD.hist[key]||''});
  return d;}
 window.__addRow=addRow;
 fetch(ADD.url,{cache:'no-store'}).then(r=>r.json()).then(j=>{if(j&&j.ok&&Array.isArray(j.rows))j.rows.forEach(r=>{try{addRow(r)}catch(e){}});
  window.__sheetRows=(j&&j.rows||[]).length;if(/^#g\d+$/.test(location.hash))openFromHash();}).catch(()=>{window.__sheetRows=-1;});
 /* form */
 const f=document.getElementById('addf');if(!f)return;
 const ob=document.getElementById('add-open'),msg=document.getElementById('af-msg'),go=document.getElementById('af-go');
 ob.addEventListener('click',()=>{const o=f.classList.toggle('hide');ob.setAttribute('aria-expanded',String(!o));if(!o)document.getElementById('af-name').focus();});
 const secw=document.getElementById('af-secw');
 f.querySelectorAll('input[name=af-where]').forEach(x=>x.addEventListener('change',()=>{secw.style.display=f.querySelector('input[name=af-where]:checked').value==='todo'?'none':'';}));
 function shrink(file){return new Promise((res,rej)=>{const u=URL.createObjectURL(file),im=new Image();
  im.onload=()=>{const s=Math.min(1,1200/Math.max(im.naturalWidth,im.naturalHeight)),c=document.createElement('canvas');
   c.width=Math.round(im.naturalWidth*s);c.height=Math.round(im.naturalHeight*s);const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);
   g.drawImage(im,0,0,c.width,c.height);URL.revokeObjectURL(u);res(c.toDataURL('image/jpeg',0.82));};
  im.onerror=()=>{URL.revokeObjectURL(u);rej(new Error('photo'));};im.src=u;});}
 f.addEventListener('submit',async e=>{e.preventDefault();
  const name=document.getElementById('af-name').value.trim();if(!name){msg.textContent='请填菜名';return;}
  const where=f.querySelector('input[name=af-where]:checked').value;
  const p={name,where,section:where==='menu'?document.getElementById('af-sec').value:'',protein:document.getElementById('af-prot').value,
   recent:document.getElementById('af-recent').checked,soup:document.getElementById('af-soup').checked,
   link:document.getElementById('af-link').value.trim(),ingredients:document.getElementById('af-ing').value.trim(),website:document.getElementById('af-hp').value};
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
})();
