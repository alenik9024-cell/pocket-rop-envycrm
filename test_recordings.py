import unittest
from email.message import Message
from unittest.mock import MagicMock, patch

import server


class RecordingTests(unittest.TestCase):
    path = '/api/callrecords/telphin/abc123'
    origin = 'https://novikov.envycrm.com'

    def test_extensionless_links(self):
        for value in (self.path, self.origin + self.path):
            with self.subTest(value=value):
                self.assertEqual(server.recording_reference(value), value)
                self.assertEqual(server.recording_reference({'nested': [value]}), value)

    def test_json_log_data(self):
        events = server.normalize_envycrm_logs([{
            'type_id': 2009,
            'data': '{"record_url": "%s", "duration": 60, "status": 1}' % self.path,
        }])
        self.assertEqual(events[0]['_recording_url'], self.path)
        self.assertEqual(events[0]['duration_seconds'], 60)

    def test_recording_link_is_not_discarded_without_duration_metadata(self):
        timeline = {
            'status': 'available',
            'events': [{
                'occurred_at': '2026-10-01T12:00:00',
                'status': 'unknown',
                '_recording_url': self.path,
            }],
        }
        self.assertEqual(server.call_recording_from_timeline(timeline), self.path)

    def test_download_without_credentials(self):
        response = MagicMock()
        response.headers = Message()
        response.headers['Content-Type'] = 'audio/mpeg'
        response.read.return_value = b'audio'
        response.__enter__.return_value = response
        with patch.object(server, 'urlopen', return_value=response) as opener:
            result = server.fetch_call_recording(self.path + '?api_key=old', {
                'base_url': self.origin + '/openapi/v1', 'api_key': 'secret',
            })
        self.assertEqual(result, (b'audio', 'mp3'))
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, self.origin + self.path)
        self.assertIsNone(request.get_header('Cookie'))
        self.assertIsNone(request.get_header('Authorization'))

    def test_http_and_foreign_host_rejected(self):
        with patch.object(server, 'urlopen') as opener:
            for origin in ('http://novikov.envycrm.com', 'https://example.org'):
                with self.subTest(origin=origin), self.assertRaises(RuntimeError):
                    server.fetch_call_recording(origin + self.path, {
                        'base_url': self.origin + '/openapi/v1', 'api_key': 'secret',
                    })
            opener.assert_not_called()


if __name__ == '__main__':
    unittest.main()