# This is based upon https://github.com/Aplopio/haystack-queryparser with local customizations

import re
import sys
import operator
from haystack.query import SQ
from django.conf import settings

# # Optional more precise control of __exact keyword: disabled for now
# Pattern_Field_Query = re.compile(r"^(\w+):(\w+)\s*", re.U)
# Pattern_Field_Exact_Query = re.compile(r"^(\w+):\"(.+)\"\s*", re.U)

# Paterns without more precise control of __exact keyword
Pattern_Field_Query = re.compile(r"^(\w+):", re.U)
Pattern_Normal_Query = re.compile(r"^(\w+)\s*", re.U)
Pattern_Operator = re.compile(r"^(AND|OR|NOT|\-|\+)\s*", re.U)
Pattern_Quoted_Text = re.compile(r"^\"([^\"]*)\"\s*", re.U)

HAYSTACK_DEFAULT_OPERATOR = getattr(settings, 'HAYSTACK_DEFAULT_OPERATOR', 'AND')
DEFAULT_OPERATOR = ''
OP = {
    'AND': operator.and_,
    'OR': operator.or_,
    'NOT': operator.inv,
    '+': operator.and_,
    '-': operator.inv,
}
KNOWN_FIELDS = ['title', 'author', 'creator', 'subject', 'variable', 'units',
                'contributor', 'accessibility', 'created', 'modified', 'publisher',
                'rating', 'resource_type', 'owner']


class NoMatchingBracketsFound(Exception):
    """ malformed parenthetic expression """

    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return "Matching brackets were not found: "+self.value


class UnhandledException(Exception):
    """ fault during regular expression matching """
    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return self.value


class FieldNotKnownException(Exception):
    """ Attempt to use unregistered field """

    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return self.value


def head(string):
    return string.split()[0]


def tail(string):
    return " ".join(string.split()[1:])


class ParseSQ(object):

    def __init__(self, use_default=HAYSTACK_DEFAULT_OPERATOR):
        self.Default_Operator = use_default

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, current):
        self._prev = self._current if current in ['-', 'NOT'] else None
        self._current = current

    def apply_operand(self, new_sq):
        if self.current in ['-', 'NOT']:
            new_sq = OP[self.current](new_sq)
            self.current = self._prev
        if self.sq:
            return OP[self.current](self.sq, new_sq)
        return new_sq

    def handle_field_query(self):
        mat = re.search(Pattern_Field_Query, self.query)
        search_field = mat.group(1)
        if search_field not in KNOWN_FIELDS:
            raise FieldNotKnownException("field {} is not one of {}"
                                         .format(search_field, ','.join(KNOWN_FIELDS)))

        self.query, n = re.subn(Pattern_Field_Query, '', self.query, 1)
        if re.search(Pattern_Quoted_Text, self.query):
            mat = re.search(Pattern_Quoted_Text, self.query)
            self.sq = self.apply_operand(SQ(**{search_field+"__exact": mat.group(1)}))
            self.query, n = re.subn(Pattern_Quoted_Text, '', self.query, 1)
        else:
            word = head(self.query)
            self.sq = self.apply_operand(SQ(**{search_field: word}))
            self.query = tail(self.query)

        self.current = self.Default_Operator

    def handle_brackets(self):
        no_brackets = 1
        i = 1
        assert self.query[0] == "("
        while no_brackets and i < len(self.query):
            if self.query[i] == ")":
                no_brackets -= 1
            elif self.query[i] == "(":
                no_brackets += 1
            i += 1
        if not no_brackets:
            parser = ParseSQ(self.Default_Operator)
            self.sq = self.apply_operand(parser.parse(self.query[1:i-1]))
        else:
            raise NoMatchingBracketsFound(self.query)
        self.query, self.current = self.query[i:], self.Default_Operator

    def handle_normal_query(self):
        word = head(self.query)
        self.sq = self.apply_operand(SQ(content=word))
        self.current = self.Default_Operator
        self.query = tail(self.query)

    def handle_operator_query(self):
        self.current = re.search(Pattern_Operator, self.query).group(1)
        self.query, n = re.subn(Pattern_Operator, '', self.query, 1)

    def handle_quoted_query(self):
        mat = re.search(Pattern_Quoted_Text, self.query)
        query_temp = mat.group(1)
        # it seams that haystack exact only works if there is a space in the query.So adding a space
        # if not re.search(r'\s', query_temp):
        #     query_temp+=" "
        self.sq = self.apply_operand(SQ(content__exact=query_temp))
        self.query, n = re.subn(Pattern_Quoted_Text, '', self.query, 1)
        self.current = self.Default_Operator

    def parse(self, query):
        self.query = query
        try:
            self.sq = SQ()
            self.current = self.Default_Operator
            while self.query:
                self.query = self.query.lstrip()
                if re.search(Pattern_Field_Query, self.query):
                    self.handle_field_query()
                # # Optional control of exact keyword: disabled for now
                # elif re.search(Pattern_Field_Exact_Query, self.query):
                #     self.handle_field_exact_query()
                elif re.search(Pattern_Quoted_Text, self.query):
                    self.handle_quoted_query()
                elif re.search(Pattern_Operator, self.query):
                    self.handle_operator_query()
                elif re.search(Pattern_Normal_Query, self.query):
                    self.handle_normal_query()
                elif self.query[0] == "(":
                    self.handle_brackets()
                else:
                    self.query = self.query[1:]
        except:
            print self.sq, self.query, self.current
            raise UnhandledException(sys.exc_info())
        return self.sq
