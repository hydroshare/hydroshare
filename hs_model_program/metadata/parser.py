__author__ = 'tonycastronova'
"""
Utility functions for parsing science metadata from ini
"""

import ConfigParser
import cPickle as pickle
import datetime

class metadata_type_struct():

    title = 'str'
    type = 'str'
    abstract = 'str'
    language = 'str'
    subject = 'str'
    format = 'str'
    name='str'
    creatorOrder='int'
    organization = 'str'
    email = 'str'
    address = 'str'
    phone = 'str'
    homepage = 'str'
    researcherID = 'str'
    researchGateID = 'str'
    created = '%Y-%m-%d %H:%M:%S'
    modified = '%Y-%m-%d %H:%M:%S'
    valid = '%Y-%m-%d %H:%M:%S'
    rightsStatement = 'str'
    rightsURL =  'str'
    version = 'str'
    releaseDate = '%Y-%m-%d'
    url = 'str'
    description = 'str'


class multidict(dict):
    _unique = 0

    def __setitem__(self, key, val):
        if isinstance(val, dict):
            self._unique += 1
            key += '^'+str(self._unique)
        dict.__setitem__(self, key, val)



def validate(ini_content):

    cparser = ConfigParser.ConfigParser(None, multidict)

    print '1'

    # parse the ini
    cparser.read(ini_content)

    print '2'

    # get the ini sections from the parser
    parsed_sections = cparser.sections()

    # todo: validate phone numbers using regex
    # todo: validate emails using regex
    # todo: allow dates to have utcoffset embedded
    # todo: validate that format is of a recognized type (application/zip, application/octet-stream)
    # todo: make sure subject is delimited by a semicolon


    # validate
    for section in parsed_sections:
        # get ini options
        options = cparser.options(section)

        # check each option individually
        for option in options:
            val = cparser.get(section,option)

            # validate date format
            if option == 'simulation_start' or option == 'simulation_end':
                try:
                    datetime.datetime.strptime(val, getattr(metadata_type_struct, option))
                except ValueError:
                    raise ValueError("Incorrect data format, should be "+getattr(metadata_type_struct, option))
            else:
                # validate data type
                if not isinstance(val,type(getattr(metadata_type_struct, option))):
                    raise Exception(option+' is not of type '+getattr(metadata_type_struct, option))


    return 1

def get_metadata_dictionary(ini_content):

    cparser = ConfigParser.ConfigParser(None, multidict)

    # parse the ini
    cparser.readfp(ini_content)

    # get the ini sections from the parser
    parsed_sections = cparser.sections()

    meta_dict = {}
    for section in parsed_sections:
        section_name = section.split('^')[0]

        options = cparser.options(section)

        # save ini options as dictionary
        d = {}
        for option in options:
            d[option] = cparser.get(section,option)
        d['type'] = section

        if section_name not in meta_dict:
            meta_dict[section_name] = [d]
        else:
            meta_dict[section_name].append(d)


    return meta_dict