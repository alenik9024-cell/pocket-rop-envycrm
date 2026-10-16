import json
import unittest
from unittest.mock import patch

import server


class NoContactAnalysisTests(unittest.TestCase):
    def test_short_busy_call_is_not_treated_as_sales_failure(self):
        ai_response = {
            'status': 'yellow', 'status_text': 'НАРУШЕНИЕ СКРИПТА',
            'analysis': 'Нет контакта.', 'recommendation': 'Не звонить повторно сразу.',
            'outcome': 'Нужен контроль', 'priority': 'medium',
            'evidence': ['Абонент занят'], 'card_gaps': ['Нет данных о клиенте'],
            'communication_summary': {}, 'next_actions': [],
        }
        timeline = {'status': 'available', 'events': [{'category': 'call', 'status': 'answered', 'duration_seconds': 8}]}
        with patch.object(server, 'ai_request') as request:
            request.return_value = {'choices': [{'message': {'content': json.dumps(ai_response)}}]}
            result = server.analyze_deal_evidence(
                {'id': 1, 'name': 'Сделка', 'fields': []}, timeline,
                'К сожалению, абонент занят и не может ответить на звонок.',
            )
        self.assertEqual(result['contact_status'], 'no_contact')
        self.assertEqual(result['outcome'], 'Норма')
        self.assertEqual(result['priority'], 'low')
        self.assertEqual(result['next_contact_policy'], 'do_not_redial_immediately')
        self.assertEqual(result['card_gaps'], [])
        self.assertIn('не состоялся', result['analysis'].lower())

    def test_no_contact_policy_is_not_a_spam_instruction(self):
        result = server.no_contact_policy('Абонент занят и не может ответить')
        self.assertEqual(result['contact_status'], 'no_contact')
        self.assertEqual(result['next_contact_policy'], 'do_not_redial_immediately')
        self.assertIn('не делать повторный звонок', result['recommendation'].lower())


if __name__ == '__main__':
    unittest.main()
