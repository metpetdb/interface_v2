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

def combine_identical_parameters(paramsIn):
    paramsOut = {}
    listParams = ['rock_types', 'metamorphic_grades', 'minerals', 'elements', 'oxides', 'countries', 'metamorphic_regions', 'regions']
    for param in paramsIn:
        if param[0] in listParams:
            if param[0] in paramsOut:
                paramsOut[param[0]] += ',' + param[1]
            else:
                paramsOut[param[0]] = param[1]
        else:
            paramsOut[param[0]] = param[1]
    return paramsOut
