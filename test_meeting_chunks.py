import unittest
import tempfile
from pathlib import Path
import server

class MeetingChunkTests(unittest.TestCase):
    def test_chunks_append_and_consume(self):
        with tempfile.TemporaryDirectory() as d:
            old = tempfile.gettempdir
            tempfile.gettempdir = lambda: d
            try:
                sid = 'a' * 32
                self.assertEqual(server.append_meeting_chunk(sid, b'one'), 3)
                self.assertEqual(server.append_meeting_chunk(sid, b'two'), 6)
                self.assertEqual(server.consume_meeting_chunks(sid), b'onetwo')
                self.assertFalse(server.meeting_chunk_path(sid).exists())
            finally:
                tempfile.gettempdir = old

if __name__ == '__main__': unittest.main()
