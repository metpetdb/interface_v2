from flask import url_for
from urllib import urlencode

def paginate_model(model_name, data, filters):
    count = data['count']

    page = 1
    if 'page' in filters:
    	page = int(filters['page'])
    	del filters['page']
    previous = None
    if data['previous']:
	    previous = url_for(model_name)+'?page='+str(page-1)+'&'+urlencode(filters)
    next = None
    if data['next']:
	    next = url_for(model_name)+'?page='+str(page+1)+'&'+urlencode(filters)
    last = url_for(model_name)+'?page='+str(count/20)+'&'+urlencode(filters)

    return (next, previous, last, count)
