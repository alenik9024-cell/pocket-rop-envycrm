chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ meetingAgentBackend: 'https://rop-193-124-65-29.sslip.io' });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === 'meeting-agent-get-config') {
    chrome.storage.local.get({ meetingAgentBackend: 'https://rop-193-124-65-29.sslip.io' }, sendResponse);
    return true;
  }
});
