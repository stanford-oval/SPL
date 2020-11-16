# Copyright 2020 The Board of Trustees of the Leland Stanford Junior University
#
# Author: Silei Xu <silei@cs.stanford.edu>
#         Mehrad Moradshahi <mehrad@cs.stanford.edu>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#  contributors may be used to endorse or promote products derived from
#  this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import extruct
import requests
import json
import os
import urllib.parse
import time
from bs4 import BeautifulSoup
import argparse
import datetime

TYPE_MAP = {'RESTAURANT': 'Restaurant', 'HOTEL': 'Hotel'}


ITER = 2

def process_current(url):
    # if re.findall(r'[dg]-\d+', url):
    #     url = re.sub(r'[dg]-\d+', '', url)
    url = url.strip('#REVIEWS')
    return url.strip('#REVIEWS')

def crawl(init_url, base_url, url_pattern, output, interval=0):

    queue = [init_url]
    visited = set()
    
    orig_url_pattern = url_pattern
    i = 0
    while len(queue) > 0 and len(output) < args.target_size:
        
        url_pattern = base_url
        if i >= ITER:
            url_pattern = orig_url_pattern
        
        i += 1
        
        # get one url from the queue
        # shuffle every round
        # random.shuffle(queue)
        current = queue.pop()

        # if the url has been visited, skip
        current = process_current(current)
        if current in visited:
            continue

        # extract the schema.org data
        print(f'Looking for schema.org data from page: {current}')
        # otherwise, start getting information from the url
        response = requests.get(current)
        extracted = extract(response.content, response.url)
            
        if len(extracted) != 0:
            output.extend(extracted)
            print('Successful schema extraction from {}'.format(response.url))
            print('Completed {} of {} total'.format(len(output), args.target_size))
            
        # mark the current page to be visited
        visited.add(current)

        # find unvisited links in the current page and add to the queue
        add_urls(queue, response.text, url_pattern, base_url, visited)

        # wait to avoid being banned by the website
        time.sleep(interval)


def extract(html, url):

    # data = BeautifulSoup(html, 'html.parser')
    data = extruct.extract(html, url, syntaxes=['microdata', 'json-ld', 'rdfa', 'microformat'], errors='log')
    schemas = []
    if data.get('json-ld'):
        for schema in data['json-ld']:
            if schema.get('@type', None):
                # print('*****' + schema['@type'])
                type = schema_pattern_match(schema['@type'])
                if type:
                    schema['@type'] = type
                    schemas.append(schema)
    if data.get('microdata'):
        for schema in data['microdata']:
            # print('*****' + schema['type'])
            type = schema_pattern_match(schema['type'])
            if type:
                schema['type'] = type
                schemas.append(schema)
    if data.get('microformat'):
        for schema in data['microformat']:
            # print('*****' + schema['type'])
            type = schema_pattern_match(schema['type'])
            if type:
                schema['type'] = type
                schemas.append(schema)
    
    return schemas


def add_urls(queue, html, url_pattern, base_url, visited):

    # parse the current page
    soup = BeautifulSoup(html, 'html5lib')

    # find all links that matches the patterns
    all_tags = set([link.name for link in soup.find_all()])
    all_urls = set()
    for link in soup.find_all():
        if 'href' not in link.attrs:
            continue
        url = urllib.parse.urljoin(base_url, link['href'])
        if url in visited:
            continue

        # if the url found matches the given pattern, add it to the queue
        all_urls.add(url)
        if url_pattern_match(url, url_pattern):
            # insert in random location to simulate shuffling
            # i = random.randint(0, len(queue))
            i = 0
            queue.insert(i, url.split('?')[0])
            # queue.append(url.split('?')[0])

def url_pattern_match(url, url_pattern):
    # empty pattern matches anything
    if args.url_patterns is None or args.url_patterns == []:
        return True
    else:
        return url.startswith(url_pattern)
    
    
def schema_pattern_match(type):
    type = process_type(type)
    if type in args.schema_types:
        return type
    else:
        return None


def process_type(word):
    try:
        return TYPE_MAP.get(word, word)
    except:
        return word

def main():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--language', type=str, help='language to extract parameters for')
    parser.add_argument('--experiment', default='restaurants', type=str, help='')
    parser.add_argument('--schema_types', nargs='+', help='list of acceptable types')
    parser.add_argument('--init_urls', nargs='+', help='list of init url')
    parser.add_argument('--base_urls', nargs='+', help='list of base url (should correspond to init_urls)')
    parser.add_argument('--url_patterns', nargs='+', help='list of acceptable url patterns')
    parser.add_argument('--target_size', default=100, type=int, help='')
    parser.add_argument('--output_file', type=str, help='')
    
    global args
    args = parser.parse_args()
    
    output = []
    
    for init_url, base_url, url_pattern in zip(args.init_urls, args.base_urls, args.url_patterns):
        try:
            crawl(init_url, base_url, url_pattern, output)
            
        finally:
        
            timestamp = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            
            if args.output_file is None:
                args.output_file = '../schema_data/{}/{}/data_{}.json'.format(args.experiment, args.language)
                
            output_file = args.output_file.rsplit('.', 1)[0] + '_' + timestamp + '.' + args.output_file.rsplit('.', 1)[1]
        
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        print('Saving results to {} file'.format(output_file))
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
