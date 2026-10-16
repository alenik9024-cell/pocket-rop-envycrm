import json
import unittest
from unittest.mock import patch

import server


class EvidenceAnalysisTests(unittest.TestCase):
    def test_timeline_extracts_message_email_and_card_evidence(self):
        events = server.normalize_envycrm_logs([
            {'type_id': 2010, 'created_at': '2026-10-01T10:00:00',
             'data': {'comment': 'Клиент просит прислать КП на client@example.com'}},
            {'type_id': 2001, 'created_at': '2026-10-01T11:00:00',
             'data': {'subject': 'КП', 'body': 'Отправили предложение, ждём ответа'}},
            {'type_id': 9999, 'created_at': '2026-10-01T12:00:00',
             'data': {'task': 'Позвонить завтра'}}
        ])
        self.assertEqual([event['category'] for event in events], ['message', 'email', 'task'])
        self.assertIn('[скрыто]', events[0]['content'])
        self.assertEqual(events[1]['content'], 'КП\nОтправили предложение, ждём ответа')

    def test_unified_analysis_sends_card_timeline_and_optional_transcript(self):
        response = {
            'status': 'yellow', 'status_text': 'НАРУШЕНИЕ СКРИПТА',
            'analysis': 'Не зафиксирован следующий шаг.',
            'recommendation': 'Назначить контакт.', 'outcome': 'Нужен контроль',
            'priority': 'medium', 'evidence': ['В истории нет подтверждения даты'],
            'card_gaps': ['Не заполнен бюджет'], 'communication_summary': {'call': 0, 'message': 1, 'email': 1, 'task': 1},
            'next_actions': [{'action': 'Уточнить бюджет', 'deadline': 'сегодня', 'success_metric': 'Поле заполнено', 'owner': 'Менеджер', 'channel': 'звонок', 'phrase': 'Уточните бюджет', 'acceptance': 'Бюджет подтвержден'}]
        }
        with patch.object(server, 'ai_request') as request:
            request.return_value = {'choices': [{'message': {'content': json.dumps(response)}}]}
            result = server.analyze_deal_evidence(
                {'id': 1, 'stage': 'Новый', 'fields': [{'name': 'Бюджет', 'value': ''}]},
                {'status': 'available', 'events': [{'category': 'message', 'content': 'Текст'}]},
                transcript=None,
            )
        sent = request.call_args.args[0]
        user_text = sent[1]['content']
        self.assertIn('Карточка сделки', user_text)
        self.assertIn('История коммуникаций', user_text)
        self.assertNotIn('None', user_text)
        self.assertEqual(result['evidence_mode'], 'card_and_communications')

    def test_no_recording_does_not_block_analysis(self):
        with patch.object(server, 'ai_request') as request:
            request.return_value = {'choices': [{'message': {'content': json.dumps({
                'status': 'yellow', 'status_text': 'НАРУШЕНИЕ СКРИПТА',
                'analysis': 'Недостаточно данных.', 'recommendation': 'Запросить контакт.',
                'outcome': 'Нужен контроль', 'priority': 'medium', 'evidence': [],
                'card_gaps': [], 'communication_summary': {}, 'next_actions': []
            })}}]}
            result = server.analyze_deal_evidence({'id': 1}, {'status': 'available', 'events': []})
        self.assertEqual(result['call_audit_status'], 'not_available')
        self.assertEqual(result['evidence_mode'], 'card_only')


if __name__ == '__main__':
    unittest.main()
