from flask import url_for
from urllib import urlencode

def paginate_model(model_name, data, filters):
    count = data['count']

    page = 1
    if 'page' in filters:
    	page = int(filters['page'])
    	del filters['page']
    size = 20
    if 'page_size' in filters:
        size = int(filters['page_size'])
    previous = None
    if data['previous']:
	    previous = url_for(model_name)+'?page='+str(page-1)+'&'+urlencode(filters)
    next = None
    if data['next']:
	    next = url_for(model_name)+'?page='+str(page+1)+'&'+urlencode(filters)
    last = url_for(model_name)+'?page='+str(count/size+1)+'&'+urlencode(filters)

    return (next, previous, last, count)

# When multiple filters are passed to a search request, each filter option is encoded
#   as a separate paramater, e.g. 'rock_types=Gneiss&rock_types=Slate'.  The API
#   doesn't like this, instead preferring comma-separated values in one string.  This
#   fixes that.
def multi_args_to_list(argsIn):
    argsOut = {}
    for arg in argsIn:
        if arg[0] == 'rock_types':
            if arg[0] in argsOut:
                argsOut[arg[0]] += ',' + arg[1]
            else:
                argsOut[arg[0]] = arg[1]
    else:
        argsOut[arg[0]] = arg[1]
    return argsOut