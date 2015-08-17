import dotenv
import json
from ast import literal_eval
from getenv import env
from requests import get, post
from urllib import urlencode
from urllib2 import urlopen
from flask import (
    Flask,
    request,
    render_template,
    url_for,
    redirect,
    flash,
    session
)
from flask_mail import Mail, Message
from forms import (
    LoginForm,
    RequestPasswordResetForm,
    PasswordResetForm,
    EditForm,
    EditChemForm
)
from lib.api import MetpetAPI
from utilities import paginate_model

mail = Mail()
metpet_ui = Flask(__name__)
metpet_ui.config.from_object('config')
mail.init_app(metpet_ui)


@metpet_ui.route('/')
def index():
    return render_template('index.html')


@metpet_ui.route('/search/')
def search():
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = {}
    for key in dict(request.args):
        if dict(request.args)[key][0] and key != 'resource':
            filters[key] = (',').join(dict(request.args)[key])

    if request.args.get('resource') == 'sample':
        #get samples with filters
        url = url_for('samples')+'?'+urlencode(filters)
        return redirect(url)

    if request.args.get('resource') == 'chemicalanalysis':
        #get chemical analyses given sample filters
        if 'minerals_and' in filters:
            del filters['minerals_and']
        url = url_for('chemical_analyses')+'?'+urlencode(filters)+'&sample_filters=True'
        return redirect(url)

    rock_types = json.loads(urlopen(env('API_DRF_HOST')+'/rock_types/?fields=name&page_size=40&format=json').read())['results']
    regions = json.loads(urlopen(env('API_DRF_HOST')+'/regions/?fields=name&page_size=2000&format=json').read())['results']
    minerals = json.loads(urlopen(env('API_DRF_HOST')+'/minerals/?fields=name&page_size=200&format=json').read())['results']
    references = json.loads(urlopen(env('API_DRF_HOST')+'/references/?fields=name&page_size=1100&format=json').read())['results']
    metamorphic_regions = json.loads(urlopen(env('API_DRF_HOST')+'/metamorphic_regions/?fields=name&page_size=240&format=json').read())['results']
    metamorphic_grades = json.loads(urlopen(env('API_DRF_HOST')+'/metamorphic_grades/?fields=name&page_size=30&format=json').read())['results']
    collectors = json.loads(urlopen(env('API_DRF_HOST')+'/collectors/?fields=name&page_size=140&format=json').read())['results']

    countries = set()
    igsns = set()
    numbers = set()
    owners = set()
    fields = 'country,sesar_number,number,public_data,owner'
    api_samples = json.loads(urlopen(env('API_DRF_HOST')+'/samples/?fields='+fields+'&page_size=2000&format=json').read())
    #while api_samples['next']:
    for sample in api_samples['results']:
        countries.add(sample['country'])
        igsns.add(sample['sesar_number'])
        numbers.add(sample['number'])
        if sample['public_data']:
            owners.add(sample['owner']['name'])
    #    api_samples = json.loads(urlopen(api_samples['next']).read())

    #if email:
    #    logged_in_user = api.user.get(params={'email': email, 'fields': 'user_id,name'}).data['results']
    #    owners.add(logged_in_user[0]['name'])

    return render_template('search_form.html',
        countries=countries,
        igsns=igsns,
        metamorphic_grades=metamorphic_grades,
        metamorphic_regions=metamorphic_regions,
        minerals=minerals,
        numbers=numbers,
        owners=owners,
        collectors=collectors,
        references=references,
        regions=regions,
        rock_types=rock_types
    )


@metpet_ui.route('/search-chemistry/')
def search_chemistry():
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = {}
    for key in dict(request.args):
        if dict(request.args)[key][0] and key != 'resource':
            filters[key] = (',').join(dict(request.args)[key])

    if request.args.get('resource') == 'chemicalanalysis':
        url = url_for('chemical_analyses')+'?'+urlencode(filters)
        return redirect(url)

    if request.args.get('resource') == 'sample':
        filters['fields'] = 'subsample'
        chem_results = []
        if 'all_results' in filters:
            chemicals = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/?'+urlencode(filters)+'&page_size=2000&format=json').read())
            chem_results = chemicals['results']
            while chemicals['next']:
                chemicals = json.loads(urlopen(chemicals['next']).read())
                chem_results += chemicals['results']
        else:
            chem_results = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/?'+urlencode(filters)+'&format=json').read())['results']
        
        numbers = set()
        for c in chem_results:
            numbers.add(c['subsample']['sample'])#need number not id
        url = url_for('samples')+'?'+urlencode({'numbers': numbers})
        return redirect(url)

    minerals = json.loads(urlopen(env('API_DRF_HOST')+'/minerals/?fields=name&page_size=200&format=json').read())['results']
    oxides = json.loads(urlopen(env('API_DRF_HOST')+'/oxides/?fields=species&page_size=100&format=json').read())['results']
    elements = json.loads(urlopen(env('API_DRF_HOST')+'/elements/?fields=name,symbol&page_size=120&format=json').read())['results']

    return render_template('chemical_search_form.html',
        elements=elements,
        oxides=oxides,
        minerals=minerals)


@metpet_ui.route('/samples/')
def samples():
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    next = previous = last = total_count = None
    filters = literal_eval(json.dumps(request.args))

    sample_results = []
    if 'all_results' in filters:
        samples = json.loads(urlopen(env('API_DRF_HOST')+'/samples/?'+urlencode(filters)+'&page_size=2000&format=json').read())
        sample_results = samples['results']
        while samples['next']:
            samples = json.loads(urlopen(samples['next']).read())
            sample_results += samples['results']
        next, previous, last, total_count = None, None, url_for('samples')+'?'+urlencode(filters), samples['count']
    else:
        samples = json.loads(urlopen(env('API_DRF_HOST')+'/samples/?'+urlencode(filters)+'&format=json').read())
        sample_results = samples['results']
        next, previous, last, total_count = paginate_model('samples', samples, filters)

    for s in sample_results:
        pos = s['location_coords'].split(" ")
        s['location_coords'] = [round(float(pos[2].replace(")","")),5),round(float(pos[1].replace("(","")),5)]
        s['minerals'] = (', ').join([m['name'] for m in s['minerals']])
        if s['collection_date']:
            s['collection_date'] = s['collection_date'][:-10]

    return render_template('samples.html',
        samples=sample_results,
        showmap='showmap' in filters,
        next_url=next,
        prev_url=previous,
        total=total_count,
        first_page=url_for('samples')+'?'+urlencode(filters),
        last_page=last)


@metpet_ui.route('/sample/<string:id>')
def sample(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    sample = json.loads(urlopen(env('API_DRF_HOST')+'/samples/'+id+'?format=json').read())
    if not sample:
        return HttpResponse("Sample does not exist")

    pos = sample['location_coords'].split(" ")
    sample['location_coords'] = [round(float(pos[2].replace(")","")),5), round(float(pos[1].replace("(","")),5)]
    sample['regions'] = (', ').join(sample['regions'])
    sample['references'] = (', ').join(sample['references'])
    sample['metamorphic_regions'] = (', ').join([mmr['name'] for mmr in sample['metamorphic_regions']])
    sample['metamorphic_grades'] = (', ').join([mmg['name'] for mmg in sample['metamorphic_grades']])
    sample['minerals'] = (', ').join([m['name'] for m in sample['minerals']])
    sample['aliases'] = (', ').join([a['name'] for a in sample['aliases']])
    if sample['collection_date']:
        sample['collection_date'] = sample['collection_date'][:-10]

    subsamples = json.loads(urlopen(env('API_DRF_HOST')+'/subsamples/?'+urlencode({"samples": sample['id']})+'&format=json').read())['results']

    return render_template('sample.html',
        sample=sample,
        subsamples=subsamples
    )

@metpet_ui.route('/subsample/<string:id>')
def subsample(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    subsample = json.loads(urlopen(env('API_DRF_HOST')+'/subsamples/'+id+'?format=json').read())
    if not subsample:
        return HttpResponse("Subsample does not exist")

    subsample['sample']['number'] = json.loads(urlopen(env('API_DRF_HOST')+'/samples/'+subsample['sample']['id']+'?fields=number&format=json').read())['number']
    chemical_analyses = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/?'+urlencode({"subsample_id": subsample['id']})+'&format=json').read())['results']

    return render_template('subsample.html',
        subsample=subsample,
        chemical_analyses=chemical_analyses
    )


@metpet_ui.route('/edit_sample/<string:id>', methods = ['GET','POST'])
def edit_sample(id):
    form = EditForm()
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    sample = json.loads(urlopen(env('API_DRF_HOST')+'/samples/'+id+'?format=json').read())

    rock_types = json.loads(urlopen(env('API_DRF_HOST')+'/rock_types/?fields=name&page_size=40&format=json').read())['results']
    api_regions = json.loads(urlopen(env('API_DRF_HOST')+'/regions/?fields=name&page_size=2000&format=json').read())['results']
    api_minerals = json.loads(urlopen(env('API_DRF_HOST')+'/minerals/?fields=name&page_size=200&format=json').read())['results']

    metamorphic_regions = set()
    metamorphic_grades = set()
    api_samples = json.loads(urlopen(env('API_DRF_HOST')+'/samples/?fields=metamorphic_regions,metamorphic_grades&page_size=2000&format=json').read())
    #while api_samples['next']:
    for sample in api_samples['results']:
        for mmr in sample['metamorphic_regions']:
            metamorphic_regions.add(mmr['name'])
        for mmg in sample['metamorphic_grades']:
            metamorphic_grades.add(mmg['name'])
    #    api_samples = json.loads(urlopen(api_samples['next']).read())

    location = sample['location_coords'].split(" ")

    form.owner.data = sample['owner']['name']
    form.public.data = sample['public_data']
    form.location_text.data = sample['location_text']
    form.collector.data = sample['collector']
    form.rock_type.data = sample['rock_type']['rock_type']
    form.rock_type.choices = [(r['rock_type'],r['rock_type']) for r in rock_types]
    form.country.data = sample['country']
    form.date_collected.data = sample['collection_date']
    form.longitude.data = location[1].replace("(","")
    form.latitude.data = location[2].replace(")","")
    form.minerals.data = [mineral['name'] for mineral in sample['minerals']]
    form.minerals.choices = [(m, m) for m in minerals]
    form.metamorphic_grades.choices = [(m['name'],m['name']) for m in metamorphic_grades]
    form.metamorphic_regions.choices = [(m['name'],m['name']) for m in metamorphic_regions]
    for r in range(len(form.region.entries)):
        form.region.pop_entry()
    for r in [region['name'] for region in sample['regions']]:
        form.region.append_entry(r)
    if sample['metamorphic_grades']:
        form.metamorphic_grades.data = sample['metamorphic_grades'][0]['name']
    if sample['metamorphic_regions']:
        form.metamorphic_regions.data = sample['metamorphic_regions'][0]['name']

    if form.validate_on_submit():
        rock = ''
        rock_select = form.rock_type.data
        for r in rock_types:
            if r['rock_type'] == rock_select:
                rock = r

        met_grades = []
        mmg_select = form.metamorphic_grades.data
        for mmg in metamorphic_grades:
            if mmg_select == mmg['name']:
                met_grades.append(mmg)

        mins = []
        mineral_select = form.minerals.data
        for m in api_minerals:
            if m['name'] in mineral_select:
                mins.append(m)

        regs = []
        region_select = form.region.data
        for r in api_regions:
            if r['name'] in region_select:
                regs.append(r)

        new_sample = json.loads(urlopen(env('API_DRF_HOST')+'/samples/'+id+'?format=json').read())
        new_sample.data['rock_type'] = rock
        new_sample.data['metamorphic_grades'] = met_grades
        new_sample.data['minerals'] = mins
        new_sample.data['regions'] = regs
        new_sample.data['location'] = "POINT (" + str(form.longitude.data) + " " + str(form.latitude.data) + ")"
        new_sample.data['user']['name'] = form.owner.data
        new_sample.data['public_data'] = form.public.data
        new_sample.data['location_text'] = form.location_text.data
        new_sample.data['collection_date'] = form.date_collected.data
        new_sample.data['collector'] = form.collector.data
        new_sample.data['country'] = form.country.data
        if form.date_collected.data != "":
            new_sample.data['collection_date'] = form.date_collected.data
        else:
            new_sample.data['collection_date'] = None

        new_sample = api.samples.put(id, new_sample.data)
        return redirect(url_for('sample', id=id))

    return render_template('edit_sample.html',
        form = form,
        id = sample['number'],
        regions = api_regions,
        minerals = sorted(api_minerals.values(), key=lambda k: k['name']),
        api_key = api_key
    )

@metpet_ui.route('/new_sample/', methods = ['GET', 'POST'])
def new_sample():
    form = EditForm();
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    rock_types = json.loads(urlopen(env('API_DRF_HOST')+'/rock_types/?fields=name&page_size=40&format=json').read())['results']
    api_regions = json.loads(urlopen(env('API_DRF_HOST')+'/regions/?fields=name&page_size=2000&format=json').read())['results']
    api_minerals = json.loads(urlopen(env('API_DRF_HOST')+'/minerals/?fields=name&page_size=200&format=json').read())['results']

    metamorphic_regions = set()
    metamorphic_grades = set()
    api_samples = json.loads(urlopen(env('API_DRF_HOST')+'/samples/?fields=metamorphic_regions,metamorphic_grades&page_size=2000&format=json').read())
    #while api_samples['next']:
    for sample in api_samples['results']:
        for mmr in sample['metamorphic_regions']:
            metamorphic_regions.add(mmr['name'])
        for mmg in sample['metamorphic_grades']:
            metamorphic_grades.add(mmg['name'])
    #    api_samples = json.loads(urlopen(api_samples['next']).read())

    form.rock_type.choices = [(r['rock_type'],r['rock_type']) for r in rock_types]
    form.metamorphic_grades.choices = [(m['name'],m['name']) for m in metamorphic_grades]
    form.metamorphic_regions.choices = [(m['name'],m['name']) for m in metamorphic_regions]
    form.minerals.choices = []

    if form.validate_on_submit():
        rock = ''
        rock_select = form.rock_type.data
        for r in rock_types:
            if r['rock_type'] == rock_select:
                rock = r

        met_grades = []
        mmg_select = form.metamorphic_grades.data
        for mmg in metamorphic_grades:
            if mmg_select == mmg['name']:
                met_grades.append(mmg)

        mins = []
        mineral_select = form.minerals.data
        for m in api_minerals:
            if m['name'] in mineral_select:
                mins.append(m)

        regs = []
        region_select = form.region.data
        for r in api_regions:
            if r['name'] in region_select:
                regs.append(r)

        sample_data = {}
        sample_data[u'rock_type'] = rock
        sample_data[u'metamorphic_grades'] = met_grades
        sample_data[u'minerals'] = mins
        sample_data[u'regions'] = regs
        sample_data[u'location'] = u"POINT (" + str(form.longitude.data) + " " + str(form.latitude.data) + ")"
        sample_data[u'user']['name'] = form.owner.data
        sample_data[u'public_data'] = form.public.data
        sample_data[u'location_text'] = form.location_text.data
        sample_data[u'collection_date'] = form.date_collected.data
        sample_data[u'collector'] = form.collector.data
        sample_data[u'country'] = form.country.data
        
        sample_data = api.samples.post(sample_data)
        return redirect(url_for('search'))

    return render_template('edit_sample.html',
        form = form,
        id = '',
        regions = api_regions,
        minerals = sorted(api_minerals.values(), key=lambda k: k['name']),
        api_key = api_key
    )


@metpet_ui.route('/chemical_analyses/')
def chemical_analyses():
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    next = previous = last = total_count = None
    filters = literal_eval(json.dumps(request.args))
    filters['fields'] = 'subsample,id,analysis_method,mineral,analyst,analysis_date,reference_x,reference_y,total'

    chem_results = []
    if 'all_results' in filters:
        chemicals = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/?'+urlencode(filters)+'&page_size=2000&format=json').read())
        chem_results = chemicals['results']
        while chemicals['next']:
            chemicals = json.loads(urlopen(chemicals['next']).read())
            chem_results += chemicals['results']
        next, previous, last, total_count = None, None, url_for('chemical_analyses')+'?'+urlencode(filters), chemicals['count']
    else:
        chemicals = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/?'+urlencode(filters)+'&format=json').read())
        chem_results = chemicals['results']
        next, previous, last, total_count = paginate_model('chemical_analyses', chemicals, filters)

    for c in chem_results:
        c['sample'] = json.loads(urlopen(env('API_DRF_HOST')+'/samples/'+c['subsample']['sample']+'?fields=number&format=json').read())
        if c['analysis_date']:
            c['analysis_date'] = c['analysis_date'][:-10]

    return render_template('chemical_analyses.html',
        chemical_analyses=chem_results,
        next_url=next,
        prev_url=previous,
        total=total_count,
        first_page=url_for('chemical_analyses')+'?'+urlencode(filters),
        last_page=last
    )


@metpet_ui.route('/chemical_analysis/<string:id>')
def chemical_analysis(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api
    
    analysis = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/'+id+'?format=json').read())
    if not analysis:
        return HttpResponse("Chemical analysis does not exist")
    analysis['sample'] = json.loads(urlopen(env('API_DRF_HOST')+'/samples/'+analysis['subsample']['sample']+'?fields=number&format=json').read())

    return render_template('chemical_analysis.html',
        analysis=analysis
    )


@metpet_ui.route('/edit_chemical/<string:id>', methods = ['GET','POST'])
def edit_chemical(id):
    form = EditChemForm()
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api
    api.auth(user=email,api_key=api_key)

    chemical = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/'+id+'?format=json').read())

    api_minerals = json.loads(urlopen(env('API_DRF_HOST')+'/minerals/?fields=name&page_size=200&format=json').read())['results']
    api_oxides = []#json.loads(urlopen(env('API_DRF_HOST')+'/oxides/?fields=species&page_size=50&format=json').read())['results']
    api_elements = []#json.loads(urlopen(env('API_DRF_HOST')+'/elements/?fields=name,symbol&page_size=50&format=json').read())['results']
    chemicals = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/?fields=elements,oxides&page_size=1000&format=json').read())
    #while chemicals['next']:
    for c in chemicals['results']:
        for o in c['oxides']:
            if {'species': o['species']} not in api_oxides:
                api_oxides.append({'species': o['species']})
        for e in c['elements']:
            if {'name': e['name'], 'symbol': e['symbol']} not in api_elements:
                api_elements.append({'name': e['name'], 'symbol': e['symbol']})
    #    chemicals = json.loads(urlopen(chemicals['next']).read())

    elements = [e['name'] for e in api_elements if e['resource_uri'] in chemical['elements']]
    oxides = [o['species'] for o in api_oxides if o['resource_uri'] in chemical['oxides']]

    params = {'email': email, 'api_key': api_key}
    pre = env('API_DRF_HOST')
    suf = '?format=json'
    user = get(pre+chemical['user']+suf, params=params).json()
    subsample = json.loads(urlopen(env('API_DRF_HOST')+'/subsamples/'+chemical['subsample']['id']+'?format=json').read())
    sample = json.loads(urlopen(env('API_DRF_HOST')+'/samples/'+chemical['subsample']['sample']+'?format=json').read())

    form.owner.data = user['name']
    form.point_number.data = chemical['spot_id']
    form.public.data = chemical['public_data']
    form.analysis_method.data = chemical['analysis_method']
    form.analyst.data = chemical['analyst']
    form.description.data = chemical['description']
    form.minerals.data = chemical['minerals']['name']
    form.minerals.choices = [(m,m) for m in api_minerals]
    form.total.data = chemical['total']
    form.StageX.data = chemical['stage_x']
    form.StageY.data = chemical['stage_y']
    for i in range(len(oxides)):
        form.oxides.append_entry(oxides[i])
        form.oxides[i].label = oxides[i]
    for i in range(len(elements)):
        form.elements.append_entry(elements[i])
        form.elements[i].label = elements[i]

    if form.validate_on_submit():
        new_sample = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/'+id+'?format=json').read())

        elements = [e for e in api_elements if e['name'] in form.elements.data]
        oxides = [o for o in api_oxides if o['species'] in form.oxides.data]

        mins = []
        mineral_select = form.minerals.data
        for m in api_minerals:
            if m['name'] in mineral_select:
                mins.append(m)

        new_sample.data['user'] = form.owner.data
        new_sample.data['spot_id'] = form.point_number.data
        new_sample.data['public_data'] = form.public.data
        new_sample.data['analysis_method'] = form.analysis_method.data
        new_sample.data['analyst'] = form.analyst.data
        new_sample.data['description'] = form.description.data
        new_sample.data['minerals'] = mins
        new_sample.data['total'] = form.total.data
        new_sample.data['stage_x'] = form.StageX.data
        new_sample.data['stage_y'] = form.StageY.data
        if oxides:
            new_sample.data['oxides'] = oxides
        if elements:
            new_sample.data['elements'] = elements

        new_sample = api.chemical_analysis.put(id, new_sample.data)
        return redirect(url_for('chemical_analysis', id=id))

    return render_template('edit_chemical.html',
        form = form,
        id = chemical['spot_id'],
        elements = api_elements,
        oxides = api_oxides,
        minerals = api_minerals,
        sample = sample,
        subsample = subsample,
        api_key = api_key
    )


@metpet_ui.route('/new_chemical/', methods = ['GET', 'POST'])
def new_chemical():
    form = EditChemForm()
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api
    api.auth(user=email,api_key=api_key)

    api_minerals = json.loads(urlopen(env('API_DRF_HOST')+'/minerals/?fields=name&page_size=200&format=json').read())['results']
    api_oxides = []#json.loads(urlopen(env('API_DRF_HOST')+'/oxides/?fields=species&page_size=50&format=json').read())['results']
    api_elements = []#json.loads(urlopen(env('API_DRF_HOST')+'/elements/?fields=name,symbol&page_size=50&format=json').read())['results']
    chemicals = json.loads(urlopen(env('API_DRF_HOST')+'/chemical_analyses/?fields=elements,oxides&page_size=1000&format=json').read())
    #while chemicals['next']:
    for c in chemicals['results']:
        for o in c['oxides']:
            if {'species': o['species']} not in api_oxides:
                api_oxides.append({'species': o['species']})
        for e in c['elements']:
            if {'name': e['name'], 'symbol': e['symbol']} not in api_elements:
                api_elements.append({'name': e['name'], 'symbol': e['symbol']})
    #    chemicals = json.loads(urlopen(chemicals['next']).read())

    form.minerals.choices = [(m,m) for m in api_minerals]

    if form.validate_on_submit():
        elements = [e for e in api_elements if e['name'] in form.elements.data]
        oxides = [o for o in api_oxides if o['species'] in form.oxides.data]

        mins = []
        mineral_select = form.minerals.data
        for m in api_minerals:
            if m['name'] in mineral_select:
                mins.append(m)

        chem_data = {}
        chem_data.data['user'] = form.owner.data
        chem_data.data['spot_id'] = form.point_number.data
        chem_data.data['public_data'] = form.public.data
        chem_data.data['analysis_method'] = form.analysis_method.data
        chem_data.data['analyst'] = form.analyst.data
        chem_data.data['description'] = form.description.data
        chem_data.data['minerals'] = mins
        chem_data.data['total'] = form.total.data
        chem_data.data['stage_x'] = form.StageX.data
        chem_data.data['stage_y'] = form.StageY.data
        if oxides:
            chem_data.data['oxides'] = oxides
        if elements:
            chem_data.data['elements'] = elements

        chem_data = api.chemical_analysis.post(chem_data)
        return redirect(url_for('search_chemistry'))

    return render_template('edit_chemical.html',
        form = form,
        id = '',
        elements = api_elements,
        oxides = api_oxides,
        minerals = api_minerals,
        api_key = api_key
    )


@metpet_ui.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('api_key'):
        return redirect(url_for('search'))
    form = LoginForm()
    if form.validate_on_submit():
        payload = {'email': form.email.data, 'password': form.password.data}
        response =  post(env('API_DRF_HOST') + '/authenticate/', data=payload)
        if response.status_code == 200:
            data = json.loads(response.text)
            session['email'] = data['email']
            session['api_key'] = data['api_key']
            flash('Login successful!')
            return redirect(url_for('search'))
        else:
            flash('Authentication failed. Please try again.')
    return render_template('login.html', form=form)


@metpet_ui.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('api_key', None)
    flash('Logout successful.')
    return redirect(url_for('search'))


@metpet_ui.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        payload = {'email': form.email.data}
        response = post(env('API_DRF_HOST') + '/reset_password/', data=payload)
        if response.status_code == 200:
            data = json.loads(response.text)
            message = Message("Metpetdb: Reset Password", sender=env('DEFAULT_MAIL_SENDER'), recipients=[form.email.data])
            reset_url = url_for('reset_password', token=data['reset_token'], _external=True)
            message.body = render_template('reset_password_email.html', reset_url=reset_url)
            mail.send(message)
            flash('Please check your email for a link to reset your password')
            return redirect(url_for('login'))
        else:
            flash("Invalid email. Please try again.")
    return render_template('request_password_reset.html', form=form)


@metpet_ui.route('/reset_password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    form = PasswordResetForm()
    if form.validate_on_submit():
        payload = {'token': form.token.data, 'password': form.password.data}
        response = post(env('API_DRF_HOST') + '/reset_password/', data=payload)
        if response.status_code == 200:
            data = json.loads(response.text)
            session['email'] = data['email']
            session['api_key'] = data['api_key']
            flash('Password reset successful!')
            return redirect(url_for('index'))
        else:
            flash('Password reset failed. Please try again.')
            return redirect(url_for('request_password_reset'))

    if token:
        response = get(env('API_DRF_HOST') + '/reset_password/' + token)
        if response.status_code == 200:
            form = PasswordResetForm(token=token)
            return render_template('reset_password.html', form=form)
    flash('Password reset failed. Please try again.')
    return redirect(url_for('request_reset_password'))


@metpet_ui.route('/user/<string:id>')
def user(id):
    user = json.loads(urlopen(env('API_DRF_HOST')+'/users/'+id+'?format=json').read())
    if not user:
        return HttpResponse("User does not exist")
    return render_template('user.html', user=user)


if __name__ == '__main__':
    dotenv.read_dotenv('../app_variables.env')
    metpet_ui.run(debug=True)
