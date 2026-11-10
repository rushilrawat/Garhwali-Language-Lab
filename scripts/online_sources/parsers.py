"""Pure parsers that turn downloaded source payloads into corpus records."""

import html
import json
import gzip
import re
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import quote
from wikitext_plain import to_plain_text
from online_sources.records import BY, SA, csv_dict_rows, latin_record, make_record, sha


class GenericTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skipped = 0

    def handle_starttag(self, tag, _attrs):
        if tag in ('script', 'style'):
            self.skipped += 1
        elif tag in ('p', 'li', 'h1', 'h2', 'h3', 'br') and not self.skipped:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skipped:
            self.skipped -= 1
        elif tag in ('p', 'li', 'h1', 'h2', 'h3') and not self.skipped:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.skipped:
            self.parts.append(data)

    def text(self):
        value = html.unescape(''.join(self.parts))
        value = re.sub(r'[ \t]+', ' ', value)
        return re.sub(r'\n{3,}', '\n\n', value).strip()


class OBSTextParser(HTMLParser):
    TARGET_CLASSES = {'mt', 's', 'p', 'pmr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.div_depth = 0
        self.content_depth = None
        self.capture_depth = None
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            self.div_depth += 1
            if self.content_depth is None and attrs.get('id') == 'content':
                self.content_depth = self.div_depth
            elif self.content_depth is not None and self.capture_depth is None:
                classes = set(attrs.get('class', '').split())
                if classes & self.TARGET_CLASSES:
                    self.capture_depth = self.div_depth
                    self.parts = []
        elif tag == 'br' and self.capture_depth is not None:
            self.parts.append(' ')

    def handle_data(self, data):
        if self.capture_depth is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag != 'div':
            return
        if self.capture_depth == self.div_depth:
            text = ' '.join(''.join(self.parts).split())
            if text and text != '&nbsp;':
                self.blocks.append(text)
            self.capture_depth = None
            self.parts = []
        if self.content_depth == self.div_depth:
            self.content_depth = None
        self.div_depth -= 1


class TableAndLineParser(HTMLParser):
    """Retain table cells and visual block boundaries from vocabulary pages."""

    def __init__(self):
        super().__init__()
        self.parts, self.rows = [], []
        self.row = self.cell = None
        self.skipped = 0

    def handle_starttag(self, tag, _attrs):
        if tag in ('script', 'style'):
            self.skipped += 1
        elif not self.skipped:
            if tag in ('div', 'p', 'li', 'br', 'tr'):
                self.parts.append('\n')
            if tag == 'tr':
                self.row = []
            elif tag in ('td', 'th') and self.row is not None:
                self.cell = []

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skipped:
            self.skipped -= 1
        elif not self.skipped:
            if tag in ('td', 'th') and self.cell is not None:
                self.row.append(re.sub(r'\s+', ' ', ''.join(self.cell)).strip())
                self.cell = None
            elif tag == 'tr' and self.row is not None:
                if self.row:
                    self.rows.append(self.row)
                self.row = None
            if tag in ('div', 'p', 'li', 'tr'):
                self.parts.append('\n')

    def handle_data(self, data):
        if not self.skipped:
            self.parts.append(data)
            if self.cell is not None:
                self.cell.append(data)

    def lines(self):
        value = html.unescape(''.join(self.parts))
        return [re.sub(r'\s+', ' ', line).strip()
                for line in value.splitlines() if line.strip()]


def sand_garhwali_records(data, info, parameters_data=None,
                          parameters_info=None):
    parameters = {
        item['ID']: item for item in csv_dict_rows(parameters_data)
    } if parameters_data else {}
    rows = []
    for item in csv_dict_rows(data):
        if item.get('Language_ID') != 'Garhwali':
            continue
        parameter = parameters.get(item.get('Parameter_ID'), {})
        rows.append(latin_record(
            'sand_garhwali', item['ID'], item.get('Form') or item['Value'], info,
            'South Asian Numeral Database contributors; source mephd2021; Numeralbank editors',
            corpus_layer='core_open', genre='numeral_lexicon', modality='text',
            parameter_id=item.get('Parameter_ID'), value=item.get('Value'),
            english_gloss=parameter.get('Name'),
            concepticon_id=parameter.get('Concepticon_ID'),
            concepticon_gloss=parameter.get('Concepticon_Gloss'),
            parameter_table_provenance=parameters_info,
            segments=item.get('Segments'), source_bibliography=item.get('Source'),
            source_url='https://github.com/numeralbank/sand/tree/v1.0',
            rights_evidence='https://zenodo.org/records/15463198'))
    return rows


def chan_garhwali_records(data, info):
    rows = []
    for item in csv_dict_rows(data):
        if item.get('Language_ID') != 'garh1243-2':
            continue
        rows.append(latin_record(
            'chan_numerals_garhwali', item['ID'], item.get('Form') or item['Value'], info,
            'Eugene Chan numeral data; Numeralbank CLDF editors',
            corpus_layer='core_open', genre='numeral_lexicon', modality='text',
            parameter_id=item.get('Parameter_ID'), value=item.get('Value'),
            segments=item.get('Segments'), other_form=item.get('Other_Form'),
            variant_id=item.get('Variant_ID'), source_bibliography=item.get('Source'),
            upstream_language_id=item.get('Language_ID'),
            source_url='https://github.com/numeralbank/channumerals/tree/v1.0.2',
            rights_evidence='https://zenodo.org/records/15654191'))
    return rows


def mamta_garhwali_records(values_data, values_info, examples_data, examples_info):
    values = []
    for item in csv_dict_rows(values_data):
        if item.get('Language_ID') != 'garh1243':
            continue
        values.append(latin_record(
            'mamta_southasia_values', item['ID'], item['Value'], values_info,
            'Special Numerals in South Asian Languages contributors and CLDF editors',
            corpus_layer='reference_open', genre='numeral_lexicon', modality='text',
            parameter_id=item.get('Parameter_ID'), example_ids=item.get('Example_IDs'),
            source_url='https://github.com/cldf-datasets/mamtasouthasia/tree/v1.0',
            rights_evidence='https://zenodo.org/records/17985722'))
    examples = []
    for item in csv_dict_rows(examples_data):
        if item.get('Language_ID') != 'garh1243':
            continue
        examples.append(latin_record(
            'mamta_southasia_examples', item['ID'], item['Primary_Text'], examples_info,
            'Special Numerals in South Asian Languages contributors and CLDF editors',
            corpus_layer='core_open', genre='translated_example', modality='text',
            analyzed_word=item.get('Analyzed_Word'), gloss=item.get('Gloss'),
            translation=item.get('Translated_Text'), lgr_conformance=item.get('LGR_Conformance'),
            source_url='https://github.com/cldf-datasets/mamtasouthasia/tree/v1.0',
            rights_evidence='https://zenodo.org/records/17985722'))
    return values, examples


def lsi_cldf_garhwali_records(data, info, parameters_data=None,
                              parameters_info=None):
    parameters = {
        item['ID']: item for item in csv_dict_rows(parameters_data)
    } if parameters_data else {}
    rows = []
    for item in csv_dict_rows(data):
        if item.get('Language_ID') != 'GARHWALI':
            continue
        parameter = parameters.get(item.get('Parameter_ID'), {})
        record = latin_record(
            'lsi_cldf_garhwali', item['ID'], item.get('Form') or item['Value'], info,
            'George A. Grierson, Linguistic Survey of India; Lexibank CLDF editors',
            corpus_layer='historical_review', genre='historical_lexicon', modality='text',
            parameter_id=item.get('Parameter_ID'), value=item.get('Value'),
            english_gloss=parameter.get('Name'),
            concepticon_id=parameter.get('Concepticon_ID'),
            concepticon_gloss=parameter.get('Concepticon_Gloss'),
            parameter_table_provenance=parameters_info,
            segments=item.get('Segments'), source_bibliography=item.get('Source'),
            source_url='https://github.com/lexibank/lsi/tree/v1.0',
            rights_evidence='https://zenodo.org/records/8361936',
            quality_flags=['structured_derivative_of_existing_lsi_ocr',
                           'source_level_duplicate_expected'])
        record['historical'] = True
        rows.append(record)
    return rows


def obs_text_blocks(data):
    parser = OBSTextParser()
    parser.feed(data.decode('utf-8'))
    return parser.blocks


def obs_garhwali_record(story_number, data, info):
    blocks = obs_text_blocks(data)
    if len(blocks) < 2:
        raise ValueError(f'Open Bible Story {story_number} has too little text')
    text_value = '\n\n'.join(blocks)
    devanagari = sum('\u0900' <= char <= '\u097f' for char in text_value)
    alphabetic = sum(char.isalpha() for char in text_value)
    if alphabetic == 0 or devanagari / alphabetic < 0.5:
        raise ValueError(f'Open Bible Story {story_number} is not predominantly Devanagari')
    return make_record(
        'obs_garhwali', f'{story_number:03d}', text_value, info,
        'CC-BY-SA-4.0', 'https://creativecommons.org/licenses/by-sa/4.0/',
        'Open Bible Stories — Garhwali (gbm), OBS-TLF v1 (2026-06-26), aggregated by the unfoldingWord OBS Library project; text-only extraction from the TLF umbrella OBS Android app. CC BY-SA 4.0. Audio and Sweet Publishing illustrations are excluded.',
        corpus_layer='licensed_sharealike', genre='religious_narrative', modality='text',
        story_number=story_number,
        source_url=f'https://media.ipsapps.org/in/osa/stories/36-Garhwali-{story_number:03d}.html',
        rights_evidence='https://openbiblestories.org/l/gbm/; https://git.door43.org/OBS-TLF/gbm_obs/releases/tag/v1',
        rights_status='upstream_openbiblestories_declares_CC_BY_SA_4; v1_2026_06_26; text_only',
        quality_flags=['translation_quality_unreviewed', 'illustrations_excluded'])


def djvu_word_pages(data):
    root = ET.fromstring(data)
    pages = []
    for page in root.findall('.//OBJECT'):
        lines = []
        for line in page.findall('.//LINE'):
            text = ' '.join((word.text or '').strip() for word in line.findall('WORD')).strip()
            if text:
                lines.append(text)
        pages.append('\n'.join(lines))
    return pages


def garhwali_section(text):
    match = re.search(r'^==\s*Garhwali\s*==\s*\n(.*?)(?=^==[^=]|\Z)', text, re.M | re.S)
    return match.group(1).strip() if match else ''


def plain_wikitext(text):
    """Render the small Wiktionary subset used for glosses and examples."""
    previous = None
    while text != previous:
        previous = text
        text = re.sub(r'\{\{[^{}]*\}\}', ' ', text)
    text = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'<[^>]*>', ' ', text)
    text = text.replace("'''", '').replace("''", '')
    return re.sub(r'\s+', ' ', html.unescape(text)).strip(' ;,')


def wiktionary_page_records(page, info):
    """Extract Garhwali values instead of treating English wikitext as corpus text."""
    title = page['title']
    if not re.search(r'[\u0900-\u097f]', title):
        return []
    revision = page['revisions'][0]
    section = garhwali_section(revision['slots']['main']['*'])
    if not section:
        return []
    source_url = f'https://en.wiktionary.org/w/index.php?oldid={revision["revid"]}'
    attribution = (
        'English Wiktionary contributors; '
        f'https://en.wiktionary.org/w/index.php?title={quote(title)}&action=history'
    )
    glosses = []
    for line in section.splitlines():
        if line.startswith('# ') and not line.startswith('#:'):
            gloss = plain_wikitext(line[2:])
            if gloss and gloss not in glosses:
                glosses.append(gloss)
    common = dict(
        corpus_layer='core_open', modality='text',
        source_url=source_url, rights_evidence=source_url,
        revision_id=revision['revid'], text_format='structured_wiktionary',
    )
    rows = [make_record(
        'wiktionary_en', f'{page["pageid"]}:lemma', title, info,
        'CC-BY-SA-4.0', SA, attribution,
        genre='lexicon', english_gloss='; '.join(glosses), **common,
    )]
    seen_values = {title}
    alternative_sections = re.findall(
        r'^=+Alternative forms=+\s*\n(.*?)(?=^={3,}[^=]|\Z)',
        section, re.M | re.S,
    )
    alternative_index = 0
    for alternative_section in alternative_sections:
        for match in re.finditer(r'\{\{(?:alter|l)\|gbm\|([^{}]+)\}\}', alternative_section):
            for value in match.group(1).split('|'):
                value = plain_wikitext(value)
                if ('=' in value or value in seen_values
                        or not re.search(r'[\u0900-\u097f]', value)):
                    continue
                seen_values.add(value)
                alternative_index += 1
                rows.append(make_record(
                    'wiktionary_en', f'{page["pageid"]}:alternative:{alternative_index}',
                    value, info, 'CC-BY-SA-4.0', SA, attribution,
                    genre='lexicon', english_gloss='; '.join(glosses),
                    relation='alternative_form', headword=title, **common,
                ))
    usage_index = 0
    for line in section.splitlines():
        match = re.search(r'\{\{(?:ux|usex)\|gbm\|(.+)\}\}', line)
        if not match:
            continue
        fields = match.group(1).split('|', 1)
        example = plain_wikitext(fields[0])
        translation = plain_wikitext(fields[1]) if len(fields) > 1 else ''
        if not example or not re.search(r'[\u0900-\u097f]', example):
            continue
        usage_index += 1
        rows.append(make_record(
            'wiktionary_en', f'{page["pageid"]}:usage:{usage_index}', example, info,
            'CC-BY-SA-4.0', SA, attribution,
            genre='sentence', translation=translation, **common,
        ))
    return rows


def incubator_wiktionary_records(payload, info):
    rows = []
    for page in payload['query']['pages'].values():
        revision = page['revisions'][0]
        raw = revision['slots']['main']['*']
        if not raw.strip() or re.match(r'^\s*#redirect', raw, re.I):
            continue
        text = to_plain_text(raw)
        if not text:
            continue
        rows.append(make_record(
            'incubator_wt', page['pageid'], text, info, 'CC-BY-SA-4.0', SA,
            'Wikimedia Incubator contributors; '
            f'https://incubator.wikimedia.org/w/index.php?title={quote(page["title"])}&action=history',
            title=page['title'], revision_id=revision['revid'], corpus_layer='core_open',
            item_url=f'https://incubator.wikimedia.org/w/index.php?oldid={revision["revid"]}',
            text_format='plain_text_from_wikitext', source_text_format='wikitext',
            genre='lexicon', modality='text', quality_flags=['mechanically_rendered_wikitext'],
        ))
    return rows


def meta_record(row, split, index, info):
    if row.get('iso_639_3') != 'gbm':
        raise ValueError('Non-Garhwali row in Garhwali configuration')
    key = ':'.join(str(row.get(k, '')) for k in ('speaker_id', 'prompt_id', 'segment_id'))
    return make_record('meta_omni', key, row['raw_text'], info, 'CC-BY-4.0', BY,
                       'Meta Omnilingual ASR Corpus contributors; see saved upstream dataset card',
                       split=split, upstream_row_index=index, speaker_id=row.get('speaker_id'),
                       prompt_id=row.get('prompt_id'), prompt=row.get('prompt'),
                       segment_id=row.get('segment_id'), duration_seconds=row.get('duration'),
                       modality='speech_transcript', genre='prompted_speech', corpus_layer='core_open',
                       source_url='https://huggingface.co/datasets/facebook/omnilingual-asr-corpus',
                       rights_status='upstream_meta_cc_by_4_0',
                       rights_evidence='sources/online/meta_omni/card.md.metadata.json',
                       audio_downloaded=False)


def benchmark_record(kind, row, split, index, info, canary):
    licenses = {'flores': ('CC-BY-SA-4.0', SA),
                'xorqa': ('MIT', 'https://opensource.org/license/mit'),
                'crosssum': ('CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/')}
    if row.get('lang', 'gbm') != 'gbm':
        raise ValueError('Wrong benchmark language')
    text = row['source'] if kind == 'flores' else row['question'] if kind == 'xorqa' else row['summary']
    rec = make_record('indicgenbench_' + kind, f'{split}:{index}', text, info, *licenses[kind],
                       'Singh et al. (2024), Google IndicGenBench; upstream dataset card and source example retained',
                       split=split, usage='evaluation_only', benchmark_canary=canary,
                       source_example=row, corpus_layer='evaluation_only', genre=kind, modality='text',
                       rights_status='upstream_declared_license; component_rights_review_before_redistribution')
    return rec


def indic_asr_record(row, row_index, info):
    if row.get('language') != 'garhwali' or not row.get('sentence', '').strip():
        raise ValueError(f'Unexpected Garhwali ASR row {row_index}')

    upstream_source = row.get('source') or 'not_reported'
    source_url = 'https://huggingface.co/datasets/grushaaaaa/indic-dialect-asr'
    rights_status = 'dataset_declares_CC_BY_4; source_component_and_consent_review_pending'
    rights_evidence = None
    quality_flags = [
        'community_aggregation', 'possible_upstream_duplicate',
        'source_lineage_review_required',
    ]
    attribution = f'Indic Dialect ASR by grushaaaaa; declared source: {upstream_source}'

    if upstream_source.startswith('Vaani/'):
        rights_status = 'upstream_vaani_cc_by_4_0'
        rights_evidence = 'https://vaani.iisc.ac.in/dataset/Version1'
        attribution = (
            'Project VAANI, IISc/ARTPARK; transcript accessed via '
            'grushaaaaa/indic-dialect-asr'
        )
        quality_flags.remove('source_lineage_review_required')
    elif upstream_source == 'facebook/omnilingual-asr-corpus':
        rights_status = 'upstream_meta_cc_by_4_0'
        rights_evidence = 'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus'
        attribution = (
            'AI at Meta, Omnilingual ASR Corpus; transcript accessed via '
            'grushaaaaa/indic-dialect-asr'
        )
        quality_flags.remove('source_lineage_review_required')

    return make_record(
        'indic_dialect_asr_gbm', row_index, row['sentence'], info,
        'CC-BY-4.0', BY, attribution,
        split='train', upstream_row_index=row_index,
        upstream_source=upstream_source,
        usage='all_data_experimental_user_approved', corpus_layer='experimental',
        experimental_training_eligible=True, genre='speech_transcript',
        modality='speech_transcript', audio_referenced=True,
        source_url=source_url, rights_status=rights_status,
        rights_evidence=rights_evidence, quality_flags=quality_flags,
    )


def paharili_line(line):
    fields = line.rstrip('\n').rsplit('\t', 1)
    if len(fields) != 2 or not fields[0].strip() or not re.fullmatch(r'[a-z]{3}', fields[1]):
        raise ValueError('Malformed PahariLI labeled sentence')
    return fields[0], fields[1]


def madlad_clean_records(raw, info, known_hashes):
    """Extract novel clean Garhwali documents while retaining conservative rights flags."""
    rows = []
    duplicate_rows = 0
    seen = set(known_hashes)
    for index, line in enumerate(gzip.decompress(raw).decode().splitlines()):
        item = json.loads(line)
        if set(item) != {'text'} or not item['text'].strip():
            raise ValueError(f'Unexpected MADLAD Garhwali row {index}')
        normalized = unicodedata.normalize('NFC', item['text']).strip()
        digest = sha(normalized.encode())
        if digest in seen:
            duplicate_rows += 1
            continue
        seen.add(digest)
        devanagari = sum('\u0900' <= char <= '\u097f' for char in normalized)
        alphabetic = sum(char.isalpha() for char in normalized)
        nonspace = sum(not char.isspace() for char in normalized)
        copyright_marker = bool(re.search(r'copyright|©|all rights reserved', normalized, re.I))
        flags = ['common_crawl', 'dataset_clean_partition',
                 'component_rights_review_required', 'source_url_removed']
        if copyright_marker:
            flags.append('copyright_notice_detected')
        rows.append(make_record(
            'madlad400_gbm_clean', index, item['text'], info,
            'ODC-BY-1.0-database-only', 'https://opendatacommons.org/licenses/by/1-0/',
            'Kudugunta et al. (2023), MADLAD-400; original web authors retain component rights',
            upstream_row=index, upstream_split='clean', dataset_revision=info.get('dataset_revision'),
            usage='all_data_experimental_user_approved', corpus_layer='experimental',
            experimental_training_eligible=True, genre='web_document',
            modality='text', source_url='https://huggingface.co/datasets/allenai/MADLAD-400',
            rights_status='ODC_BY_1_covers_database; underlying_page_copyrights_not_cleared',
            quality_flags=flags,
            quality_metrics={'characters': len(normalized), 'alphabetic_characters': alphabetic,
                             'devanagari_characters': devanagari,
                             'devanagari_share_of_nonspace': round(devanagari / nonspace, 4)
                             if nonspace else 0,
                             'line_count': len(normalized.splitlines()),
                             'copyright_marker': copyright_marker}))
    return rows, duplicate_rows


def madlad_provenance(info):
    """Attach the immutable dataset revision to downloaded file provenance."""
    enriched = dict(info)
    enriched['dataset_revision'] = '9d886a76bd8fa69b294f2dd3843dacb8388ee5a5'
    enriched['upstream_partition_sha256'] = '6516174f88d38e5c6db032a3e3d83d002e20a34df0f02f52c9188884b6bb6999'
    return enriched
