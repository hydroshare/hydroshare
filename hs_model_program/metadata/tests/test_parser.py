__author__ = 'tonycastronova'

import ConfigParser
import os, sys
from os.path import *
import unittest
from hs_hydroprogram.metadata.parser import *
import mmap

class test_ini_parse(unittest.TestCase):

    def setUp(self):
        self.cparser = ConfigParser.ConfigParser(None, multidict)
        self.config = os.path.realpath('../mytest.meta')


    def test_get_metadata_dict(self):

        path = abspath(join(dirname(__file__),'../mytest.meta'))
        #path = os.path.join(os.path.abspath(__file__),'mytest.meta')

        # this is what will be passed via POST
        ini_file = open(path, 'r')
        content = ini_file.read()

        fileObj = mmap.mmap(-1,len(content))
        fileObj.write(content)
        fileObj.seek(0)

        dict = get_metadata_dictionary(fileObj)

        print 'done'

    def test_sections(self):

        # parse the ini
        self.cparser.read(self.config)

        # double check the sections by reading the file directly
        sections = []
        with open (self.config,'r') as f:
            lines = f.readlines()
            for line in lines:
                if '[' in line:
                    sections.append(line[1:-2])
        sections = sorted(list(sections))


        # get the ini sections from the parser
        parsed_sections = sorted(self.cparser.sections())

        for i in xrange(0,len(sections)):
            self.assertTrue(sections[i] == parsed_sections[i].split('^')[0])


    def test_duplicate_sections(self):

        # parse the ini
        self.cparser.read(self.config)

        # get the ini sections from the parser
        parsed_sections = sorted(self.cparser.sections())

        self.assertTrue(len(parsed_sections) == 5)


    def read_duplicates(self,path):

        config_params = {}

        # read sections
        self.cparser.read(self.config)
        sections = self.cparser.sections()

        for s in sections:
            # get the section key (minus the random number)
            section = s.split('_')[0]

            # get the section options
            options = self.cparser.options(s)

            if section not in config_params:
                config_params[section] = [options]
            else:
                config_params[section].append(options)

        return config_params

    def test_config_validate(self):
        test = validate(self.config)
        self.assertTrue(test)