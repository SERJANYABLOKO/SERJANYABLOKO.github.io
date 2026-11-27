/* Общие helpers для всех страниц Serjant Lab */

const SESSION_KEY = 'el_session';
const PROGRESS_KEY = 'el_progress';

function getSession(){
  try { return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null'); }
  catch(e){ return null; }
}
function saveSession(user){ localStorage.setItem(SESSION_KEY, JSON.stringify(user)); }
function clearSession(){ localStorage.removeItem(SESSION_KEY); }

function progressKey(){ const s = getSession(); return PROGRESS_KEY + '_' + (s ? s.login : 'guest'); }
function getProgress(){
  try { return JSON.parse(localStorage.getItem(progressKey()) || '{}'); }
  catch(e){ return {}; }
}
function saveProgress(p){ localStorage.setItem(progressKey(), JSON.stringify(p)); }
function markLessonDone(key, score, total){
  const p = getProgress();
  const old = p[key];
  p[key] = { done:true, score:Math.max(score, old ? old.score : 0), total:total };
  saveProgress(p);
}
function saveTaskResult(key, score, total){
  const p = getProgress();
  const k = 'task:' + key;
  const old = p[k];
  if (!old || score > old.score) p[k] = { done:true, score:score, total:total };
  saveProgress(p);
}

async function apiGet(path){
  const res = await fetch(path, {cache:'no-store'});
  if (!res.ok) throw new Error('Не удалось загрузить ' + path + ' (HTTP ' + res.status + ')');
  return res.json();
}

function headerHTML(active){
  const s = getSession();
  const links = [
    ['index.html','Главная'],
    ['courses.html','Курсы'],
    ['tasks.html','Задания'],
    ['words.html','1000 слов'],
    ['login.html','Вход']
  ];
  const nav = links.map(([href,label]) =>
    '<a href="' + href + '"' + (active === href ? ' class="active"' : '') + '>' + label + '</a>'
  ).join('');
  const user = s
    ? '<div class="user-area"><span class="user-chip"><span class="avatar">' + (s.name || s.login).charAt(0).toUpperCase() + '</span>' + (s.name || s.login) + '</span><button class="logout" id="logoutBtn">Выйти</button></div>'
    : '<div class="user-area"><a href="login.html" class="btn small">Войти</a></div>';
  return '<header class="header"><div class="container">' +
    '<a href="index.html" class="logo"><span class="icon">SL</span>Serjant <span>Lab</span></a>' +
    '<nav class="nav" id="mainNav">' + nav + '</nav>' +
    '<div style="display:flex;align-items:center;gap:10px">' + user +
    '<button class="menu-btn" id="menuBtn" aria-label="Меню">☰</button></div>' +
    '</div></header>';
}
function mountHeader(active){
  document.body.insertAdjacentHTML('afterbegin', headerHTML(active));
  const btn = document.getElementById('menuBtn');
  const nav = document.getElementById('mainNav');
  if (btn && nav) btn.onclick = () => nav.classList.toggle('open');
  const out = document.getElementById('logoutBtn');
  if (out) out.onclick = () => { clearSession(); location.href = 'index.html'; };
}
function footerHTML(){
  return '<footer class="footer container"><div>Serjant Lab — учим английский простыми словами</div>' +
    '<div><a href="../index.html#portfolio">← В портфолио</a> · SERJANT DEV</div></footer>';
}
function mountFooter(){ document.body.insertAdjacentHTML('beforeend', footerHTML()); }

function esc(str){
  return String(str).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
