import unittest
import urllib.error
from unittest.mock import patch

import check_source_freshness as m


class SourceFreshnessTests(unittest.TestCase):
    def test_extracts_unique_http_links_without_fragments(self):
        markdown = '[one](https://example.org/data#part) [again](https://example.org/data#other) [local](README.md)'
        self.assertEqual(m.extract_urls(markdown), ['https://example.org/data'])

    def test_reports_material_http_and_etag_changes(self):
        previous = [
            {'url': 'https://a.example', 'status': 200, 'etag': 'old'},
            {'url': 'https://b.example', 'status': 200, 'etag': None},
        ]
        current = [
            {'url': 'https://a.example', 'status': 200, 'etag': 'new'},
            {'url': 'https://b.example', 'status': 404, 'etag': None},
        ]
        self.assertEqual(m.diff_records(previous, current), [
            {'url': 'https://a.example', 'changes': {'etag': {'before': 'old', 'after': 'new'}}},
            {'url': 'https://b.example', 'changes': {'status': {'before': 200, 'after': 404}}},
        ])

    def test_live_request_uses_a_certificate_context(self):
        class Response:
            status = 200
            headers = {'ETag': 'v1'}

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        def open_with_context(request, timeout, context):
            self.assertIsNotNone(context)
            return Response()

        with patch.object(m.urllib.request, 'urlopen', side_effect=open_with_context):
            result = m.inspect_url('https://example.org')
        self.assertEqual(result['status'], 200)

    def test_retries_head_rejection_with_bounded_get(self):
        class Response:
            status = 200
            headers = {'Content-Length': '42'}

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        rejected = urllib.error.HTTPError('https://example.org', 405, 'method', {}, None)
        with patch.object(m.urllib.request, 'urlopen', side_effect=[rejected, Response()]) as opened:
            result = m.inspect_url('https://example.org')
        self.assertEqual(result['status'], 200)
        self.assertEqual(opened.call_args_list[1].args[0].method, 'GET')


if __name__ == '__main__':
    unittest.main()
