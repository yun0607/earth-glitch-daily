const TZ = 'Asia/Taipei';
const $ = (selector) => document.querySelector(selector);
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const taiwanDate = () => new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const readableDate = (date) => date.replace(/-/g,'.');
const validLicenses = new Set(['cc0','cc-by','cc-by-sa','cc-by-nc','cc-by-nc-sa']);
let species = [], today = taiwanDate();
function buildFallback(el){ el.innerHTML = '<span class="photo-placeholder" role="img" aria-label="圖像暫缺">✳</span>'; }
function savedPhoto(item){
  const photo=item.photo;
  const allowed=photo && validLicenses.has(photo.license) && /^https:\/\//.test(photo.url) && /^https:\/\//.test(photo.source) && photo.author && photo.attribution;
  return {taxonId:item.taxonId,photo:allowed?photo:null,source:item.taxonId?`https://www.inaturalist.org/taxa/${item.taxonId}`:`https://www.inaturalist.org/search?q=${encodeURIComponent(item.scientificName)}`};
}
function unlocked(item){return item.date<=today;}
function makePhoto(item,info,target){
  if(!info.photo){buildFallback(target);return;}
  const photo=info.photo;
  target.innerHTML='';const img=document.createElement('img');img.alt=`${item.title}（iNaturalist 授權照片）`;img.loading='lazy';img.referrerPolicy='no-referrer';img.onerror=()=>buildFallback(target);img.src=photo.url;target.append(img);
  const label=document.createElement('div');label.className='photo-credit';
  const source=document.createElement('a');source.href=photo.source;source.target='_blank';source.rel='noopener noreferrer';source.textContent=`圖片：${photo.attribution} · ${photo.license.toUpperCase()}`;
  label.append(source);target.append(label);
}

async function renderToday(){
  const item=species.find((x)=>x.date===today);
  const first=species[0];
  $('#today-date').textContent=new Intl.DateTimeFormat('zh-TW',{timeZone:TZ,dateStyle:'full'}).format(new Date());
  $('#day-count').textContent=first?`DATABASE ONLINE · ${species.filter(unlocked).length} / ${species.length} UNLOCKED`:'';
  const panel=$('#spotlight');
  if(!item){panel.innerHTML=`<div class="notice"><h2>今天的研究檔案尚未排程</h2><p>已安排日期之外不會循環使用舊物種。請依 AGENTS.md 新增下一天的資料。</p><a class="outlink" href="#archive">查看已公開的歷史圖鑑 ↗</a></div>`;return;}
  panel.innerHTML=`<div class="photo-panel" id="hero-photo"><span class="photo-placeholder">✳</span></div><div class="spotlight-copy"><span class="token">TODAY'S GLITCH · ${escapeHTML(readableDate(item.date))}</span><h2>${escapeHTML(item.title)}</h2><span class="latin">${escapeHTML(item.scientificName)}</span><p>${escapeHTML(item.teaser)}</p><div class="rating">異常指數 <strong>${'★'.repeat(item.bugRating)}${'☆'.repeat(5-item.bugRating)}</strong></div><button class="primary" id="today-detail">開啟研究檔案 ↗</button></div>`;
  $('#today-detail').addEventListener('click',()=>openDetail(item));
  const info=savedPhoto(item);makePhoto(item,info,$('#hero-photo'));
}
function renderArchive(){
  const selection=$('#category').value,query=$('#search').value.trim().toLocaleLowerCase();
  const results=species.filter(x=>(!selection||x.category===selection)&&(!query||x.title.toLocaleLowerCase().includes(query)||x.scientificName.toLocaleLowerCase().includes(query)));
  $('#empty').classList.toggle('hidden',Boolean(results.length));
  $('#archive-list').innerHTML='';
  for(const item of results){
    const locked=!unlocked(item);const button=document.createElement('button');button.className=`specimen${locked?' locked':''}`;button.disabled=locked;
    button.innerHTML=`<span class="mini">${locked?'🔒 UNRELEASED':'✳ ARCHIVED'} · ${escapeHTML(readableDate(item.date))}</span><h3>${locked?'機密物種':escapeHTML(item.title)}</h3><span class="sub">${locked?'資料尚未解鎖':escapeHTML(item.scientificName)}</span><span class="hint">${locked?'未來公開':escapeHTML(item.category)+' · 查看檔案 ↗'}</span>`;
    if(!locked)button.addEventListener('click',()=>openDetail(item));$('#archive-list').append(button);
  }
}
async function openDetail(item){
  if(!unlocked(item))return;
  const modal=document.createElement('div');modal.className='modal';modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');modal.setAttribute('aria-label',`${item.title}研究檔案`);
  modal.innerHTML=`<div class="dialog panel"><button class="close" aria-label="關閉">×</button><span class="eyebrow">SPECIMEN FILE · ${escapeHTML(readableDate(item.date))}</span><h2>${escapeHTML(item.title)}</h2><div class="latin">${escapeHTML(item.scientificName)}</div><div class="photo-panel" id="modal-photo" style="min-height:235px;margin:20px 0"><span class="photo-placeholder">✳</span></div><p>${escapeHTML(item.teaser)}</p><dl><dt>分類</dt><dd>${escapeHTML(item.category)}</dd><dt>奇特特徵</dt><dd>${escapeHTML(item.feature)}</dd><dt>BUG 指數</dt><dd>${'★'.repeat(item.bugRating)}（娛樂指標）</dd><dt>物種來源</dt><dd id="source-detail">來源載入中…</dd></dl><p class="credit">來源為 iNaturalist。圖片與物種文字不代表 iNaturalist 官方推薦；如圖片無適合的開放授權則顯示替代圖。</p></div>`;
  document.body.append(modal);const close=()=>{modal.remove();document.removeEventListener('keydown',onKey)};const onKey=e=>{if(e.key==='Escape')close()};document.addEventListener('keydown',onKey);
  modal.querySelector('.close').addEventListener('click',close);modal.addEventListener('click',e=>{if(e.target===modal)close()});modal.querySelector('.close').focus();
  const info=savedPhoto(item);if(!modal.isConnected)return;
  makePhoto(item,info,modal.querySelector('#modal-photo'));
  const a=document.createElement('a');a.href=info.source;a.target='_blank';a.rel='noopener noreferrer';a.textContent=info.taxonId?'查看物種紀錄 ↗':'搜尋原始資料 ↗';modal.querySelector('#source-detail').replaceChildren(a);
}
async function main(){
  try{
    const response=await fetch('data/species.json');if(!response.ok)throw Error('資料讀取失敗');
    species=await response.json();species.sort((a,b)=>a.date.localeCompare(b.date));
    const categories=[...new Set(species.map(s=>s.category))].sort((a,b)=>a.localeCompare(b,'zh-Hant'));
    for(const c of categories){const option=document.createElement('option');option.value=c;option.textContent=c;$('#category').append(option)}
    $('#search').addEventListener('input',renderArchive);$('#category').addEventListener('change',renderArchive);
    renderArchive();await renderToday();
  }catch(e){$('#spotlight').innerHTML=`<div class="notice">資料載入失敗。請使用本機伺服器或 GitHub Pages 開啟網站。<br><small>${escapeHTML(e.message)}</small></div>`;}
}
main();
