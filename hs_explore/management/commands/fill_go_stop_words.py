from hs_explore.models import LDAWord
from django.core.management.base import BaseCommand
from hs_odm2.models import ODM2Variable
from nltk.corpus import stopwords


def split_csdms():
    filename = 'csdms'
    std_names = []
    with open(filename) as f:
        std_names = f.readlines()
    std_names = [x.strip() for x in std_names]
    names = set()
    measures = set()
    decors = set()
    for std_name in std_names:
        tokens = std_name.split("__")
        name = tokens[0]
        if len(tokens) > 1:
            measures.add(tokens[1])
        name_tokens = name.split("~")
        idx = 0
        raw_name = name_tokens[0].replace("_", " ")
        names.add(raw_name)
        if len(name_tokens) > 1:
            for d in name_tokens[1:]:
                raw_d = d.replace("_", " ")
                decors.add(raw_d)

    splitted_names = set()
    for full_name in names:
        tokens = full_name.split(" ")
        splitted_names.update(tokens)

    splitted_decors = set()
    for decor in decors:
        tokens = decor.split(" ")
        splitted_decors.update(tokens)

    return names, splitted_names, decors, splitted_decors


def fill_csdms():
    csdms_raw_full_names, csdms_splitted_names, csdms_raw_decors, csdms_splitted_decors = split_csdms()
    for csdms_name in csdms_raw_full_names:
        if len(csdms_name) > 1:
            LDAWord.add_word('CSDMS', 'go', 'name', csdms_name)
    for splitted_name in csdms_splitted_names:
        if len(splitted_name) > 1:
            LDAWord.add_word('CSDMS', 'go', 'name', splitted_name)

    for csdms_decor in csdms_raw_decors:
        if len(csdms_decor) > 1:
            LDAWord.add_word('CSDMS', 'go', 'decor', csdms_decor)

    for splitted_decor in csdms_splitted_decors:
        if len(splitted_decor) > 1:
            LDAWord.add_word('CSDMS', 'go', 'decor', splitted_decor)



def fill_odm2():
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
            LDAWord.add_word('ODM2', 'go', 'name', odm2_word)

def fill_stop_words():
    customized_stops = ['max', 'maximum', 'minimum', 'orgin', '________', 'center', 'rapid', 'test', 'example', 'demo', 'mm', 'jupyter_hub', 'ipython', 'odm2', 'min', 'net', 'unit', 'rating', 'hydrologic', 'age', 'contact', 'log', 'change', 'count', 'run', 'pi', 'et', 'al', 'set', 'zone', 'latitude', 'longitude','region', 'matter', 'section', 'column','domain', 'height', 'depth', 'top', 'bottom', 'left', 'right', 'upper', 'lower', 'location', 'image', 'link', 'paper', 'day', 'second', 'parameter', 'solution', 'public', 'first', 'sources', 'main', 'sample', 'new', 'total', 'state', 'water', 'source', 'resource', 'available', 'year', 'area', 'model', 'rate', 'time', 'ratio', 'west', 'south', 'east', 'north']
   
    english_stops = ['through', 'should', "shouldn't", 'both', 'in', 'which', "needn't", 'its', "wouldn't", 'ourselves', 'at', 'than', 'she', 'yourselves', "you'll", 'it', "weren't", 'here', 'be', 'does', 'who', 'him', 'own', 'these', 'her', 'they', 'won', 'ours', "couldn't", 'further', 'a', "hasn't", 'not', 'the', 'having', 'hers', 's', 'or', 'then', 'myself', 'during', 'themselves', 'on', 'down', 'doing', 'before', 'is', 'each', 'them', 'our', 'wouldn', 'll', 'off', 'nor', "you'd", 'aren', 'had', 'yourself', 'to', 'don', 'm', 'yours', 'more', "wasn't", 'was', 'because', 'very', 'couldn', "that'll", 'your', 'have', 'over', 'where', 'until', "isn't", 'itself', "aren't", 'me', 'we', 'ain', "haven't", 'too', 'needn', "won't", 'didn', "don't", 'for', 'i', 'are', "should've", 'but', 'from', 'why', 'of', "shan't", "you're", 'all', 'himself', 'theirs', 'd', 'whom', 'while', 'again', "didn't", 'few', 'after', 'some', 'shan', 't', 'weren', 'haven', 'do', "mightn't", 'can', "you've", 'an', 'only', 'his', 'being', 'above', 'any', 'has', 'same', 'their', 'as', 'mustn', 've', 'wasn', "she's", 'no', 'such', 'under', 'so', 'doesn', 'ma', 'about', 'those', 'shouldn', 'below', 'what', "doesn't", 'he', 'hadn', 'with', 'just', 'am', 'y', 'there', 'other', 'if', 'isn', 'between', 'mightn', 'how', 'up', 'my', 'this', 'once', 'were', 'out', 'when', 'that', 'by', 'into', 'and', 'will', 'o', 'now', "it's", "hadn't", "mustn't", 'been', 'did', 're', 'herself', 'against', 'hasn', 'you', 'most']
 
    for stop_word in customized_stops:
        LDAWord.add_word('Customized', 'stop', 'name', stop_word)
    for stop_word in english_stops:
        LDAWord.add_word('English', 'stop', 'name', stop_word)

class Command(BaseCommand):
    help = "Filling go words and stop words used in the LDA algorithm"


    def handle(self, *args, **options):
        LDAWord.clear()
        print("filling in go words")
        fill_csdms()
        fill_odm2()
        print("filling in stop words")
        fill_stop_words()
