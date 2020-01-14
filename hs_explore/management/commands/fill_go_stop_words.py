from hs_explore.models import LDAWord
from django.core.management.base import BaseCommand
from hs_odm2.models import ODM2Variable


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
    
    for stop_word in customized_stops:
	LDAWord.add_word('Customized', 'stop', 'name', stop_word)	


class Command(BaseCommand):
    help = "check on tracking"


    def handle(self, *args, **options):
 	LDAWord.clear()
        
	fill_csdms()
        fill_odm2()
        fill_stop_words()
