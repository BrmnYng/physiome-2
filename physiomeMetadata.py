import bs4
import os
import re
import requests_cache

import yaml
from collections import OrderedDict

#???do not understand the 'pmr' parameter: is it cache name or serializer.
#!!!my understanding is that it is an extension of request, but with caching features
#requests-cache.readthedocs.io/en/stable/session.html
session = requests_cache.CachedSession('pmr')
#String object 'BASE_URL' 
BASE_URL = 'https://models.physiomeproject.org'

def get_model_metadata(id):
    """Creates a metadata file for the physiome models
    
    Args:
       id (str): physiome model identifier   
    
    Returns:
        metadata (dict): metadata describing physiome model
            keys: id, title, description, thumbnails    
    
    """

    #formats 'url'(str) into https://models.physiomeproject.org/id(int)/view
    url = '{}/{}/view'.format(BASE_URL, id)
    #??? what type of variable is response? I am assuming HTML, but why need response.text in later lines
    #sends get request to specified 'url' formatted above
    response = session.get(url)
    #returns an HTTPError (used for debugging)
    response.raise_for_status()

    #pulls data out of HTML files
    #??? is html_doc a html variable?
    html_doc = bs4.BeautifulSoup(response.text, 'html.parser')
    #???
    content = html_doc.find(id='content')
    content_core = content.find(id='content-core').find('div')

    #dictionary of data to be returned
    metadata = {
        'id': id,
        'Title': None,
        'Abstract': None,
        'Description': None,
        'Thumbnails': None,
        'Keywords': None,
        'Authors': None, 
        'Curators': None,
        'Citations': None,
        'License': "spdxID: MIT" ,
        'Created': None,
        'Modified':None, 
    }
    """
        'id': id,
        'Title': None,
        'Abstract': None,
        'Description': None,
        'Thumbnails': None,
    """

    metadata['License'] = "spdxID: MIT" 

    # title
    title_el = content.find('h1')
    #removes any whitespace from title_el
    title = title_el.text.strip()

    metadata['Title'] = title

    # description
    description = ''
    caption = ''
    for child in content_core.children:
        if child.name == 'title':
            continue        
        if isinstance(child, str):
            description += child
        elif child.name == 'table':
            continue
        else:
            description += child.text

    description = description.replace('\xa0', ' ')
    description = description.strip()
    description = re.sub(r'\n[ \t]+', '\n', description)
    description = re.sub(r'\n{2,}', '\n\n', description)    

    metadata['Description'] = description

    # image
    images = content_core.find_all(class_='tmp-doc-informalfigure table')
    metadata['Thumbnails'] = []
    for image in images:
        image_src = image.find('img').get('src')
        image_url = '{}/{}/{}'.format(BASE_URL, id, image_src)
        response = session.get(image_url)
        response.raise_for_status()

        if not os.path.isdir(id):
            os.makedirs(id)
       
        with open(os.path.join(id, image_src), 'wb') as file:
            file.write(response.content)

        metadata['Thumbnails'].append({
            'filename': image_src,
            'caption': image.text.strip().replace('\xa0', ' '),
        })

    curators = [{"Orcid": "0000-0002-2605-5080", "Name":"Jonathan Karr"}, {"Orcid": "0000-0002-0962-961X", "Name": "Briman Yang"},{"Orcid": "XXXX-XXXX-XXXX-XXXX", "Name": "Wang Mak"},{"Orcid": "XXXX-XXXX-XXXX-XXXX", "Name": "Justin Wang"}]

    metadata['Curators'] = curators

    return metadata

id = 'e/105'
metadata = get_model_metadata(id)

md = OrderedDict(metadata)

metadata_filename = str(id) + '.yml'
with open(metadata_filename, 'w') as file:
    file.write(yaml.dump(metadata, sort_keys = False, default_flow_style=False))

print("Success!")