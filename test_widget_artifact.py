import unittest
from pathlib import Path


class WidgetArtifactTests(unittest.TestCase):
    def test_widget_uses_envycrm_api_and_next_action(self):
        html = (Path(__file__).parent / 'widget.html').read_text(encoding='utf-8')
        self.assertIn('envycrmwidget.min.js', html)
        self.assertIn('EnvyCrmWidget.getDeal', html)
        self.assertIn('/api/pocket/deals/', html)
        self.assertIn('next_actions', html)

    def test_outer_extension_initializes_crm_window(self):
        html = (Path(__file__).parent / 'extension.html').read_text(encoding='utf-8')
        self.assertIn('EnvyCrmWidget.init', html)
        self.assertIn("'before-deal-task'", html)
        self.assertIn("type: 'iframe'", html)
        self.assertIn('widget.html', html)


if __name__ == '__main__':
    unittest.main()
