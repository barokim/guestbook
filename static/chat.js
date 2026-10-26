'use strict';
const el = id => document.getElementById(id);
let socket = null, room = null, seen = new Set();
async function api(path, method = 'GET', data) {
  const response = await fetch(path, {method, body: data && new URLSearchParams(data)});
  if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  return response.json();
}
function showError(error) { el('status').textContent = String(error); }
function add(message) {
  if (seen.has(message.id)) return;
  seen.add(message.id);
  const li = document.createElement('li');
  li.dataset.id = String(message.id);
  li.textContent = `${message.name} · ${message.created_at}: ${message.message}`;
  // REST 이력과 WebSocket이 엇갈려 도착해도 ID 순서를 유지합니다.
  const next = [...el('messages').children].find(item => Number(item.dataset.id) > message.id);
  el('messages').insertBefore(li, next || null);
}
async function refresh() {
  const rooms = await api('/chat/rooms');
  el('rooms').replaceChildren();
  for (const item of rooms) {
    const li = document.createElement('li'), button = document.createElement('button');
    button.textContent = item.title;
    button.onclick = () => enter(item).catch(showError);
    li.append(button); el('rooms').append(li);
  }
}
async function enter(item) {
  if (room !== null) await leave();
  await api(`/chat/rooms/${item.id}/join`, 'POST');
  room = item.id; seen = new Set(); el('messages').replaceChildren();
  el('room-title').textContent = item.title; el('leave').disabled = false;
  const current = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/chat/rooms/${room}/ws`);
  socket = current;
  current.onmessage = event => { if (socket !== current) return; const data = JSON.parse(event.data); data.type === 'message' ? add(data) : showError(data.detail); };
  current.onopen = async () => {
    if (socket !== current) return;
    el('send').disabled = false; el('status').textContent = '연결됨';
    try {
      let after = 0;
      while (socket === current) {
        const rows = await api(`/chat/rooms/${item.id}/messages?after=${after}`);
        if (socket !== current) return;
        rows.forEach(add);
        if (rows.length < 100) break;
        after = rows[rows.length - 1].id;
      }
    } catch (error) { showError(error); }
  };
  current.onclose = () => { if (socket === current) { el('send').disabled = true; el('status').textContent = '연결 종료. 방을 다시 선택해 주세요.'; } };
  current.onerror = () => showError('연결 실패. 세션과 서버 상태를 확인해주세요.');
}
async function leave() {
  if (room === null) return;
  await api(`/chat/rooms/${room}/leave`, 'POST');
  socket?.close(); socket = null; room = null;
  el('leave').disabled = true; el('send').disabled = true;
  el('status').textContent = '방에서 나왔습니다.';
}
el('refresh').onclick = () => refresh().catch(showError);
el('leave').onclick = () => leave().catch(showError);
el('create-room').onsubmit = async event => {
  event.preventDefault();
  const title = new FormData(event.target).get('title');
  try { const result = await api('/chat/rooms', 'POST', {title}); await refresh(); await enter({id: result.id, title}); } catch (error) { showError(error); }
};
el('send-message').onsubmit = event => {
  event.preventDefault();
  if (socket?.readyState !== WebSocket.OPEN) return showError('먼저 방에 연결해주세요.');
  socket.send(JSON.stringify({message: new FormData(event.target).get('message')}));
  event.target.reset();
};
refresh().catch(showError);
