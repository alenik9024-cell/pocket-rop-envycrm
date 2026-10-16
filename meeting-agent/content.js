(() => {
  const isTelemost = location.hostname === 'telemost.yandex.ru' && location.pathname.startsWith('/j/');
  const isCrm = location.hostname === 'novikov.envycrm.com';
  const storageKey = 'meetingAgentContext';
  let recorder;
  let stream;
  let sessionId;

  const setContext = (context) => chrome.storage.local.set({ [storageKey]: context });
  const getContext = () => new Promise(resolve => chrome.storage.local.get(storageKey, result => resolve(result[storageKey] || null)));

  function panel(title, text) {
    const old = document.getElementById('meeting-agent-panel');
    if (old) old.remove();
    const root = document.createElement('section');
    root.id = 'meeting-agent-panel';
    root.innerHTML = `<h3>${title}</h3><p>${text}</p><div id="meeting-agent-fields"></div><div id="meeting-agent-status"></div>`;
    document.documentElement.appendChild(root);
    return root;
  }
  function status(root, message, error = false) {
    const node = root.querySelector('#meeting-agent-status');
    node.textContent = message;
    node.className = error ? 'error' : '';
  }
  function backend() {
    return new Promise(resolve => chrome.runtime.sendMessage({ type: 'meeting-agent-get-config' }, result => resolve((result?.meetingAgentBackend || 'http://127.0.0.1:8000').replace(/\/$/, ''))));
  }

  async function saveCrmContext() {
    let context;
    try { context = MeetingAgentUtils.contextFromLocation(location); }
    catch (error) { const root = panel('Meeting Agent', 'Контекст запуска не сохранён.'); status(root, error.message, true); return; }
    if (!context) return;
    await setContext(context);
    // CRM context is stored silently; the visible control belongs in Telemost only.

  }

  async function showTelemostPanel() {
    let current;
    try { current = MeetingAgentUtils.parseTelemostUrl(location.href); }
    catch (error) { return; }
    const context = await getContext();
    const root = panel('Транскрипция встречи', 'Транскрипция активируется вашим нажатием; браузер может отдельно запросить техническое разрешение на аудио.');
    const fields = root.querySelector('#meeting-agent-fields');
    const dealInput = document.createElement('input');
    dealInput.type = 'number'; dealInput.min = '1'; dealInput.placeholder = 'deal_id';
    if (context?.meetingId === current.meetingId) dealInput.value = context.dealId;
    const label = document.createElement('label'); label.textContent = 'CRM deal_id'; label.append(dealInput); fields.append(label);
    const start = document.createElement('button'); start.textContent = 'Начать транскрипцию'; fields.append(start);
    const stop = document.createElement('button'); stop.textContent = 'Остановить'; stop.className = 'secondary'; stop.disabled = true; fields.append(stop);
    if (!context || context.meetingId !== current.meetingId) status(root, 'Произвольная ссылка не содержит CRM-сделку. Введите deal_id или откройте ссылку из CRM.', true);

    start.addEventListener('click', async () => {
      start.disabled = true;
      try {
        const dealId = Number(dealInput.value);
        if (!Number.isInteger(dealId) || dealId <= 0) throw new Error('Введите положительный deal_id.');
        const api = await backend();
        const response = await fetch(`${api}/api/meetings/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ deal_id: dealId, telemost_url: current.url }) });
        const registered = await response.json();
        if (!response.ok) throw new Error(registered.error || 'Не удалось зарегистрировать встречу.');
        // getDisplayMedia is intentionally inside this click handler: no hidden or automatic capture.
        stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
        const audioTracks = stream.getAudioTracks();
        if (!audioTracks.length) throw new Error('Браузер не вернул аудиодорожку. Выберите вкладку Telemost и включите звук.');
        const audioOnly = new MediaStream(audioTracks);
        sessionId = registered.id;
        const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : 'audio/webm';
        recorder = new MediaRecorder(audioOnly, { mimeType: mime });
        const chunks = [];
        recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
        recorder.onstop = async () => {
          stream?.getTracks().forEach(track => track.stop());
          stream = null;
          stop.disabled = true;
          status(root, 'Обрабатываю встречу локально…');
          try {
            const blob = new Blob(chunks, { type: mime });
            const bytes = new Uint8Array(await blob.arrayBuffer());
            let binary = '';
            for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
            const result = await fetch(`${api}/api/meetings/${sessionId}/audio`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ audio_base64: btoa(binary), format: 'webm' }) });
            const payload = await result.json();
            if (!result.ok) throw new Error(payload.error || 'Не удалось сформировать резюме.');
            status(root, 'Резюме и договорённости сохранены в сделке. Аудио и стенограмма удалены.');
          } catch (error) {
            status(root, error.message || 'Не удалось обработать встречу.', true);
          }
        };        recorder.start(1000);
        stop.disabled = false;
        status(root, `Транскрипция активна. Сессия ${registered.id.slice(0, 8)}…`);
      } catch (error) {
        stream?.getTracks().forEach(track => track.stop()); stream = null; start.disabled = false;
        status(root, error.message || 'Запись не запущена.', true);
      }
    });
    stop.addEventListener('click', () => { if (recorder && recorder.state !== 'inactive') recorder.stop(); stop.disabled = true; start.disabled = false; });
  }
  if (isCrm) saveCrmContext();
  if (isTelemost) showTelemostPanel();
})();
