import unittest


class IngestionGraphTests(unittest.TestCase):
    def test_wave_mapping_rejects_unknown_wave(self):
        import ingestion_graph as module

        self.assertEqual(module.wave_actions('fourth'), ('fourth_wave_acquire', 'fourth_wave_extract'))
        self.assertEqual(module.wave_actions('seventh'), ('seventh_wave_acquire', 'seventh_wave_extract'))
        self.assertEqual(module.wave_actions('eighth'), ('eighth_wave_acquire', 'eighth_wave_extract'))
        self.assertEqual(module.wave_actions('ninth'), ('ninth_wave_acquire', 'ninth_wave_extract'))
        with self.assertRaises(ValueError):
            module.wave_actions('unknown')

    def test_transient_acquisition_errors_are_retryable(self):
        import ingestion_graph as module

        self.assertTrue(module.retryable_acquisition_error(RuntimeError('HTTP 429')))
        self.assertTrue(module.retryable_acquisition_error(RuntimeError('HTTP 504')))
        self.assertTrue(module.retryable_acquisition_error(RuntimeError('operation timed out')))
        self.assertFalse(module.retryable_acquisition_error(RuntimeError('HTTP 404')))
        self.assertFalse(module.retryable_acquisition_error(ValueError('bad schema')))

    def test_graph_runs_pipeline_in_order_and_records_completion(self):
        import ingestion_graph as module
        from langgraph.checkpoint.memory import InMemorySaver

        calls = []

        def acquire(wave):
            calls.append(('acquire', wave))

        def extract(wave):
            calls.append(('extract', wave))

        def dedup():
            calls.append(('dedup', None))

        def verify():
            calls.append(('verify', None))

        graph = module.build_ingestion_graph(
            acquire=acquire,
            extract=extract,
            dedup=dedup,
            verify=verify,
            checkpointer=InMemorySaver(),
        )
        state = graph.invoke(
            {'wave': 'fourth', 'completed_steps': []},
            {'configurable': {'thread_id': 'test-run'}},
        )

        self.assertEqual(calls, [
            ('acquire', 'fourth'),
            ('extract', 'fourth'),
            ('dedup', None),
            ('verify', None),
        ])
        self.assertEqual(state['completed_steps'], ['acquire', 'extract', 'dedup', 'verify'])
        self.assertEqual(state['status'], 'complete')


if __name__ == '__main__':
    unittest.main()
