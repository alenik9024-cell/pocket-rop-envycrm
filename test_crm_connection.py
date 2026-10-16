import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

import server


class CRMConnectionTests(unittest.TestCase):
    def test_read_retries_temporary_connection_failure(self):
        for method, endpoint in [('GET', '/main/data'), ('POST', '/deal/list')]:
            with self.subTest(endpoint=endpoint):
                response = MagicMock()
                response.__enter__.return_value = response
                response.read.return_value = b'{}'
                request = Request('https://example.org' + endpoint, method=method)
                with patch.object(server, 'urlopen', side_effect=[URLError('timeout'), response]) as opener, patch.object(server.time, 'sleep'):
                    self.assertEqual(server.read_crm_response(request, endpoint), b'{}')
                    self.assertEqual(opener.call_count, 2)

    def test_persistent_timeout_is_bounded(self):
        request = Request('https://example.org/main/data')
        with patch.object(server, 'urlopen', side_effect=TimeoutError()) as opener, patch.object(server.time, 'sleep'):
            with self.assertRaises(TimeoutError):
                server.read_crm_response(request, '/main/data')
            self.assertEqual(opener.call_count, 2)

    def test_write_is_not_retried(self):
        request = Request('https://example.org/deal/log/create', method='POST')
        with patch.object(server, 'urlopen', side_effect=URLError('timeout')) as opener:
            with self.assertRaises(URLError):
                server.read_crm_response(request, '/deal/log/create')
            opener.assert_called_once()

    def test_http_error_is_not_retried(self):
        request = Request('https://example.org/main/data')
        error = HTTPError(request.full_url, 401, 'Unauthorized', {}, None)
        with patch.object(server, 'urlopen', side_effect=error) as opener:
            with self.assertRaises(HTTPError):
                server.read_crm_response(request, '/main/data')
            opener.assert_called_once()


if __name__ == '__main__':
    unittest.main()