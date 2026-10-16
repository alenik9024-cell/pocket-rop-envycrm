(() => {
  const HOST = 'telemost.yandex.ru';
  function parseTelemostUrl(value) {
    const url = new URL(String(value || '').trim());
    if (url.protocol !== 'https:' || url.hostname !== HOST || !/^\/j\/[A-Za-z0-9_-]+$/.test(url.pathname)) {
      throw new Error('Нужна ссылка Telemost вида https://telemost.yandex.ru/j/<id>.');
    }
    url.hash = '';
    return { url: url.toString(), meetingId: url.pathname.slice(3) };
  }
  function contextFromLocation(locationLike) {
    const params = new URL(locationLike.href).searchParams;
    const dealId = params.get('deal_id') || params.get('dealId');
    const telemostUrl = params.get('telemost_url') || params.get('telemostUrl');
    if (!dealId && !telemostUrl) return null;
    if (!/^\d+$/.test(String(dealId || '')) || Number(dealId) <= 0) throw new Error('deal_id должен быть положительным числом.');
    const parsed = parseTelemostUrl(telemostUrl);
    return { dealId: Number(dealId), telemostUrl: parsed.url, meetingId: parsed.meetingId };
  }
  globalThis.MeetingAgentUtils = { parseTelemostUrl, contextFromLocation };
})();
