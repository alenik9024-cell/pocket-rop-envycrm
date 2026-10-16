import json
import unittest
from unittest.mock import patch

import server


class ActionPlanTests(unittest.TestCase):
    def test_audit_requires_manager_steps_for_successful_deal(self):
        response = {
            'status': 'yellow', 'status_text': 'НАРУШЕНИЕ СКРИПТА',
            'analysis': 'Нужно уточнить следующий шаг.', 'recommendation': 'Вернуть сделку в работу.',
            'outcome': 'Нужен контроль', 'priority': 'medium', 'evidence': [], 'card_gaps': [],
            'communication_summary': {},
            'next_actions': [
                {'action': 'Получить контакт', 'deadline': 'сегодня', 'success_metric': 'Контакт подтвержден', 'owner': 'Менеджер', 'channel': 'звонок', 'phrase': 'Добрый день, удобно говорить?', 'acceptance': 'Клиент ответил'}
            ],
        }
        with patch.object(server, 'ai_request') as request:
            request.return_value = {'choices': [{'message': {'content': json.dumps(response)}}]}
            result = server.analyze_deal_evidence({'id': 1}, {'status': 'available', 'events': []})
        self.assertEqual(len(result['next_actions']), 1)
        self.assertIn('owner', result['next_actions'][0])
        self.assertIn('phrase', result['next_actions'][0])
        self.assertIn('acceptance', result['next_actions'][0])

    def test_action_plan_is_deterministic_for_no_contact(self):
        result = server.no_contact_policy('Абонент занят и не может ответить')
        self.assertEqual(result['next_actions'][0]['owner'], 'Менеджер')
        self.assertEqual(result['next_actions'][0]['channel'], 'CRM-очередь')
        self.assertIn('не перезванивать сразу', result['next_actions'][0]['action'].lower())


if __name__ == '__main__':
    unittest.main()
