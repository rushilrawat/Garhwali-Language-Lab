"""Declarative registry of online source waves and scholarly source decisions."""

from online_sources.records import BY, SA


def scholarly_open_sources():
    """Rights-audited scholarship used as reference material, never corpus rows."""
    return [
        {
            'source_id': 'acl_dialect_matters',
            'title': 'Dialect Matters: Cross-Lingual ASR Transfer for Low-Resource Indic Language Varieties',
            'authors': ['Akriti Dhasmana', 'Aarohi Srivastava', 'David Chiang'],
            'year': 2026,
            'topic': 'Garhwali ASR, code-mixing, dialect transfer, and error analysis',
            'landing_page': 'https://aclanthology.org/2026.vardial-1.12/',
            'license_id': 'CC-BY-4.0',
            'license_url': BY,
            'license_evidence': 'https://aclanthology.org/faq/copyright/',
            'artifacts': ['landing.html', 'paper.pdf', 'copyright.html'],
            'disposition': 'open_research_reference',
        },
        {
            'source_id': 'scholarly_montaut_2022',
            'title': "On the Non-Lexical Categories of avyay 'Invariables' and Their Grammaticalization in Pahari Languages, with a Comparison to Standard Hindi",
            'authors': ['Annie Montaut'],
            'year': 2022,
            'topic': 'Garhwali and Kumaoni adpositions, case marking, particles, and grammaticalization',
            'landing_page': 'https://hasp.ub.uni-heidelberg.de/catalog/book/919',
            'license_id': 'CC-BY-SA-4.0',
            'license_url': SA,
            'license_evidence': 'https://hasp.ub.uni-heidelberg.de/catalog/book/919',
            'artifacts': [
                'book.html (access-challenge response)',
                'chapter.html (access-challenge response)',
            ],
            'local_access_status': 'automated_full_text_blocked_by_anubis_challenge',
            'disposition': 'catalogued_open_license_access_challenge',
        },
        {
            'source_id': 'scholarly_sahu_2023',
            'title': 'Preserving the Linguistic Diversity of Uttarakhand: Role of Language and Education Policies',
            'authors': ['Preety Sahu'],
            'year': 2023,
            'topic': 'Garhwali language vitality, education, policy, and intergenerational transmission',
            'landing_page': 'https://www.journals.asianresassoc.org/index.php/ijll/article/view/1194',
            'license_id': 'CC-BY-4.0',
            'license_url': BY,
            'license_evidence': 'https://www.journals.asianresassoc.org/index.php/ijll/article/view/1194',
            'artifacts': ['landing.html', 'paper.pdf'],
            'disposition': 'open_research_reference',
        },
        {
            'source_id': 'scholarly_uniyal_2019',
            'title': 'English-Garhwali SMT System – Development and Evaluation',
            'authors': ['Arushi Uniyal'],
            'year': 2019,
            'topic': 'English-Garhwali parallel corpora, statistical MT, evaluation, and error categories',
            'landing_page': 'https://www.researchpublish.com/papers/english-garhwali-smt-system--development-and-evaluation',
            'license_id': 'CC-BY-NC-3.0',
            'license_url': 'https://creativecommons.org/licenses/by-nc/3.0/',
            'license_evidence': 'https://www.researchpublish.com/papers/english-garhwali-smt-system--development-and-evaluation',
            'artifacts': ['landing.html', 'paper.pdf'],
            'disposition': 'restricted_noncommercial_research_reference',
        },
        {
            'source_id': 'scholarly_stronski_2010',
            'title': 'Non-Nominative Subjects in Rajasthani and Central Pahari: The Status of the Ergative and Obligatory Constructions',
            'authors': ['Krzysztof Stroński'],
            'year': 2010,
            'topic': 'Central Pahari split ergativity, obligation, and non-nominative subjects',
            'landing_page': 'https://pressto.amu.edu.pl/index.php/linpo/article/view/v10122-010-0007-9',
            'license_id': 'CC-BY-NC-ND-4.0',
            'license_url': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
            'license_evidence': 'https://pressto.amu.edu.pl/index.php/linpo/article/view/v10122-010-0007-9',
            'artifacts': ['landing.html', 'paper.pdf'],
            'disposition': 'unaltered_noncommercial_research_reference',
        },
    ]


# Graph-managed ingestion waves: wave name -> (acquire action, extract action)
# in collect_online.py. ingestion_graph.py reads this table; add a wave by
# defining both actions in collect_online.py and registering them here.
WAVES = {
    'fourth': ('fourth_wave_acquire', 'fourth_wave_extract'),
    'fifth': ('fifth_wave_acquire', 'fifth_wave_extract'),
    'sixth': ('sixth_wave_acquire', 'sixth_wave_extract'),
    'seventh': ('seventh_wave_acquire', 'seventh_wave_extract'),
    'eighth': ('eighth_wave_acquire', 'eighth_wave_extract'),
    'ninth': ('ninth_wave_acquire', 'ninth_wave_extract'),
    'tenth': ('tenth_wave_acquire', 'tenth_wave_extract'),
}
