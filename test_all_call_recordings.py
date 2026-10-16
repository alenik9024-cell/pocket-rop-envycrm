import unittest
from server import call_recordings_from_timeline


class AllCallRecordingsTests(unittest.TestCase):
    def test_returns_all_unique_recordings_in_chronological_order(self):
        timeline = {'status': 'available', 'events': [
            {'category': 'call', 'occurred_at': '2026-01-02', '_recording_url': 'https://novikov.envycrm.com/api/callrecords/telphin/2'},
            {'category': 'call', 'occurred_at': '2026-01-01', '_recording_url': 'https://novikov.envycrm.com/api/callrecords/telphin/1'},
            {'category': 'call', 'occurred_at': '2026-01-03', '_recording_url': 'https://novikov.envycrm.com/api/callrecords/telphin/2'},
        ]}
        result = call_recordings_from_timeline(timeline)
        self.assertEqual([item[1] for item in result], [
            'https://novikov.envycrm.com/api/callrecords/telphin/1',
            'https://novikov.envycrm.com/api/callrecords/telphin/2',
        ])


if __name__ == '__main__':
    unittest.main()
