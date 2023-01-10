#! /usr/bin/python

# This is loosely based upon https://github.com/Aplopio/haystack-queryparser
# with local customization -- Alva L. Couch, 11/21/2017

"""
Test common search query syntax.
"""

from unittest import TestCase

from haystack.inputs import Clean, Exact
from haystack.query import SQ

from hs_core.discovery_parser import InequalityNotAllowedError, MalformedDateError, MatchingBracketsNotFoundError, \
    ParseSQ


class SimpleTest(TestCase):

    def setUp(self):
        pass

    def test_quotes(self):
        testcase = {
            'note': str(SQ(content=Clean("note"))),
            'note bones': str(SQ(content=Clean("note")) & SQ(content=Clean("bones"))),
            'note "bones"': str(SQ(content=Clean("note")) & SQ(content=Exact("bones"))),
            '"need note"': str(SQ(content=Exact("need note"))),
            'need note used': str(SQ(content=Clean("need"))
                                  & SQ(content=Clean("note"))
                                  & SQ(content=Clean("used"))),
            '"need" "note"': str(SQ(content=Exact("need"))
                                 & SQ(content=Exact("note"))),

            # removed '+', '-' syntaxes 4/5/2019. test cases modified accordingly.
            '"note"': str(SQ(content=Exact('note'))),
            'need -note': str(SQ(content=Clean('need')) & SQ(content=Clean(' note'))),
            '"need -note"': str(SQ(content=Exact('need -note'))),
            'need +note': str(SQ(content=Clean('need')) & SQ(content=Clean('+note'))),
            'need+note': str(SQ(content=Clean('need+note'))),
        }
        parser = ParseSQ()
        for case in list(testcase.keys()):
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_fields(self):
        testcase = {
            "author:admin": str(SQ(creator="admin")),
            "first_author:admin": str(SQ(author="admin")),
            "author:admin notes": str(SQ(creator="admin") & SQ(content=Clean("notes"))),
            'author:"admin notes"': str(SQ(creator=Exact("admin notes"))),
            'title:"need note"': str(SQ(title=Exact("need note"))),
            'subject:"exp>20"': str(SQ(subject=Exact("exp>20"))),
            'subject:"HP employee"': str(SQ(subject=Exact("HP employee"))),
            'subject:10': str(SQ(subject='10')),
            'subject:-10': str(SQ(subject='-10')),
            # all keywords accepted, non-matches are treated literally
            '-subject:10': str(SQ(content=Clean(' subject:10'))),
            'foo:bar': str(SQ(content=Clean('foo:bar'))),
        }
        parser = ParseSQ(handle_fields=True)

        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_logic(self):
        testcase = {
            'need note NOT used': str(SQ(content=Clean("need"))
                                      & SQ(content=Clean("note")) & ~ SQ(content=Clean("used"))),
            '(a AND b) OR (c AND d)': str((SQ(content=Clean("a")) & SQ(content=Clean("b")))
                                          | (SQ(content=Clean("c")) & SQ(content=Clean("d")))),
            'a AND b OR (c AND d)': str(SQ(content=Clean("a")) & SQ(content=Clean("b"))
                                        | (SQ(content=Clean("c")) & SQ(content=Clean("d")))),
            '"a AND b" OR "(c AND d)"': str(SQ(content=Exact("a AND b"))
                                            | SQ(content=Exact("(c AND d)"))),
            '"notes done" OR papaya': str(SQ(content=Exact("notes done"))
                                          | SQ(content=Clean("papaya"))),
            '"a AND b" OR (c AND d)': str(SQ(content=Exact("a AND b"))
                                          | (SQ(content=Clean("c")) & SQ(content=Clean("d")))),
            'subject:"HP employee" OR something': str(SQ(subject=Exact("HP employee"))
                                                      | SQ(content=Clean('something'))),
        }
        parser = ParseSQ(handle_logic=True, handle_fields=True)

        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_parse_with_different_default(self):
        testcase = {
            'helo again bye': {'sq': str(SQ(content=Clean('helo')) | SQ(content=Clean('again'))
                                         | SQ(content=Clean('bye'))),
                               'operator': 'OR'},
            'helo again AND bye': {
                'sq': str((SQ(content=Clean('helo')) | SQ(content=Clean('again'))) & SQ(content=Clean('bye'))),
                'operator': 'OR'},
            'helo again AND bye run': {
                'sq': str(((SQ(content=Clean('helo')) | SQ(content=Clean('again')))
                          & SQ(content=Clean('bye'))) | SQ(content=Clean('run'))),
                'operator': 'OR'},

        }
        for case in testcase.keys():
            parser = ParseSQ(testcase[case]['operator'], handle_logic=True)
            self.assertEqual(str(parser.parse(case, )), testcase[case]['sq'])

    def test_operators_and_fields(self):
        testcase = {
            'iphone AND NOT subject:10': str(SQ(content=Clean('iphone')) & ~SQ(subject='10')),
            'iphone OR NOT subject:10': str(SQ(content=Clean('iphone')) | ~SQ(subject='10')),
            'NOT subject:10': str(~SQ(subject='10')),
            'NOT subject:"10"': str(~SQ(subject=Exact('10'))),
        }
        parser = ParseSQ(handle_fields=True, handle_logic=True)
        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_dates(self):
        testcase = {
            "created:2017-05-02": str(SQ(created__gte='2017-05-02T00:00:00Z')
                                      & SQ(created__lt='2017-05-03T00:00:00Z')),
            "created:2017-05": str(SQ(created__gte='2017-05-01T00:00:00Z')
                                   & SQ(created__lt='2017-05-02T00:00:00Z')),
            "created:2017": str(SQ(created__gte='2017-01-01T00:00:00Z')
                                & SQ(created__lt='2017-01-02T00:00:00Z')),
            "modified:2017-05-02": str(SQ(modified__gte='2017-05-02T00:00:00Z')
                                       & SQ(modified__lt='2017-05-03T00:00:00Z')),
            "modified:2017-05": str(SQ(modified__gte='2017-05-01T00:00:00Z')
                                    & SQ(modified__lt='2017-05-02T00:00:00Z')),
            "modified:2017": str(SQ(modified__gte='2017-01-01T00:00:00Z')
                                 & SQ(modified__lt='2017-01-02T00:00:00Z')),
            "start_date:2017-05-02": str(SQ(start_date__gte='2017-05-02T00:00:00Z')
                                         & SQ(start_date__lt='2017-05-03T00:00:00Z')),
            "start_date:2017-05": str(SQ(start_date__gte='2017-05-01T00:00:00Z')
                                      & SQ(start_date__lt='2017-05-02T00:00:00Z')),
            "start_date:2017": str(SQ(start_date__gte='2017-01-01T00:00:00Z')
                                   & SQ(start_date__lt='2017-01-02T00:00:00Z')),
            "end_date:2017-05-02": str(SQ(end_date__gte='2017-05-02T00:00:00Z')
                                       & SQ(end_date__lt='2017-05-03T00:00:00Z')),
            "end_date:2017-05": str(SQ(end_date__gte='2017-05-01T00:00:00Z')
                                    & SQ(end_date__lt='2017-05-02T00:00:00Z')),
            "end_date:2017": str(SQ(end_date__gte='2017-01-01T00:00:00Z')
                                 & SQ(end_date__lt='2017-01-02T00:00:00Z')),
        }
        parser = ParseSQ(handle_fields=True)
        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_inequalities(self):
        testcase = {
            "north<=50.0": str(SQ(north__lte='50.0')),
            "north<50.0": str(SQ(north__lt='50.0')),
            "north>=50.0": str(SQ(north__gte='50.0')),
            "north>50.0": str(SQ(north__gt='50.0')),
            "east<=50.0": str(SQ(east__lte='50.0')),
            "east<50.0": str(SQ(east__lt='50.0')),
            "east>=50.0": str(SQ(east__gte='50.0')),
            "east>50.0": str(SQ(east__gt='50.0')),
            "created>2017-05-02": str(SQ(created__gte='2017-05-03T00:00:00Z')),
            "created>=2017-05-02": str(SQ(created__gte='2017-05-02T00:00:00Z')),
            "created<2017-05-02": str(SQ(created__lt='2017-05-02T00:00:00Z')),
            "created<=2017-05-02": str(SQ(created__lt='2017-05-03T00:00:00Z')),
        }
        parser = ParseSQ(handle_fields=True)
        for case in testcase.keys():
            self.assertEqual(str(parser.parse(case)), testcase[case])

    def test_exceptions(self):
        testcase = {
            # This exception removed 4/5/2019: "foo:bar": FieldNotRecognizedError,
            "created:20170": MalformedDateError,
            "created:2017-30": MalformedDateError,
            "created:2017-12-64": MalformedDateError,
            "abstract>foo": InequalityNotAllowedError,
            "(abstract:something": MatchingBracketsNotFoundError
        }
        parser = ParseSQ(handle_fields=True, handle_logic=True)
        for case in testcase.keys():
            with self.assertRaises(testcase[case]):
                parser.parse(case)
