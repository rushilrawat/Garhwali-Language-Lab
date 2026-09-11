import importlib.util
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name('collect_online.py')


class CollectionTests(unittest.TestCase):
    def load(self):
        self.assertTrue(MODULE.exists(), 'Online collector has not been implemented')
        spec = importlib.util.spec_from_file_location('collect_online', MODULE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_failed_validation_preserves_previous_source(self):
        mod = self.load()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'source.jsonl'
            p.write_text('previous\n')
            with self.assertRaises(ValueError):
                mod.save_records(p, [{'record_id': 'x', 'text_original': ''}])
            self.assertEqual(p.read_text(), 'previous\n')

    def test_duplicate_identifiers_are_rejected(self):
        mod = self.load()
        r = mod.make_record('test', '1', 'गढ़वाली', {'raw_path': 'a', 'sha256': 'b'},
                            'CC-BY-4.0', 'https://creativecommons.org/licenses/by/4.0/', 'test')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                mod.save_records(Path(d) / 'x.jsonl', [r, r])

    def test_wiktionary_extracts_only_garhwali_section(self):
        mod = self.load()
        text = '==Hindi==\nHindi text\n==Garhwali==\n===Noun===\n# water\n==Nepali==\nNepali text'
        self.assertEqual(mod.garhwali_section(text), '===Noun===\n# water')

    def test_transcript_keeps_upstream_split_and_is_unreviewed(self):
        mod = self.load()
        row = {'iso_639_3': 'gbm', 'raw_text': 'मि ठीक छौं।', 'speaker_id': '12',
               'prompt_id': 'p1', 'segment_id': 's1', 'duration': 4.2}
        rec = mod.meta_record(row, 'test', 0, {'raw_path': 'x', 'sha256': 'y'})
        self.assertEqual(rec['split'], 'test')
        self.assertFalse(rec['native_reviewed'])
        self.assertFalse(rec['training_eligible'])
        self.assertEqual(rec['text_original'], row['raw_text'])
        with self.assertRaises(ValueError):
            mod.meta_record(dict(row, iso_639_3='hin'), 'test', 0, {})

    def test_benchmark_train_named_split_still_cannot_train(self):
        mod = self.load()
        self.assertTrue(hasattr(mod, 'benchmark_record'), 'Benchmark isolation not implemented')
        row = {'lang': 'gbm', 'question': 'कन छा तुम?', 'translated_answers': [{'text': 'ठीक'}]}
        rec = mod.benchmark_record('xorqa', row, 'train', 0, {'raw_path': 'x', 'sha256': 'y'}, 'canary')
        self.assertEqual(rec['split'], 'train')
        self.assertEqual(rec['usage'], 'evaluation_only')
        self.assertFalse(rec['training_eligible'])

    def test_paharili_label_is_parsed_from_final_tab(self):
        mod = self.load()
        text, label = mod.paharili_line('गढ़वाली वाक्य\tgbm\n')
        self.assertEqual(text, 'गढ़वाली वाक्य')
        self.assertEqual(label, 'gbm')
        with self.assertRaises(ValueError):
            mod.paharili_line('unlabeled sentence')

    def test_madlad_clean_extract_skips_known_exact_text(self):
        mod = self.load()
        duplicate = 'पहले से मौजूद गढ़वाली दस्तावेज।'
        novel = 'नौ दस्तावेज गढ़वाली मा च।'
        payload = gzip.compress(('\n'.join([
            json.dumps({'text': duplicate}, ensure_ascii=False),
            json.dumps({'text': novel}, ensure_ascii=False),
        ]) + '\n').encode())
        known = {hashlib.sha256(duplicate.encode()).hexdigest()}
        rows, duplicate_count = mod.madlad_clean_records(
            payload, {'raw_path': 'x', 'sha256': 'y', 'dataset_revision': 'z'}, known)
        self.assertEqual(duplicate_count, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['text_normalized'], novel)
        self.assertEqual(rows[0]['corpus_layer'], 'experimental')
        self.assertFalse(rows[0]['training_eligible'])
        self.assertIn('component_rights_review_required', rows[0]['quality_flags'])
        self.assertLessEqual(rows[0]['quality_metrics']['devanagari_share_of_nonspace'], 1)

    def test_cldf_numeral_extractors_keep_only_garhwali_rows(self):
        mod = self.load()
        info = {'raw_path': 'x.csv', 'sha256': 'y'}
        sand = ('ID,Language_ID,Parameter_ID,Value,Form,Source\n'
                'Garhwali-1,Garhwali,1_one,ek,ek,mephd2021\n'
                'Hindi-1,Hindi,1_one,ek,ek,source\n').encode()
        rows = mod.sand_garhwali_records(sand, info)
        self.assertEqual([row['text_normalized'] for row in rows], ['ek'])
        self.assertEqual(rows[0]['parameter_id'], '1_one')
        self.assertEqual(rows[0]['corpus_layer'], 'core_open')

        chan = ('ID,Language_ID,Parameter_ID,Value,Form,Source\n'
                'garh1243-2-1,garh1243-2,1,ek,ek,chan2019\n'
                'garh1243-1-1,garh1243-1,1,ak,ak,chan2019\n').encode()
        rows = mod.chan_garhwali_records(chan, info)
        self.assertEqual([row['record_id'] for row in rows], ['chan_numerals_garhwali:garh1243-2-1'])

    def test_mamta_examples_are_distinct_from_numeral_values(self):
        mod = self.load()
        info = {'raw_path': 'x.csv', 'sha256': 'y'}
        values = ('ID,Language_ID,Parameter_ID,Value,Source,Example_IDs\n'
                  '1-garh1243,garh1243,1,ek,,garh1243-oneboy\n').encode()
        examples = ('ID,Language_ID,Primary_Text,Translated_Text\n'
                    'garh1243-oneboy,garh1243,ek ləɖkɑ,one boy\n').encode()
        value_rows, example_rows = mod.mamta_garhwali_records(values, info, examples, info)
        self.assertEqual(value_rows[0]['genre'], 'numeral_lexicon')
        self.assertEqual(example_rows[0]['genre'], 'translated_example')
        self.assertEqual(example_rows[0]['translation'], 'one boy')

    def test_lsi_cldf_records_are_marked_as_historical_derivatives(self):
        mod = self.load()
        info = {'raw_path': 'forms.csv', 'sha256': 'z'}
        data = ('ID,Language_ID,Parameter_ID,Value,Form,Source\n'
                'GARHWALI-one,GARHWALI,one,ek,ek,Grierson1916\n'
                'HINDI-one,HINDI,one,ek,ek,Grierson1916\n').encode()
        rows = mod.lsi_cldf_garhwali_records(data, info)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]['historical'])
        self.assertEqual(rows[0]['corpus_layer'], 'historical_review')
        self.assertIn('structured_derivative_of_existing_lsi_ocr', rows[0]['quality_flags'])

    def test_obs_parser_extracts_text_and_ignores_images_and_scripts(self):
        mod = self.load()
        page = '''<html><script>ignore me</script><div id="content">
        <div class="mt"><span>कथा</span></div>
        <div class="s"><div>शीर्षक</div></div>
        <div class="p"><img src="x.jpg"/>पहलो वाक्य।</div>
        <div class="pmr">स्रोत</div></div></html>'''.encode()
        blocks = mod.obs_text_blocks(page)
        self.assertEqual(blocks, ['\u0915\u0925\u093e', '\u0936\u0940\u0930\u094d\u0937\u0915', '\u092a\u0939\u0932\u094b \u0935\u093e\u0915\u094d\u092f\u0964', '\u0938\u094d\u0930\u094b\u0924'])

    def test_obs_record_stays_in_noncommercial_sharealike_layer(self):
        mod = self.load()
        page = '<div id="content"><div class="mt">कथा</div><div class="p">गढ़वाली पाठ।</div></div>'.encode()
        record = mod.obs_garhwali_record(7, page, {'raw_path': 'story.html', 'sha256': 'x'})
        self.assertEqual(record['record_id'], 'obs_garhwali:007')
        self.assertEqual(record['license_id'], 'CC-BY-NC-SA-4.0')
        self.assertEqual(record['corpus_layer'], 'restricted_nc_sa')
        self.assertIn('item_page_has_no_license_block', record['quality_flags'])
        self.assertEqual(record['story_number'], 7)

    def test_djvu_word_pages_preserve_page_boundaries(self):
        mod = self.load()
        xml = b'''<DJVUXML><BODY><OBJECT><PAGECOLUMN><REGION><PARAGRAPH><LINE>
        <WORD>first</WORD><WORD>page</WORD></LINE></PARAGRAPH></REGION></PAGECOLUMN></OBJECT>
        <OBJECT><PAGECOLUMN><REGION><PARAGRAPH><LINE><WORD>second</WORD></LINE>
        <LINE><WORD>line</WORD></LINE></PARAGRAPH></REGION></PAGECOLUMN></OBJECT></BODY></DJVUXML>'''
        self.assertEqual(mod.djvu_word_pages(xml), ['first page', 'second\nline'])

    def test_scholarly_manifest_distinguishes_full_text_from_access_challenge(self):
        mod = self.load()
        sources = mod.scholarly_open_sources()
        self.assertEqual(len(sources), 5)
        self.assertEqual(len({source['source_id'] for source in sources}), 5)
        self.assertTrue(all(source['license_id'].startswith('CC-') for source in sources))
        montaut = next(source for source in sources if source['source_id'] == 'scholarly_montaut_2022')
        self.assertEqual(montaut['local_access_status'], 'automated_full_text_blocked_by_anubis_challenge')
        self.assertEqual(montaut['disposition'], 'catalogued_open_license_access_challenge')
        self.assertTrue(all('access-challenge response' in artifact for artifact in montaut['artifacts']))

    def test_cultural_chunks_keep_only_garhwal_context_and_page_identity(self):
        mod = self.load()
        text = ('unrelated first page' + '\f' +
                'A Garhwal village account with enough cultural context to retain as evidence.' + '\f' +
                'unrelated last page')
        chunks = mod.cultural_chunks(text, terms=('garhwal',), source_kind='page')
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['source_unit'], 2)
        self.assertIn('Garhwal village', chunks[0]['text'])

    def test_cultural_record_is_reference_only(self):
        mod = self.load()
        record = mod.cultural_record(
            'test_culture', 'p1', 'Garhwal ritual account.',
            {'raw_path': 'x', 'sha256': 'y'}, 'Public-Domain',
            'https://creativecommons.org/publicdomain/mark/1.0/', 'Test attribution',
            cultural_genres=['ritual'])
        self.assertEqual(record['iso_639_3'], 'eng')
        self.assertEqual(record['corpus_layer'], 'cultural_reference')
        self.assertFalse(record['training_eligible'])

    def test_thematic_parser_keeps_tables_and_block_lines(self):
        mod = self.load()
        parser = mod.TableAndLineParser()
        parser.feed('<div>Bird - पक्षी - चखुल</div><table><tr><th>Hindi</th><th>Garhwali</th></tr><tr><td>पेड़</td><td>डाळु</td></tr></table>')
        self.assertIn('Bird - पक्षी - चखुल', parser.lines())
        self.assertEqual(parser.rows[-1], ['पेड़', 'डाळु'])

    def test_thematic_variants_remove_transliteration_and_notes(self):
        mod = self.load()
        self.assertEqual(mod.devanagari_variants('चखुलि (cakhuli), चखुल/चखुलु (?)'),
                         ['चखुलि', 'चखुल', 'चखुलु'])


if __name__ == '__main__':
    unittest.main()
