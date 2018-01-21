#! /usr/bin/python

# This is loosely based upon https://github.com/Aplopio/haystack-queryparser
# with local customization -- Alva L. Couch, 11/21/2017

"""
Test common search query syntax.
"""

from unittest import TestCase
from haystack.query import SQ
from hs_core.discovery_parser import ParseSQ, \
    FieldNotRecognizedError, \
    MalformedDateError, \
    InequalityNotAllowedError, \
    MatchingBracketsNotFoundError


class SimpleTest(TestCase):

    def setUp(self):
        pass

    def test_basic_parse(self):
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
            'subject:"exp>20"': str(SQ(subject__exact="exp>20")),
            'subject:"HP employee"': str(SQ(subject__exact="HP employee")),
            'subject:"HP employee" OR something': str(SQ(subject__exact="HP employee") |
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
            "iphone AND NOT subject:10": str(SQ(content="iphone") & ~SQ(
                subject="10")),
            "NOT subject:10": str(~SQ(subject="10")),
            "subject:10": str(SQ(subject="10")),
            "-subject:10": str(~SQ(subject="10")),
            "subject:-10": str(SQ(subject="-10")),
        }
        parser = ParseSQ()
        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_dates(self):
        testcase = {
            "created:2017-05-02": str(SQ(created='2017-05-02T00:00:00Z')),
            "created:2017-05": str(SQ(created='2017-05-01T00:00:00Z')),
            "created:2017": str(SQ(created='2017-01-01T00:00:00Z')),
            "modified:2017-05-02": str(SQ(modified='2017-05-02T00:00:00Z')),
            "modified:2017-05": str(SQ(modified='2017-05-01T00:00:00Z')),
            "modified:2017": str(SQ(modified='2017-01-01T00:00:00Z')),
            "start_date:2017-05-02": str(SQ(start_date='2017-05-02T00:00:00Z')),
            "start_date:2017-05": str(SQ(start_date='2017-05-01T00:00:00Z')),
            "start_date:2017": str(SQ(start_date='2017-01-01T00:00:00Z')),
            "end_date:2017-05-02": str(SQ(end_date='2017-05-02T00:00:00Z')),
            "end_date:2017-05": str(SQ(end_date='2017-05-01T00:00:00Z')),
            "end_date:2017": str(SQ(end_date='2017-01-01T00:00:00Z')),
        }
        parser = ParseSQ()
        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_inequalities(self):
        testcase = {
            "north:<=50.0": str(SQ(north__lte='50.0')),
            "north:<50.0": str(SQ(north__lt='50.0')),
            "north:>=50.0": str(SQ(north__gte='50.0')),
            "north:>50.0": str(SQ(north__gt='50.0')),
            "east:<=50.0": str(SQ(east__lte='50.0')),
            "east:<50.0": str(SQ(east__lt='50.0')),
            "east:>=50.0": str(SQ(east__gte='50.0')),
            "east:>50.0": str(SQ(east__gt='50.0')),
            "created:>2017-05-02": str(SQ(created__gt='2017-05-02T00:00:00Z')),
            "created:>=2017-05-02": str(SQ(created__gte='2017-05-02T00:00:00Z')),
            "created:<2017-05-02": str(SQ(created__lt='2017-05-02T00:00:00Z')),
            "created:<=2017-05-02": str(SQ(created__lte='2017-05-02T00:00:00Z')),
        }
        parser = ParseSQ()
        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_exceptions(self):
        testcase = {
            "foo:bar": FieldNotRecognizedError,
            "created:20170": MalformedDateError,
            "created:2017-30": MalformedDateError,
            "created:2017-12-64": MalformedDateError,
            "abstract:>foo": InequalityNotAllowedError,
            "(abstract:something": MatchingBracketsNotFoundError
        }
        parser = ParseSQ()
        for case in testcase.keys():
            with self.assertRaises(testcase[case]):
                parser.parse(case)
