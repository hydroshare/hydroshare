# This is based upon https://github.com/Aplopio/haystack-queryparser with local customizations

import re
import operator
from datetime import datetime, timedelta
from haystack.query import SQ
from django.conf import settings


HAYSTACK_DEFAULT_OPERATOR = getattr(settings, 'HAYSTACK_DEFAULT_OPERATOR', 'AND')


class MatchingBracketsNotFoundError(Exception):
    """ malformed parenthetic expression """

    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return "Matching brackets were not found: "+self.value


class InequalityNotAllowedError(Exception):
    """ malformed inequality """

    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return self.value


class FieldNotRecognizedError(Exception):
    """ Attempt to use unregistered field """

    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return self.value


class MalformedDateError(Exception):
    """ date must be YYYY-MM-DD """

    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return self.value


def head(string):
    return string.split()[0]


def tail(string):
    return " ".join(string.split()[1:])


def parse_date(word):
    datetime_object = None
    for pattern in ['%m/%d/%Y', '%m/%Y', '%Y', '%Y-%m-%d', '%Y-%m']:
        try:
            datetime_object = datetime.strptime(word, pattern)
            return datetime_object
        except ValueError:
            pass
    raise MalformedDateError("'{}' is not a properly formatted date.".format(word))


class ParseSQ(object):
    """
    Parse a HydroShare query into SOLR form.
    """

    # Translation table for logical connectives
    OP = {
        'AND': operator.and_,
        'OR': operator.or_,
        'NOT': operator.inv,
        # aliases '+' (for include) and '-' (for NOT) removed 4/5/2019
        # due to potential collision with valid titles for resources.
    }

    # Translation table for inequalities
    HAYSTACK_INEQUALITY = {
        ':': '',
        '<': '__lt',
        '>': '__gt',
        '<=': '__lte',
        '>=': '__gte'
    }

    # fields known to SOLR that are reasonably searchable.
    # This omits unindexed fields and JSON fields.
    KNOWN_FIELDS = [
        'person',
        'author',
        'first_author',
        'short_id',
        'doi',
        'title',
        'abstract',
        'creator',
        'contributor',
        'subject',
        'availability',
        'replaced',
        'created',
        'modified',
        'organization',
        'publisher',
        'rating',
        'coverage_type',
        'east',
        'north',
        'northlimit',
        'eastlimit',
        'southlimit',
        'westlimit',
        'start_date',
        'end_date',
        'storage_type',
        'format',
        'identifier',
        'language',
        'source',
        'relation',
        'resource_type',
        'content_type',
        'comment',
        'comments_count',
        'owner_login',
        'owner',
        'owners_count',
        'geometry_type',
        'field_name',
        'field_type',
        'field_type_code',
        'variable',
        'variable_type',
        'variable_shape',
        'variable_descriptive_name',
        'variable_speciation',
        'site',
        'method',
        'quality_level',
        'data_source',
        'sample_medium',
        'units',
        'units_type'
    ]

    # This makes the query more friendly to humans
    # The names follow the dublin core names.
    # But humans know 'creator' as 'author'.
    REPLACE_BY = {
        'author': 'creator',
        'first_author': 'author'
    }

    INEQUALITY_FIELDS = [
        'rating',
        'created',
        'modified',
        'east',
        'north',
        'northlimit',
        'eastlimit',
        'southlimit',
        'westlimit',
        'start_date',
        'end_date',
        'comments_count',
        'owners_count',
    ]

    DATE_FIELDS = [
        'created',
        'modified',
        'start_date',
        'end_date'
    ]

    # # Optional more precise control of __exact keyword: disabled for now
    # Pattern_Field_Query = re.compile(r"^(\w+):(\w+)\s*", re.U)
    # Pattern_Field_Exact_Query = re.compile(r"^(\w+):\"(.+)\"\s*", re.U)

    # Paterns without more precise control of __exact keyword
    Pattern_Field_Query = re.compile(r"^(\w+)(:|[<>]=?)", re.U)
    Pattern_Normal_Query = re.compile(r"^(\w+)\s*", re.U)
    Pattern_Operator = re.compile(r"^(AND|OR|NOT)\s*", re.U)
    # '-', '+' removed 4/5/2019 to avoid potential collision with valid resource titles
    Pattern_Quoted_Text = re.compile(r"^\"([^\"]*)\"\s*", re.U)
    Pattern_Unquoted_Text = re.compile(r"^(\w*)\s*", re.U)

    def __init__(self, use_default=HAYSTACK_DEFAULT_OPERATOR):
        self.Default_Operator = use_default

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, current):
        self._prev = self._current if current in ['NOT'] else None
        self._current = current

    def apply_operand(self, new_sq):
        if self.current in ['NOT']:
            new_sq = self.OP[self.current](new_sq)
            self.current = self._prev
        if self.sq:
            return self.OP[self.current](self.sq, new_sq)
        return new_sq

    def handle_field_query(self):
        mat = re.search(self.Pattern_Field_Query, self.query)
        search_field = mat.group(1)
        search_operator = mat.group(2)
        if search_field not in self.KNOWN_FIELDS:
            self.handle_normal_query()
            return
            # raise FieldNotRecognizedError(
            #     "Field name '{}' is not recognized."
            #     .format(search_field))
        if search_field in self.REPLACE_BY:
            search_field = self.REPLACE_BY[search_field]

        if search_operator != ':' and search_field not in self.INEQUALITY_FIELDS:
            raise InequalityNotAllowedError(
                "Inequality is not meaningful for '{}' qualifier."
                .format(search_field))
        # Strip the qualifier off the query, leaving only the match text
        self.query = re.sub(self.Pattern_Field_Query, '', self.query, 1)

        mat = re.search(self.Pattern_Quoted_Text, self.query)
        if mat:
            text_in_quotes = mat.group(1)
            if (search_operator != ':'):
                raise InequalityNotAllowedError(
                    "Inequality is not meaningful for quoted text \"{}\"."
                    .format(text_in_quotes))
            self.sq = self.apply_operand(SQ(**{search_field+"__exact": text_in_quotes}))
            # remove quoted text from query
            self.query = re.sub(self.Pattern_Quoted_Text, '', self.query, 1)
        else:  # no quotes
            word = head(self.query)  # This has no field specifier

            # Append __lt, __lte, etc to query as needed
            inequality_qualifier = self.HAYSTACK_INEQUALITY[search_operator]

            # Parse date in one of a limited number of common formats.
            # TODO: SOLR requires GMT; convert from GMT to local locale for date.
            if search_field in self.DATE_FIELDS:
                thisday_object = parse_date(word)
                thisday = thisday_object.strftime("%Y-%m-%dT%H:%M:%SZ")
                if search_operator == ':':
                    # limit creation date to one day by generating two inequalities
                    nextday_object = thisday_object + timedelta(days=1)
                    nextday = nextday_object.strftime("%Y-%m-%dT%H:%M:%SZ")
                    self.sq = self.apply_operand(SQ(**{search_field+'__gte': thisday}) &
                                                 SQ(**{search_field+'__lt': nextday}))
                elif search_operator == '<=':  # include whole day of target date
                    nextday_object = thisday_object + timedelta(days=1)
                    nextday = nextday_object.strftime("%Y-%m-%dT%H:%M:%SZ")
                    self.sq = self.apply_operand(
                        SQ(**{search_field+"__lt": nextday}))
                elif search_operator == '>':  # include whole day of target date
                    nextday_object = thisday_object + timedelta(days=1)
                    nextday = nextday_object.strftime("%Y-%m-%dT%H:%M:%SZ")
                    self.sq = self.apply_operand(
                        SQ(**{search_field+"__gte": nextday}))
                else:
                    self.sq = self.apply_operand(
                        SQ(**{search_field+inequality_qualifier: thisday}))
            else:
                self.sq = self.apply_operand(SQ(**{search_field+inequality_qualifier: word}))
            # remove unquoted text from query
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
            raise MatchingBracketsNotFoundError("Parentheses must match in '{}'."
                                                .format(self.query))
        self.query, self.current = self.query[i:], self.Default_Operator

    def handle_normal_query(self):
        word = head(self.query)
        self.sq = self.apply_operand(SQ(content=word))
        self.current = self.Default_Operator
        self.query = tail(self.query)

    def handle_operator_query(self):
        self.current = re.search(self.Pattern_Operator, self.query).group(1)
        self.query, n = re.subn(self.Pattern_Operator, '', self.query, 1)

    def handle_quoted_query(self):
        mat = re.search(self.Pattern_Quoted_Text, self.query)
        text_in_quotes = mat.group(1)
        # it seams that haystack exact only works if there is a space in the query.So adding a space
        # if not re.search(r'\s', text_in_quotes):
        #     text_in_quotes+=" "
        self.sq = self.apply_operand(SQ(content__exact=text_in_quotes))
        self.query, n = re.subn(self.Pattern_Quoted_Text, '', self.query, 1)
        self.current = self.Default_Operator

    def parse(self, query):
        """
        Parse a textual query into phrases, and interpret each phrase

        This can raise ValueError if the values passed are not valid.
        """
        self.query = query
        self.sq = SQ()
        self.current = self.Default_Operator
        while self.query:
            self.query = self.query.lstrip()
            if re.search(self.Pattern_Field_Query, self.query):
                self.handle_field_query()
            # # Optional control of exact keyword: disabled for now
            # elif re.search(self.Pattern_Field_Exact_Query, self.query):
            #     self.handle_field_exact_query()
            elif re.search(self.Pattern_Quoted_Text, self.query):
                self.handle_quoted_query()
            elif re.search(self.Pattern_Operator, self.query):
                self.handle_operator_query()
            elif re.search(self.Pattern_Normal_Query, self.query):
                self.handle_normal_query()
            elif self.query and self.query[0] == "(":
                self.handle_brackets()
            else:
                self.handle_normal_query()
        return self.sq
