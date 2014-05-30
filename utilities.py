from flask import url_for
from urllib import urlencode

def paginate_model(model_name, data, filters):
    new_filters = dict(filters)
    del new_filters['offset']
    next, previous = None, None

    if data.data['meta']['next']:
        next_offset = int(filters['offset']) + 20
        next = url_for(model_name) + '?' + 'offset={0}'.format(next_offset)
        if new_filters:
            next = next + '&' + urlencode(new_filters)

    if data.data['meta']['previous']:
        prev_offset = int(filters['offset']) - 20
        previous = url_for(model_name) + '?' + 'offset={0}'.format(prev_offset)
        if new_filters:
            previous = previous + '&' + urlencode(new_filters)

    total_count = data.data['meta']['total_count']
    last = url_for(model_name) + '?' + 'offset={0}'.format(\
                  total_count - total_count%20)
    if new_filters:
        last = last + '&' + urlencode(new_filters)

    return (next, previous, last, total_count)
