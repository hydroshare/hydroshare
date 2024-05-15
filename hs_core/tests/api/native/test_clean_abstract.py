from django.test import TestCase
from hs_core.models import clean_abstract


class TestCleaningAbstract(TestCase):
    def test_no_convert_newlines(self):
        self.assertEqual(clean_abstract("it \r\n \r\n is \r\n \r\n finished"),
                         "it \r\n \r\n is \r\n \r\n finished")

    def test_convert_u0003(self):
        self.assertEqual(clean_abstract("it \n\u0003\n is \n\u0003\n finished"),
                         "it \n\n is \n\n finished")

    def test_convert_u0003_2(self):
        """ embedded control characters in words are converted to null """
        self.assertEqual(clean_abstract("it \n \n i\u0003s \n \n finished"),
                         "it \n \n is \n \n finished")

    def test_convert_newlines_nonsense(self):
        """ complete nonsense is converted to null """
        self.assertEqual(clean_abstract("it \n\u0003\u0004 \n i\u0003\u0006\u0001s \n \n finished"),
                         "it \n \n is \n \n finished")

    def test_convert_newlines_arb(self):
        """ arbitrary numbers of newlines not modified """
        self.assertEqual(clean_abstract("it \n\n\r\n\r\n is \n\n\n\n finished"),
                         "it \n\n\r\n\r\n is \n\n\n\n finished")

    def test_clean_abstract_no_illegal_chars(self):
        """ No illegal characters in the abstract """
        original_string = "This is a valid abstract."
        expected_result = "This is a valid abstract."
        self.assertEqual(clean_abstract(original_string), expected_result)

    def test_clean_abstract_with_illegal_chars(self):
        """ Abstract contains illegal characters """
        original_string = "This is an abstract with \x00 illegal \x1F characters."
        expected_result = "This is an abstract with  illegal  characters."
        self.assertEqual(clean_abstract(original_string), expected_result)

    def test_clean_abstract_empty_string(self):
        """ Empty abstract """
        original_string = ""
        expected_result = ""
        self.assertEqual(clean_abstract(original_string), expected_result)

    def test_clean_abstract_with_unicode_chars(self):
        """ Abstract contains unicode characters """
        original_string = "This is an abstract with 𝓊𝓃𝒾𝒸𝑜𝒹𝑒 characters."
        expected_result = "This is an abstract with 𝓊𝓃𝒾𝒸𝑜𝒹𝑒 characters."
        self.assertEqual(clean_abstract(original_string), expected_result)

    def test_clean_abstract_with_ascii_chars(self):
        """ Abstract contains ASCII characters """
        original_string = f"This is an abstract with {chr(0x23CE)} characters."
        expected_result = f"This is an abstract with {chr(0x23CE)} characters."
        self.assertEqual(clean_abstract(original_string), expected_result)

    def test_clean_abstract_with_html_tags(self):
        """ Abstract contains HTML tags """
        original_string = "This is an abstract with <b>HTML</b> tags."
        expected_result = "This is an abstract with <b>HTML</b> tags."
        self.assertEqual(clean_abstract(original_string), expected_result)

    def test_clean_abstract_with_html_entities(self):
        """ Abstract contains HTML entities """
        original_string = "This is an abstract with &lt;HTML&gt; entities."
        expected_result = "This is an abstract with &lt;HTML&gt; entities."
        self.assertEqual(clean_abstract(original_string), expected_result)

    def test_clean_abstract_with_html_entities_and_tags(self):
        """ Abstract contains HTML entities and tags """
        original_string = "This is an abstract with &lt;b&gt;HTML&lt;/b&gt; entities and tags."
        expected_result = "This is an abstract with &lt;b&gt;HTML&lt;/b&gt; entities and tags."
        self.assertEqual(clean_abstract(original_string), expected_result)

    def test_clean_abstract_with_markdown(self):
        """ Abstract contains Markdown """
        original_string = "This is an abstract with **Markdown**."
        expected_result = "This is an abstract with **Markdown**."
        self.assertEqual(clean_abstract(original_string), expected_result)
