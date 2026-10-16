import unittest

import server


class NextTaskEvidenceTests(unittest.TestCase):
    def test_crm_task_and_messenger_are_visible_as_evidence(self):
        events = server.normalize_envycrm_logs([
            {'type_id': 2006, 'created_at': '2026-10-18', 'data': {'next_time': '2026-10-19 23:59:59', 'close_task': False, 'comment': 'Повторный контакт'}},
            {'type_id': 2012, 'created_at': '2026-10-18', 'data': {'messenger': {'source': {'integrationName': 'макс', 'service': 'max'}, 'message': 'Клиент просит написать завтра'}, 'text': None}}
        ])
        self.assertEqual(events[0]['category'], 'task')
        self.assertIn('2026-10-19', events[0]['content'])
        self.assertEqual(events[1]['category'], 'message')
        self.assertIn('MAX', events[1]['channel'])
        self.assertIn('Клиент просит', events[1]['content'])

    def test_no_contact_panel_is_short_and_has_next_call_script(self):
        result = server.no_contact_policy('Абонент занят и не может ответить')
        self.assertLessEqual(len(result['recommendation']), 180)
        self.assertIn('next_call_script', result)
        self.assertLessEqual(len(result['next_call_script']), 3)
        self.assertTrue(result['next_call_script'][0]['phrase'])


if __name__ == '__main__':
    unittest.main()
