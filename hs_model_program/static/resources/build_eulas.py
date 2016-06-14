
import json

eulas = {}
files = ['gnu2.txt','gnu3.txt','mit.txt','mozilla.txt']

for file in files:
    with open(file,'r') as f:
        lines = f.readlines()
        key = lines[0].strip()
        value = ''

        for i in range(2, len(lines)):
            value += lines[i]

        eulas[key] = value

print eulas.keys()

json.dump(eulas, open('./eulas.json','w'))