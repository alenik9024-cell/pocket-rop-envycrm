import unittest
from server import normalize_envycrm_logs


class StageEvidenceTests(unittest.TestCase):
    def test_completed_video_meeting_stage_is_preserved_as_evidence(self):
        logs = [{
            'id': 1, 'type_id': 2006,
            'data': {
                'btn': {'name': 'Видеовстреча проведена'},
                'old_stage': {'name': 'Видеовстреча назначена'},
                'new_stage': {'name': 'Видеовстреча проведена'},
                'comment': 'Написать резюме встречи',
            },
            'created_at': '2026-09-29 19:16:56',
        }]
        event = normalize_envycrm_logs(logs)[0]
        self.assertIn('Видеовстреча проведена', event['content'])
        self.assertIn('video_meeting_completed', event['evidence'])


if __name__ == '__main__':
    unittest.main()
