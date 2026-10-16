import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import server


class CallPipelineTests(unittest.TestCase):
    def report(self):
        return {'status': 'green', 'status_text': 'УСПЕШНО',
                'checklist': {'crm_fields': False, 'valid_rejection': False,
                              'time_control': 'Не подтверждено', 'kp_sent': 'Не подтверждено'},
                'closing_steps': ['Уточнить бюджет', 'Предложить встречу', 'Согласовать счет'],
                'rop_instruction': 'Уточните дату следующего контакта.'}

    def test_local_model_cached_and_audio_deleted(self):
        engine = MagicMock()
        paths = []

        def recognize(path, language):
            self.assertEqual(language, 'ru')
            self.assertEqual(Path(path).read_bytes(), b'audio')
            paths.append(path)
            return iter([SimpleNamespace(text=' Диалог ')]), SimpleNamespace(duration=61)

        engine.transcribe.side_effect = recognize
        factory = MagicMock(return_value=engine)
        with patch.object(server.importlib.util, 'find_spec', return_value=True), \
                patch.dict('sys.modules', {'faster_whisper': SimpleNamespace(WhisperModel=factory)}), \
                patch.dict(server.os.environ, {'LOCAL_WHISPER_MODEL': 'base'}), \
                patch.object(server, 'LOCAL_WHISPER_MODELS', {}), \
                patch.object(server, 'fetch_call_recording', return_value=(b'audio', 'mp3')), \
                patch.object(server, 'ai_transcribe') as external:
            for _ in range(2):
                self.assertEqual(server.transcribe_audio('/record'), ('Диалог', 61))
            factory.assert_called_once_with('base', device='auto', compute_type='int8')
            external.assert_not_called()
        self.assertTrue(all(not Path(path).exists() for path in paths))

    def test_external_fallback_and_duration_boundary(self):
        with patch.object(server.importlib.util, 'find_spec', return_value=None), \
                patch.object(server, 'fetch_call_recording', return_value=(b'audio', 'mp3')), \
                patch.object(server.shutil, 'which', return_value=None), \
                patch.object(server, 'ai_transcribe') as external:
            for duration in (None, 0):
                external.return_value = ('Текст', duration)
                with self.subTest(duration=duration), self.assertRaises(RuntimeError):
                    server.transcribe_audio('/record')
            external.return_value = ('Текст', 1)
            self.assertEqual(server.transcribe_audio('/record'), ('Текст', 1))
            external.assert_called_with((b'audio', 'mp3'), with_metadata=True)

    def test_transcript_survives_analysis_failure(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(server, 'REVIEW_DB_PATH', Path(directory) / 'reviews.sqlite3'), \
                patch.object(server, 'transcribe_audio', return_value=('Текст', 60)) as transcribe:
            server.initialize_review_store()
            text = server.transcript_for_deal('/record', 1, 'project', {})
            with patch.object(server, 'ai_request', side_effect=RuntimeError('Unavailable')):
                with self.assertRaises(RuntimeError):
                    server.analyze_with_internal_ai({}, {}, text)
            self.assertEqual(server.transcript_for_deal('/record', 1, 'project', {}), text)
            transcribe.assert_called_once()

    def test_text_only_and_schema_validation(self):
        with patch.object(server, 'ai_request') as request:
            request.return_value = {'choices': [{'message': {'content': json.dumps(self.report())}}]}
            result = server.analyze_with_internal_ai({'secret': 'CRM'}, {}, 'Диалог')
            self.assertEqual(request.call_args.args[0][1], {'role': 'user', 'content': 'Диалог'})
            self.assertEqual(result['transcript'], 'Диалог')
            invalid = self.report()
            invalid['closing_steps'] = ['Только один шаг']
            request.return_value = {'choices': [{'message': {'content': json.dumps(invalid)}}]}
            with self.assertRaises(RuntimeError):
                server.analyze_with_internal_ai({}, {}, 'Диалог')

    def test_economical_model_fallback(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'{"choices": []}'
        with patch.object(server, 'AI_MODEL', 'gpt-6-sol'), \
                patch.object(server, 'AI_API_KEY', 'test-key'), \
                patch.object(server, 'ai_chat_completions_url', return_value='https://clodex.xyz/v1/chat/completions'), \
                patch.object(server, 'urlopen', side_effect=[HTTPError('url', 503, 'Unavailable', {}, None), response]) as request:
            server.ai_request([{'role': 'user', 'content': 'Текст'}])
            models = [json.loads(call.args[0].data)['model'] for call in request.call_args_list]
            self.assertEqual(models, ['gpt-6-sol', 'gpt-6-luna'])


if __name__ == '__main__':
    unittest.main()