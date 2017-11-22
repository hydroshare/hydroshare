#! /usr/bin/python

# This is loosely based upon https://github.com/Aplopio/haystack-queryparser
# with local customization -- Alva L. Couch, 11/21/2017

"""
Test common search query syntax.
"""

from unittest import TestCase
from haystack.query import SQ
from hs_core.discovery_parser import ParseSQ


class SimpleTest(TestCase):

    def setUp(self):
        pass

    def test_parse(self):
        testcase = {
            "note": str(SQ(content="note")),
            '"need note"': str(SQ(content__exact="need note")),
            "author:admin": str(SQ(author="admin")),
            "author:admin notes": str(SQ(author="admin") & SQ(content="notes")),
            "author:admin OR notes": str(SQ(author="admin") | SQ(content="notes")),
            'title:"need note"': str(SQ(title__exact="need note")),
            # "need note ?????": str(SQ(content="need") & SQ(content="note") &
            #                        SQ(content=u"?") & SQ(content=u"?") & SQ(content=u"?") &
            #                        SQ(content=u"?") & SQ(content=u"?")),
            "need note NOT used": str(SQ(content="need") & SQ(content="note") &
                                      ~SQ(content="used")),
            "(a AND b) OR (c AND d)": str((SQ(content="a") & SQ(content="b")) |
                                          (SQ(content="c") & SQ(content="d"))),
            "a AND b OR (c AND d)": str(SQ(content="a") & SQ(content="b") |
                                       (SQ(content="c") & SQ(content="d"))),
            '"a AND b" OR "(c AND d)"': str(SQ(content__exact="a AND b") |
                                            SQ(content__exact="(c AND d)")),
            '"notes done" OR papaya': str(SQ(content__exact="notes done") |
                                          SQ(content="papaya")),
            '"a AND b" OR (c AND d)': str(SQ(content__exact="a AND b") |
                                          (SQ(content="c") & SQ(content="d"))),
            'labels:"exp>20"': str(SQ(labels__exact="exp>20")),
            'labels:"HP employee"': str(SQ(labels__exact="HP employee")),
            'labels:"HP employee" OR something': str(SQ(labels__exact="HP employee") |
                                                     SQ(content='something')),

        }
        parser = ParseSQ()

        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_parse_with_new_default(self):
        testcase = {
            'helo again bye': {'sq': str(SQ(content='helo') | SQ(content='again') |
                                         SQ(content='bye')),
                               'operator': 'OR'},
            'helo again AND bye': {
                'sq': str((SQ(content='helo') | SQ(content='again')) & SQ(content='bye')),
                'operator': 'OR'},
            'helo again AND bye run': {
                'sq': str(((SQ(content='helo') | SQ(content='again')) &
                          SQ(content='bye')) | SQ(content='run')),
                'operator': 'OR'},

        }
        for case in testcase.keys():
            parser = ParseSQ(testcase[case]['operator'])
            self.assertEqual(str(parser.parse(case, )), testcase[case]['sq'])

    def test_operators(self):
        testcase = {
            "note": str(SQ(content="note")),
            "need -note": str(SQ(content="need") & ~SQ(content="note")),
            "need +note": str(SQ(content="need") & SQ(content="note")),
            "need+note": str(SQ(content="need+note")),
            "iphone AND NOT category:10": str(SQ(content="iphone") & ~SQ(
                category="10")),
            "NOT category:10": str(~SQ(category="10")),
            "category:10": str(SQ(category="10")),
            "-category:10": str(~SQ(category="10")),
            "category:-10": str(SQ(category="-10")),
        }
        parser = ParseSQ()

        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])


# def main():
#     suite = TestLoader().loadTestsFromTestCase(SimpleTest)
#     TextTestRunner(verbosity=2).run(suite)
