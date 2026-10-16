# Telemost Meeting Agent MVP

This is a deliberately small Chrome/Chromium MV3 scaffold. The product persists only structured meeting summaries and agreements. It does **not** persist audio, recordings, or a full transcript.

## Install

1. Start the project server (`python server.py`) or set the backend URL in `background.js` / extension storage.
2. Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select this `meeting-agent/` directory.
3. In the CRM, open a launch URL containing both values:

   `https://novikov.envycrm.com/...?...&deal_id=42&telemost_url=https%3A%2F%2Ftelemost.yandex.ru%2Fj%2Fabc-123`

   The content script validates and stores this context locally, then offers the Telemost link.
4. Open the Telemost link. The panel shows **Транскрипция встречи**. Enter/verify `deal_id` and click **Начать транскрипцию**. The browser may still show its technical media picker; to obtain tab audio, select the Telemost tab and enable audio there.
5. Click **Остановить** when finished. This scaffold has no transcription/AI transport yet: temporary audio chunks are discarded from memory when stopped and no audio file is written.

The button is a technical user gesture required by browser media APIs, not a business-consent workflow.

## Backend registry

- `POST /api/meetings/register` with `{ "deal_id": 42, "telemost_url": "https://telemost.yandex.ru/j/abc-123" }`
- `GET /api/meetings/{session_id}`
- `POST /api/meetings/{session_id}/summary` with `{ "summary": "...", "agreements": ["..."] }`
- `GET /api/meetings/{session_id}/summary`
- `DELETE /api/meetings/{session_id}` for explicit retention cleanup

The server validates HTTPS, the exact `telemost.yandex.ru` host, and `/j/<id>` path, then stores the deal mapping in SQLite. Summary storage contains only structured summary text and agreement bullets. There is no multipart audio endpoint in this MVP and no credential or secret in the extension.

## Data-retention policy

- Audio is transient only: it must remain in the browser's in-memory `MediaRecorder` chunks during processing and be released immediately after successful transcription/AI summary. This scaffold discards it on stop because the processing pipeline is not connected.
- Audio, recordings, and full transcripts are not persisted by the extension or backend.
- Structured summary and agreements are retained until the explicit `DELETE /api/meetings/{session_id}` cleanup call. Automatic cleanup is intentionally not implied.
- A production transcriber must implement success/failure cleanup in a `finally` path and must not add audio persistence as a fallback.

## Explicit limitations

- An arbitrary Telemost URL cannot infer a CRM deal. The deal mapping must arrive from the CRM launch context or be entered by the user.
- `getDisplayMedia()` is intentionally called only from the visible button click. Browser permission and tab-selection UI remain mandatory.
- Browser support varies: a video capture stream may contain no audio track, especially when the wrong picker target is selected. The panel reports this rather than silently claiming a recording.
- The optional multipart audio endpoint and server-side upload/transcription pipeline are not part of this MVP.
- The extension is a scaffold, not a production security boundary. Review host permissions, authentication, retention, and HTTPS deployment before wider use.
