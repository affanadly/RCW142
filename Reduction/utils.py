from AIPSData import AIPSCat
from astropy.table import Table
from astropy import units as u

def grab_catalogue(disk):
    # grab catalogue from disk
    return AIPSCat(disk)[disk]

def compare_catalogues(catalogue1, catalogue2, return_multiple=False):
    # compare two catalogues
    for catalogue in [catalogue1, catalogue2]:
        for item in catalogue:
            item.pop('date')
            item.pop('time')
    
    new_items = [item for item in catalogue2 if item not in catalogue1]
    if return_multiple:
        return new_items
    else:
        return new_items[0]

def parse_params(task, params):
    # parse parameters
    if params:
        for key in params:
            if '|' in key:
                temp = getattr(task, key.split('|')[0])
                temp[int(key.split('|')[1])] = params[key]
            else: 
                setattr(task, key, params[key])
