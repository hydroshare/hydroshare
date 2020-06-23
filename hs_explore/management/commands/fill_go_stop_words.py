"""
This stores ODM2 and CSDMS keywords used for our LDA model.
Also, this stors English and customized common hydrological
stop words used in our LDA model
"""
from hs_explore.models import LDAWord
from django.core.management.base import BaseCommand
from hs_odm2.models import ODM2Variable
from hs_csdms.models import CSDMSName


def fill_csdms_names():
    """ Store CSDMS names into LDAWord model
    """
    csdms_names = list(CSDMSName.list_all_names())
    splitted_names = set()
    for csdms_name in csdms_names:
        if len(csdms_name) <= 1:
            continue
        tokens = csdms_name.split(" ")
        LDAWord.add_word('CSDMS', 'keep', 'name', csdms_name)
        splitted_names.update(tokens)

    for splitted_name in splitted_names:
        if len(splitted_name) <= 1:
            continue
        LDAWord.add_word('CSDMS', 'keep', 'name', splitted_name)


def fill_odm2():
    """ Store ODM2 names into LDAWord model
    """
    odm2_list = list(ODM2Variable.all())
    modified_list = []
    for odm2 in odm2_list:
        tokens = odm2.split(' - ')
        new_string = tokens[0]
        if len(tokens) > 1:
            new_string = tokens[1] + ' ' + tokens[0]
        modified_list.append(new_string.lower())

    for odm2_word in modified_list:
        if len(odm2_word) > 1:
            LDAWord.add_word('ODM2', 'keep', 'name', odm2_word)


def fill_stop_words():
    """ Store common English and customized stop-words into the LDAWord model
    """
    customized_stops = ['max', 'maximum', 'minimum', 'orgin', '________', 'center',
                        'rapid', 'test', 'example', 'demo', 'mm', 'jupyter_hub',
                        'ipython', 'odm2', 'min', 'net', 'unit', 'rating',
                        'hydrologic', 'age', 'contact', 'log', 'change', 'count',
                        'run', 'pi', 'et', 'al', 'set', 'zone', 'latitude', 'longitude',
                        'region', 'matter', 'section', 'column', 'domain', 'height', 'depth',
                        'top', 'bottom', 'left', 'right', 'upper', 'lower', 'location',
                        'image', 'link', 'paper', 'day', 'second', 'parameter', 'solution',
                        'public', 'first', 'sources', 'main', 'sample', 'new', 'total',
                        'state', 'water', 'source', 'resource', 'available', 'year', 'area',
                        'model', 'rate', 'time', 'ratio', 'west', 'south', 'east', 'north',
                        'small', 'big', 'large', 'huge']

    english_stops = ['through', 'should', "shouldn't", 'both', 'in', 'which', "needn't",
                     'its', "wouldn't", 'ourselves', 'at', 'than', 'she', 'yourselves',
                     "you'll", 'it', "weren't", 'here', 'be', 'does', 'who', 'him', 'own',
                     'these', 'her', 'they', 'won', 'ours', "couldn't", 'further', 'a',
                     "hasn't", 'not', 'the', 'having', 'hers', 's', 'or', 'then', 'myself',
                     'during', 'themselves', 'on', 'down', 'doing', 'before', 'is', 'each',
                     'them', 'our', 'wouldn', 'll', 'off', 'nor', "you'd", 'aren', 'had',
                     'yourself', 'to', 'don', 'm', 'yours', 'more', "wasn't", 'was',
                     'because', 'very', 'couldn', "that'll", 'your', 'have', 'over', 'where',
                     'until', "isn't", 'itself', "aren't", 'me', 'we', 'ain', "haven't",
                     'too', 'needn', "won't", 'didn', "don't", 'for', 'i', 'are', "should've",
                     'but', 'from', 'why', 'of', "shan't", "you're", 'all', 'himself', 'theirs',
                     'd', 'whom', 'while', 'again', "didn't", 'few', 'after', 'some', 'shan',
                     't', 'weren', 'haven', 'do', "mightn't", 'can', "you've", 'an', 'only',
                     'his', 'being', 'above', 'any', 'has', 'same', 'their', 'as', 'mustn', 've',
                     'wasn', "she's", 'no', 'such', 'under', 'so', 'doesn', 'ma', 'about', 'those',
                     'shouldn', 'below', 'what', "doesn't", 'he', 'hadn', 'with', 'just', 'am',
                     'y', 'there', 'other', 'if', 'isn', 'between', 'mightn', 'how', 'up', 'my',
                     'this', 'once', 'were', 'out', 'when', 'that', 'by', 'into', 'and', 'will',
                     'o', 'now', "it's", "hadn't", "mustn't", 'been', 'did', 're', 'herself',
                     'against', 'hasn', 'you', 'most']

    for stop_word in customized_stops:
        LDAWord.add_word('Customized', 'stop', 'name', stop_word)
    for stop_word in english_stops:
        LDAWord.add_word('English', 'stop', 'name', stop_word)


class Command(BaseCommand):
    help = "Filling keep words and stop words used in the LDA algorithm"

    def handle(self, *args, **options):
        LDAWord.clear()
        print("filling in keep words")
        fill_csdms_names()
        fill_odm2()
        print("filling in stop words")
        fill_stop_words()
