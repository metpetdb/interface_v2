import ast
from urllib import urlencode
from requests import get
import json
from flask import Flask, request, render_template, url_for, redirect
import dotenv
from getenv import env
import drest

from api import MetpetAPI
from utilities import paginate_model


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search/')
def search():
    filters = dict(request.args)
    filter_dictionary = {}

    for key in filters:
        if filters[key][0]:
          if key != "resource":
            filter_dictionary[key] = ",".join(filters[key])

    if request.args.get('resource') == 'sample':
        url = url_for('samples') + '?' + urlencode(filter_dictionary)
        return redirect(url)
    elif request.args.get('resource') == 'chemicalanalysis':
        url = url_for('chemical_analyses') + '?' + urlencode(filter_dictionary)
        return redirect(url)


    api = MetpetAPI(None, None).api

    region_list = []
    collector_list = []
    reference_list = []
    metamorphic_region_list = []
    all_regions = api.region.get(params={'order_by': 'name'}).data['objects']
    all_samples = api.sample.get().data['objects']
    all_references = api.reference.get(params={'order_by': 'name'}).data['objects']
    all_metamorphic_regions = api.metamorphic_region.get(params={'order_by': 'name'}).data['objects']

    for region in all_regions:
        region_list.append(region['name'])
    for sample in all_samples:
        if sample['collector'] and sample['collector'] not in collector_list:
            collector_list.append(unicode(sample['collector']))
    for ref in all_references:
        reference_list.append(ref['name'])
    for mmr in all_metamorphic_regions:
        metamorphic_region_list.append(mmr['name'])

    return render_template('search_form.html',
                            samples=[],
                            query='',
                            regions=region_list,
                            provencances=collector_list,
                            references=reference_list,
                            mmrs=metamorphic_region_list)


@app.route('/samples/')
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
        first_page_url = url_for('samples') + '?' + urlencode(first_page_filters)
    else:
        first_page_url = url_for('samples') + urlencode(first_page_filters)

    return render_template('samples.html',
                            samples=samples,
                            next_url=next,
                            prev_url=previous,
                            total=total_count,
                            first_page=first_page_url,
                            last_page=last)


@app.route('/sample/<int:id>')
def sample(id):
    api = MetpetAPI(None, None).api
    sample = api.sample.get(id).data

    location = sample['location'].split(" ")
    longtitude = location[1].replace("(","")
    latitude = location[2].replace(")","")
    loc = [longtitude, latitude]

    filter = {"sample__sample_id": sample['sample_id'], "limit": "0"}

    subsamples = api.subsample.get(params=filter).data['objects']

    aliases = api.sample_alias.get(params=filter).data['objects']
    aliases_str = [alias['alias'] for alias in aliases]

    regions = [region['name'] for region in sample['regions']]
    metamorphic_regions = [metamorphic_region['name'] for metamorphic_region in sample['metamorphic_regions']]
    metamorphic_grades = [metamorphic_grade['name'] for metamorphic_grade in sample['metamorphic_grades']]
    references = [reference['name'] for reference in sample['references']]
    minerals = [mineral['name'] for mineral in sample['minerals']]

    if sample:
        return render_template('sample.html',
                                sample=sample,
                                location=loc,
                                minerals=(', ').join(minerals),
                                regions=(', ').join(regions),
                                references=(', ').join(references),
                                metamorphic_grades=(', ').join(metamorphic_grades),
                                metamorphic_regions=(', ').join(metamorphic_regions),
                                aliases=(', ').join(aliases_str),
                                subsamples=subsamples)
    else:
        return HttpResponse("Sample does not Exist")

@app.route('/subsample/<int:id>')
def subsample(id):
    api = MetpetAPI(None, None).api
    subsample = api.subsample.get(id).data
    user = api.user.get(subsample['user']['user_id']).data

    filter = {"subsample__subsample_id": subsample['subsample_id'],
              "limit": "0"}
    chemical_analyses = api.chemical_analysis.get(params=filter).data['objects']

    if subsample:
        return render_template('subsample.html',
                                subsample=subsample,
                                user=user,
                                chemical_analyses=chemical_analyses,
                                sample_id=subsample['sample'].split('/')[-2])
    else:
        return HttpResponse("Subsample does not Exist")


@app.route('/chemical_analyses/')
def chemical_analyses():
    api = MetpetAPI(None, None).api

    filters = ast.literal_eval(json.dumps(request.args))
    print(filters)
    offset = request.args.get('offset', 0)
    filters['offset'] = offset

    data = api.chemical_analysis.get(params=filters)
    next, previous, last, total_count = paginate_model('chemical_analyses',
                                                        data, filters)
    chemical_analyses = data.data['objects']

    first_page_filters = filters
    del first_page_filters['offset']

    if filters:
        first_page_url = url_for('chemical_analyses') + '?' + urlencode(first_page_filters)
    else:
        first_page_url = url_for('chemical_analyses') + urlencode(first_page_filters)

    return render_template('chemical_analyses.html',
                            chemical_analyses=chemical_analyses,
                            next_url=next,
                            prev_url=previous,
                            total=total_count,
                            first_page=first_page_url,
                            last_page=last)


@app.route('/chemical_analysis/<int:id>')
def chemical_analysis(id):
    url = env('API_HOST') + '/chemical_analysis/{0}'.format(id)
    response = get(url)
    return render_template('chemical_analysis.html',
                            data=response.json())


if __name__ == '__main__':
    dotenv.read_dotenv('../app_variables.env')
    app.run(debug=True)
