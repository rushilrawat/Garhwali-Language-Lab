import unittest

import wikitext_plain as m


class WikitextPlainTests(unittest.TestCase):
    def test_keeps_prose_and_link_labels_without_wiki_controls(self):
        source = (
            "__NOTOC__\n'''उत्तरखण्ड''' [[Wp/gbm/भारत|भारतौ]] यऽक राज्य च।\n"
            '[[Category:Wp/gbm]]\n{{INTERWIKI|Q1499}}'
        )
        self.assertEqual(m.to_plain_text(source), 'उत्तरखण्ड भारतौ यऽक राज्य च।')

    def test_removes_tables_input_boxes_and_media(self):
        source = (
            '{| class="wikitable"\n! आबादी\n| 100\n|}\n'
            'पातौं इ सङ्गुळ च गढ़वळी भाखा म।\n'
            '[[Image:Map.png|right|thumb|300px]]\n'
            '<inputbox>\ntype=create\ndefault=Wp/gbm/\n</inputbox>'
        )
        self.assertEqual(m.to_plain_text(source), 'पातौं इ सङ्गुळ च गढ़वळी भाखा म।')

    def test_removes_templates_but_preserves_surrounding_garhwali(self):
        source = (
            '{{Infobox language|name=गढ़वळी|nativename={{Lang|gbm|गढ़वळी}}}}\n'
            'गढ़वळी उत्तराखण्ड राज्य मा ब्वौळी जांण वळि यऽक प्रमुख भाषा च।'
        )
        self.assertEqual(
            m.to_plain_text(source),
            'गढ़वळी उत्तराखण्ड राज्य मा ब्वौळी जांण वळि यऽक प्रमुख भाषा च।',
        )


if __name__ == '__main__':
    unittest.main()
