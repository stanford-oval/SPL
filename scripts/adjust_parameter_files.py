import os
import sys
from collections import defaultdict
import json
import shutil


folder = sys.argv[1]
domain = sys.argv[2]

DOMAIN_CLASSES = {'restaurants': ['Restaurant', 'FoodEstablishment', 'LocalBusiness'],
           'hotels': ['Hotel', 'Place']}

DOMAIN_MAIN_CLASS = {'restaurants': 'FoodEstablishment',
                    'hotels': 'Hotel'}

DOMAIN_CANONICAL = {'restaurants': 'Restaurant',
                    'hotels': 'Hotel'}


data = defaultdict(list)

# first merge all files into main category
for file in os.listdir(folder):
    base, entity = file.split(':', 1)
    for r in DOMAIN_CLASSES[domain]:
        if entity.startswith(r):
            entity = entity[len(r):]
            if entity.endswith('address_streetAddress.tsv'):
                entity = entity.replace('address_streetAddress.tsv', 'address_addressLocality.tsv')
            data[entity].append(file)
            

for ent, file_list in data.items():
    with open(os.path.join(folder, 'org.schema.{}:{}{}.tmp'.format(DOMAIN_CANONICAL[domain], DOMAIN_MAIN_CLASS[domain], ent)), 'w') as fout:
        type = 'tsv' if ent.endswith('tsv') else 'json'
        all_canonicals = set()
        all_info = []

        for file in file_list:
            full_path = os.path.join(folder, file)
            with open(full_path, 'r') as fin:
                if type == 'tsv':
                    for line in fin:
                        try:
                            canonical = line.split('\t')[1]
                        except:
                            print('****', line)
                            continue
                        if canonical in all_canonicals:
                            continue
                        all_canonicals.add(canonical)
                        all_info.append(line)
                else:
                    for dicti in json.load(fin)['data']:
                        try:
                            canonical = dicti['canonical']
                        except:
                            print('****', line)
                            continue
                        if canonical in all_canonicals:
                            continue
                        all_canonicals.add(canonical)
                        all_info.append(dicti)

        if type == 'tsv':
            for info in all_info:
                fout.write(info.strip('\n') + '\n')
        if type == 'json':
            final_dump = {"result": "ok", "data": all_info}
            json.dump(final_dump, fout, ensure_ascii=False)
            
            # remove after merging
            os.remove(full_path)
    
# remove .tmp part and create one for each Domain class
for ent, file_list in data.items():
    full_path = os.path.join(folder, 'org.schema.{}:{}{}.tmp'.format(DOMAIN_CANONICAL[domain], DOMAIN_MAIN_CLASS[domain], ent))
    for class_ in DOMAIN_CLASSES[domain]:
        full_new_path = os.path.join(folder, 'org.schema.{}:{}{}'.format(DOMAIN_CANONICAL[domain], class_, ent))
        shutil.copy2(full_path, full_new_path)
    os.remove(full_path)
