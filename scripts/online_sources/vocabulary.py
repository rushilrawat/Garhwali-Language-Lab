"""Cultural-passage selection and themed-vocabulary tagging."""

import re
from online_sources.records import make_record


CULTURAL_TERMS = (
    'garhwal', 'garhwál', 'garhwâl', 'garhwalí', 'garhwali', 'gurhwal', 'gurwal',
    'गढ़वाल', 'गढ़वाली', 'गढ़वाल', 'गढ़वाली',
)


def cultural_chunks(text, terms=CULTURAL_TERMS, source_kind='page'):
    """Select page- or paragraph-level cultural evidence without copying whole books."""
    if source_kind == 'page':
        if '\f' in text:
            units = text.split('\f')
        else:
            paragraphs = re.split(r'\n\s*\n', text)
            units = []
            current = []
            current_size = 0
            for paragraph in paragraphs:
                if current and current_size + len(paragraph) > 6000:
                    units.append('\n\n'.join(current))
                    current = []
                    current_size = 0
                current.append(paragraph)
                current_size += len(paragraph)
            if current:
                units.append('\n\n'.join(current))
    elif source_kind == 'passage':
        units = re.split(r'\n\s*\n', text)
    else:
        raise ValueError(f'Unknown cultural source kind: {source_kind}')
    selected = []
    lowered_terms = tuple(term.casefold() for term in terms)
    for index, unit in enumerate(units, 1):
        cleaned = re.sub(r'[ \t]+', ' ', unit)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        if len(cleaned) < 40:
            continue
        folded = cleaned.casefold()
        if any(term in folded for term in lowered_terms):
            selected.append({'source_unit': index, 'text': cleaned})
    return selected


def cultural_genres(text):
    vocabulary = {
        'folk_narrative': ('folklore', 'folk-lore', 'legend', 'tale', 'story', 'myth', 'गाथा', 'कथा'),
        'performance': ('song', 'ballad', 'dance', 'drum', 'theatre', 'play', 'गीत', 'नाटक', 'नृत्य', 'ढोल'),
        'ritual_religion': ('ritual', 'worship', 'deity', 'god', 'goddess', 'shrine', 'temple', 'पूजा', 'देव', 'मंदिर'),
        'social_custom': ('marriage', 'custom', 'caste', 'festival', 'fair', 'विवाह', 'रीति', 'त्योहार', 'मेला'),
        'material_culture': ('food', 'dress', 'house', 'craft', 'agriculture', 'crop', 'भोजन', 'वेश', 'शिल्प', 'कृषि'),
        'language_literature': ('language', 'dialect', 'proverb', 'poem', 'literature', 'भाषा', 'बोली', 'कहावत', 'कविता'),
        'place_history': ('history', 'king', 'village', 'district', 'इतिहास', 'राजा', 'गांव', 'जिला'),
    }
    folded = text.casefold()
    labels = [label for label, markers in vocabulary.items()
              if any(marker.casefold() in folded for marker in markers)]
    return labels or ['general_cultural_context']


def cultural_record(source, key, text, info, license_id, license_url, attribution, **extra):
    record = make_record(source, key, text, info, license_id, license_url, attribution, **extra)
    record.update(iso_639_3='eng', script='Latn', corpus_layer='cultural_reference',
                  usage='research_context_only', historical=True, training_eligible=False)
    return record


THEMED_DOMAINS = {
    'bird': {'bird', 'pigeon', 'kite', 'eagle', 'vulture', 'partridge', 'hen',
             'sparrow', 'monal', 'crow', 'cuckoo', 'owl', 'starling', 'blackbird'},
    'animal': {'animal', 'fish', 'dog', 'snake', 'worm', 'cow', 'buffalo', 'goat',
               'sheep', 'ape', 'fox', 'lizard', 'rat', 'ox', 'horse', 'cat', 'tiger',
               'frog', 'bear', 'jackal', 'deer', 'elephant', 'monkey', 'mule', 'kid',
               'calf', 'snail', 'earthworm', 'crab', 'porcupine', 'leopard'},
    'insect': {'insect', 'fly', 'louse', 'leech', 'firefly', 'nit', 'locust',
               'cricket', 'scorpion', 'ant', 'bug', 'cockroach', 'flea', 'honeybee'},
    'plant_nature': {'tree', 'forest', 'fruit', 'seed', 'leaf', 'root', 'bark',
                     'flower', 'grass', 'sun', 'moon', 'star', 'water', 'rain',
                     'river', 'lake', 'sea', 'stone', 'sand', 'earth', 'cloud',
                     'fog', 'sky', 'wind', 'snow', 'ice'},
    'body': {'skin', 'meat', 'blood', 'bone', 'fat', 'egg', 'horn', 'tail', 'feather',
             'hair', 'head', 'ear', 'eye', 'nose', 'mouth', 'tooth', 'tongue',
             'fingernail', 'foot', 'leg', 'knee', 'hand', 'wing', 'belly', 'guts',
             'neck', 'back', 'breast', 'heart', 'liver'},
    'kinship_people': {'woman', 'man', 'child', 'wife', 'husband', 'mother', 'father'},
}


def themed_domain(gloss):
    tokens = set(re.sub(r'[^a-z ]', ' ', gloss.casefold()).split())
    for domain, words in THEMED_DOMAINS.items():
        if tokens & words:
            return domain
    return 'basic_vocabulary'


def devanagari_variants(value):
    """Extract written forms while dropping romanization and editorial notes."""
    value = re.sub(r'\([^)]*\)', '', value)
    value = re.sub(r'\[[^]]*\]|\{[^}]*\}', '', value)
    variants = []
    for piece in re.split(r'[,/;]', value):
        piece = piece.strip(' .?–—-')
        if piece and any('\u0900' <= char <= '\u097f' for char in piece):
            variants.append(piece)
    return variants


def themed_lexicon_record(source, key, term, info, license_id, license_url,
                           attribution, gloss_en=None, gloss_hi=None, **extra):
    script = extra.pop('script', 'Deva')
    record = make_record(source, key, term, info, license_id, license_url, attribution,
                         gloss_en=gloss_en, gloss_hi=gloss_hi,
                         semantic_domain=extra.pop('semantic_domain', themed_domain(gloss_en or '')),
                         genre='thematic_lexicon', modality='text',
                         corpus_layer='research_lexicon', usage='research_and_native_review',
                         **extra)
    record['training_eligible'] = False
    record['script'] = script
    return record


def local_gloss_domain(gloss):
    folded = gloss.casefold()
    rules = {
        'food': ('dish', 'bread', 'flour', 'food', 'sugar', 'butter', 'wine', 'grain'),
        'plant_nature': ('plant', 'tree', 'forest', 'grass', 'flower', 'seed', 'fruit', 'meadow'),
        'household_object': ('vessel', 'utensil', 'basket', 'stove', 'mill', 'blanket', 'rug'),
        'clothing_ornament': ('blouse', 'cloth', 'skirt', 'bangle', 'ring', 'slipper', 'trousers'),
        'agriculture_livestock': ('agricultur', 'crop', 'cattle', 'livestock', 'grazing', 'pastoral'),
        'ritual_culture': ('festival', 'deity', 'goddess', 'worship', 'ritual', 'dance', 'marriage'),
        'land_geography': ('river', 'stream', 'land', 'village', 'mountain', 'gullies'),
    }
    for domain, markers in rules.items():
        if any(marker in folded for marker in markers):
            return domain
    return 'local_cultural_term'


def hindi_gloss_domain(gloss, default='basic_vocabulary'):
    compact = re.sub(r'\s+', '', gloss)
    markers = {
        'bird': ('पक्षी', 'कठफोड़ा'),
        'insect': ('पिस्सू', 'खटमल', 'मच्छर', 'कनखजूरा', 'ततैया', 'मक्खी', 'चींटी',
                   'तितली', 'मकड़ा', 'बिच्छु', 'जूं', 'लीख', 'जुगुनू', 'कीड़ा'),
        'plant_nature': ('सूरज', 'चन्द्रमा', 'तारे', 'उज्याला', 'अन्धेरा', 'आसमान', 'हवा',
                         'नदि', 'पर्वत', 'बर्फ', 'पानी', 'पत्थर', 'फूल', 'काँटा', 'जड़',
                         'लकड़ी', 'घास', 'झारना', 'चमक', 'जंगल', 'पेड़', 'बिजली', 'तूफान'),
        'kinship_people': ('पत्नी', 'औरत', 'लडका'),
    }
    for domain, words in markers.items():
        if any(word in compact for word in words):
            return domain
    return default
