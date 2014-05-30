import ast
import urllib
import json
from flask import Flask, request, render_template, url_for
import dotenv
import drest

from api import MetpetAPI
from utilities import paginate_model


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/samples')
def samples():
    api = MetpetAPI(None, None).api

    filters = ast.literal_eval(json.dumps(request.args))
    offset = request.args.get('offset', 0)
    filters['offset'] = offset
    data = api.sample.get(params=filters)

    next, previous, last, total_count = paginate_model('samples', data, filters)

    samples = data.data['objects']
    for sample in samples:
        mineral_names = [mineral['name'] for mineral in sample['minerals']]
        sample['mineral_list'] = (', ').join(mineral_names)

    first_page_filters = filters
    del first_page_filters['offset']

    if filters:
        first_page_url = url_for('samples') + '?' + urllib.urlencode(first_page_filters)
    else:
        first_page_url = url_for('samples') + urllib.urlencode(first_page_filters)

    return render_template('samples.html',
                           samples=samples,
                           next_url=next,
                           prev_url=previous,
                           total=total_count,
                           first_page=first_page_url,
                           last_page=last)



if __name__ == '__main__':
    dotenv.read_dotenv('../app_variables.env')
    app.run(debug=True)
