import ast, StringIO, base64, json, unicodedata
from urllib import urlencode
from requests import get, post
from itsdangerous import URLSafeTimedSerializer

from flask import Flask, request, render_template, url_for, redirect, flash, session
from flask_mail import Mail, Message
import dotenv, drest
from getenv import env

from api import MetpetAPI
from forms import LoginForm, RequestPasswordResetForm, PasswordResetForm
from utilities import paginate_model

app = Flask(__name__)
app.config.from_object('config')
mail = Mail(app)

@app.route('/')
def index():
    return render_template('index.html')

def getAPIres(params, api_call):
    results = []
    params['offset'] = 0
    l = -1
    while len(results)-l > 0:
        l = len(results)
        results += api_call.get(params=params).data['objects']
        params['offset'] += 1000
    return results

@app.route('/search/')
def search():
    print "REQ ARGS"
    print request.args
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = dict(request.args)
    filter_dictionary = {}
    for key in filters:
        if filters[key][0]:
          if key != "resource":
            filter_dictionary[key] = (',').join(filters[key])

    #If minerals and AND are selected, intersect samples for each mineral with other filters
    if request.args.getlist('minerals__in') and len(request.args.getlist('minerals__in')) > 1 and request.args.get('mineralandor') == 'and':
        fields = 'sample_id'
        if request.args.get('resource') == 'sample':
            fields += ',user__name,collector,number,public_data,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date'
        params = {'fields': fields, 'limit': 0}
        for key in filter_dictionary:
            if key != "minerals__in" and key != "search_filters" and key != "fields" and key != "mineralandor":
                params[key] = filter_dictionary[key]
        sample_res_ids = set()
        sample_results = []
        first = True
        for m in request.args.getlist('minerals__in'):
            params['minerals__in'] = m
            samples = getAPIres(params, api.sample)
            if first:
                sample_results = samples
                first = False
            else:
                #intersect samples and sample_results
                sample_results = [s for s in samples if s['sample_id'] in sample_res_ids]
                sample_res_ids = set()
            for s in sample_results:
                sample_res_ids.add(s['sample_id'])

        if request.args.get('resource') == 'sample':
            #Build mineral list string for rendering results
            for s in sample_results:
                s['mineral_list'] = (', ').join(s['minerals__name'])
            return render_template('samples_mineral_and_samples.html', samples=sample_results)

        elif request.args.get('resource') == 'chemicalanalysis':
            #Get subsample IDs using sample IDs
            sample_resources = ((',').join(str(s['sample_id']) for s in sample_results))
            subsamples = getAPIres({'sample__in': sample_resources, 'fields': 'subsample_id', 'limit': 0}, api.subsample)
            subsample_resources = ((',').join(str(s['subsample_id']) for s in subsamples))
            #Get chemical analyses using subsample IDs
            chemical_analyses_results = getAPIres({'subsample__in': subsample_resources,
                'fields': 'chemical_analysis_id,spot_id,public_data,analysis_method,where_done,analyst,analysis_date,reference_x,reference_y,total,mineral',
                'limit': 0}, api.chemical_analysis)
            return render_template('samples_mineral_and_chemical_analyses.html', chemical_analyses=chemical_analyses_results)

    #If one or no minerals or OR selected
    if request.args.get('resource') == 'sample':
        #get samples with filters
        url = url_for('samples') + '?' + urlencode(filter_dictionary)
        return redirect(url)

    elif request.args.get('resource') == 'chemicalanalysis':
        #get chemical analyses with get-chem-analyses-given-sample-filters
        request_obj = drest.api.API(baseurl=env('API_HOST'))
        headers = None
        if email and api_key:
            headers = {'email': email, 'api_key': api_key}
        #only returns 1000 ids: how to fix?
        response = request_obj.make_request('GET','/get-chem-analyses-given-sample-filters/',
            params=filter_dictionary,headers=headers)
        ids = response.data['chemical_analysis_ids']
        url = url_for('chemical_analyses') + '?' + urlencode({'chemical_analysis_id__in': ids})
        return redirect(url)

    rock_types = api.rock_type.get(params={'order_by': 'rock_type', 'limit': 0}).data['objects']
    regions = api.region.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    references = getAPIres({'order_by': 'name', 'limit': 0}, api.reference)
    metamorphic_regions = api.metamorphic_region.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    metamorphic_grades = api.metamorphic_grade.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    samples = getAPIres({'fields': 'user__user_id,user__name,collector,number,sesar_number,country,public_data', 'limit': 0}, api.sample)
    mineral_relationships = api.mineral_relationship.get(params={'limit': 0, 
        'fields': 'parent_mineral__mineral_id,parent_mineral__name,child_mineral__mineral_id,child_mineral__name'}).data['objects']

    parents = children = set()
    for m in mineral_relationships:
        parents.add((m['parent_mineral__name'], m['parent_mineral__mineral_id']))
        children.add((m['child_mineral__name'], m['child_mineral__mineral_id']))
    mineralroots = parents - children
    m_list = parents.union(children)

    mineralnodes = []
    for (name, mid) in mineralroots:
        mineralnodes.append({"id": name, "parent": "#", "text": name, "mineral_id": mid})
    for m in mineral_relationships:
        mineralnodes.append({"id": m['child_mineral__name'], "parent": m['parent_mineral__name'],
            "text": m['child_mineral__name'], "mineral_id": m['child_mineral__mineral_id']})

    mineral_list = []
    for (name, mid) in m_list:
        mineral_list.append({"name": name, "id": mid})
    region_list = []
    for region in regions:
        region_list.append(region['name'])
    reference_list = []
    for ref in references:
        reference_list.append(ref['name'])
    metamorphic_region_list = []
    for mmr in metamorphic_regions:
        metamorphic_region_list.append(mmr['name'])
    metamorphic_grade_list = []
    for mmg in metamorphic_grades:
        metamorphic_grade_list.append(mmg['name'])

    owner_dict = {}
    if email:
        logged_in_user = api.user.get(params={'email': email, 'fields': 'user_id,name'}).data['objects']
        owner_dict[logged_in_user[0]['user_id']] = logged_in_user[0]['name']

    collector_list = country_list = set()
    igsn_list = number_list = []
    for sample in samples:
        collector_list.add(sample['collector'])
        country_list.add(sample['country'])
        if sample['sesar_number']:
            igsn_list.append(sample['sesar_number'])
        if sample['number']:
            number_list.append(sample['number'])
        if sample['public_data'] == 'Y':
            if not sample['user__user_id'] in owner_dict:
                owner_dict[sample['user__user_id']] = sample['user__name']

    return render_template('search_form.html',
        countries=sorted(list(country_list)),
        igsns=sorted(igsn_list),
        metamorphic_grades=metamorphic_grade_list,
        metamorphic_regions=metamorphic_region_list,
        mineralrelationships=json.dumps(mineral_relationships),
        minerals=sorted(mineral_list, key=lambda k: k['name']),
        mineral_nodes=json.dumps(sorted(mineralnodes, key=lambda k: k['text'])),
        numbers=sorted(number_list),
        owners=owner_dict,
        provenances=sorted(list(collector_list)),
        query='',
        references=reference_list,
        regions=region_list,
        rock_types=rock_types)


@app.route('/search-chemistry/')
def search_chemistry():
    print "REQ ARGS"
    print request.args
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = dict(request.args)
    filter_dictionary = {}
    for key in filters:
        if filters[key][0]:
          if key != "resource":
            filter_dictionary[key] = ",".join(filters[key])

    #If chem analysis data is passed, return results
    if 'squirrel' not in request.args:
        if request.args.get('resource') == 'chemicalanalysis':
            if request.args.get("results"):
                filter_dictionary['results'] = eval(unicodedata.normalize('NFKD', filter_dictionary['results']).encode('ascii','ignore').replace("null","None"))
                return render_template('chemical_analyses.html', chemical_analyses=filter_dictionary['results'])
            else:
                return render_template('chemical_analyses.html')

        elif request.args.get('resource') == 'sample':
            if request.args.get("results"):
                filter_dictionary['results'] = eval(unicodedata.normalize('NFKD', filter_dictionary['results']).encode('ascii','ignore').replace("null","None"))
                return render_template('samples.html', samples=filter_dictionary['results'])
            else:
                return render_template('samples.html')

    #If chemistry row data is passed, get (M, E1) / (M, O1)
    if request.args.get('squirrel') == 'squirrel':
        if 'elements__element_id__in' in request.args:
            element = request.args.get('elements__element_id__in')
        elif 'oxides__oxide_id__in' in request.args:
            oxide = request.args.get('oxides__oxide_id__in')
        mineral_ids = (',').join(request.args.getlist('minerals__in'))            
        cid_list = []

    #Get chemical analyses for (E, M)
        if 'elements__element_id__in' in request.args and request.args.get('resource') == 'chemicalanalysis':
            e_chem_analysis_ids = api.chemical_analysis.get(params={'elements__element_id__in': element, 'minerals__in': mineral_ids, 'fields': 'chemical_analysis_id,spot_id,public_data,analysis_method,mineral__name,where_done,analyst,analysis_date,reference_x,reference_y,total,chemical_analysis_id', 'limit': 0}).data['objects']

            for cid in e_chem_analysis_ids:
                cid_list.append(cid)
            return json.dumps(cid_list)
    
    #Get chemical analyses for (O, M)
        elif 'oxides__oxide_id__in' in request.args and request.args.get('resource') == 'chemicalanalysis':
            o_chem_analysis_ids = api.chemical_analysis.get(params={'oxides__oxide_id__in': oxide, 'minerals__in': mineral_ids, 'fields': 'chemical_analysis_id,spot_id,public_data,analysis_method,mineral__name,where_done,analyst,analysis_date,reference_x,reference_y,total,chemical_analysis_id', 'limit': 0}).data['objects']
            for cid in o_chem_analysis_ids:
                cid_list.append(cid)
            return json.dumps(cid_list)

    #Get samples for (E, M)
    elif 'elements__element_id__in' in request.args and request.args.get('resource') == 'sample':
        subsample_resources = api.chemical_analysis.get(params={'elements__element_id__in': element, 'minerals__in': mineral_ids, 'fields': 'subsample', 'limit': 0}).data['objects']
        subsample_ids = set()
        for s in subsample_resources:
            #Remove first 18 characters and trailing /
            subsample_id = s['subsample'].replace("Subsample #", "")
            subsample_ids.add(subsample_id)
        print subsample_ids

        sample_resources = api.subsample.get(params={'subsample_id__in': (',').join(str(s) for s in subsample_ids), 'fields': 'sample', 'limit':0}).data['objects']
        sample_ids = set()
        for s in sample_resources:
            #Remove first 18 characters and trailing /
            sample_id = s['sample'].replace("Sample #", "")
            sample_ids.add(sample_id)
        print sample_ids
        sample_results = api.sample.get(params={'sample_id__in': (',').join(str(s) for s in sample_ids), 'fields': 'sample_id,user__name,collector,number,public_data,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date', 'limit':0}).data['objects']
        print "S RESULTS"
        print sample_results
        return json.dumps(sample_results)

    #Get samples for (O, M)
    elif 'oxides__oxide_id__in' in request.args and request.args.get('resource') == 'sample':
        subsample_resources = api.chemical_analysis.get(params={'oxides__oxide_id__in': oxide, 'minerals__in': mineral_ids, 'fields': 'subsample', 'limit': 0}).data['objects']
        subsample_ids = set()
        for s in subsample_resources:
            #Remove first 18 characters and trailing /
            subsample_id = s['subsample'].replace("Subsample #", "")
            subsample_ids.add(subsample_id)
        print subsample_ids

        sample_resources = api.subsample.get(params={'subsample_id__in': (',').join(str(s) for s in subsample_ids), 'fields': 'sample', 'limit':0}).data['objects']
        sample_ids = set()
        for s in sample_resources:
            #Remove first 18 characters and trailing /
            sample_id = s['sample'].replace("Sample #", "")
            sample_ids.add(sample_id)
        print sample_ids
        sample_results = api.sample.get(params={'sample_id__in': (',').join(str(s) for s in sample_ids), 'fields': 'sample_id,user__name,collector,number,public_data,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date', 'limit':0}).data['objects']
        print "S RESULTS"
        print sample_results
        return json.dumps(sample_results)

    oxides = api.oxide.get(params={'limit': 0}).data['objects']
    elements = api.element.get(params={'limit': 0}).data['objects']
    mineral_relationships = api.mineral_relationship.get(params={'limit': 0,
        'fields': 'parent_mineral__mineral_id,parent_mineral__name,child_mineral__mineral_id,child_mineral__name'}).data['objects']

    parents = children = set()
    for m in mineral_relationships:
        parents.add((m['parent_mineral__name'], m['parent_mineral__mineral_id']))
        children.add((m['child_mineral__name'], m['child_mineral__mineral_id']))
    mineralroots = parents - children
    m_list = parents.union(children)

    mineralnodes = []
    for (name, mid) in mineralroots:
        mineralnodes.append({"id": name, "parent": "#", "text": name, "mineral_id": mid})
    for m in mineral_relationships:
        mineralnodes.append({"id": m['child_mineral__name'], "parent": m['parent_mineral__name'],
            "text": m['child_mineral__name'], "mineral_id": m['child_mineral__mineral_id']})

    mineral_list = []
    for (name, mid) in m_list:
        mineral_list.append({"name": name, "id": mid})

    return render_template('chemical_search_form.html',
        elements=sorted(elements, key=lambda k: k['name']),
        oxides=sorted(oxides, key=lambda k: k['species']),
        minerals=sorted(mineral_list, key=lambda k: k['name']),
        mineral_nodes=json.dumps(sorted(mineralnodes, key=lambda k: k['text'])))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('api_key'):
        return redirect(url_for('search'))
    form = LoginForm()
    if form.validate_on_submit():
        payload = {'email': form.email.data, 'password': form.password.data}
        response =  post(env('API_HOST') + '/authenticate/', data=payload)
        if response.status_code == 200:
            data = json.loads(response.text)
            session['email'] = data['email']
            session['api_key'] = data['api_key']
            flash('Login successful!')
            return redirect(url_for('search'))
        else:
            flash('Authentication failed. Please try again.')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('api_key', None)
    flash('Logout successful.')
    return redirect(url_for('search'))


@app.route('/request-password-reset', methods=['GET', 'POST'])
def request_reset_password():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        payload = {'email': form.email.data}
        response = post(env('API_HOST') + '/reset-password/', data=payload)
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


@app.route('/reset-password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    form = PasswordResetForm()
    if form.validate_on_submit():
        payload = {'token': form.token.data, 'password': form.password.data}
        response = post(env('API_HOST') + '/reset-password/', data=payload)
        if response.status_code == 200:
            data = json.loads(response.text)
            session['email'] = data['email']
            session['api_key'] = data['api_key']
            flash('Password reset successful!')
            return redirect(url_for('search'))
        else:
            flash('Password reset failed. Please try again.')
            return redirect(url_for('request_reset_password'))

    if token:
        response = get(env('API_HOST') + '/reset-password/' + token)
        if response.status_code == 200:
            form = PasswordResetForm(token=token)
            return render_template('reset_password.html', form=form)

    flash('Password reset failed. Please try again.')
    return redirect(url_for('request_reset_password'))


@app.route('/samples/')
def samples():
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = ast.literal_eval(json.dumps(request.args))
    offset = request.args.get('offset', 0)
    filters['offset'] = offset
    filters['fields'] = 'sample_id,number,user__name,public_data,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date'

    data = api.sample.get(params=filters)
    next, previous, last, total_count = paginate_model('samples', data, filters)

    samples = data.data['objects']
    for sample in samples:
        mineral_names = [str(m) for m in sample['minerals__name']]
        sample['mineral_list'] = (', ').join(mineral_names)

    first_page_url = url_for('samples') + '?' + urlencode(filters)

    return render_template('samples.html',
        samples=samples,
        next_url=next,
        prev_url=previous,
        total=total_count,
        first_page=first_page_url,
        last_page=last)


@app.route('/sample/<int:id>')
def sample(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

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
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    subsample = api.subsample.get(id).data
    user = api.user.get(subsample['user']['user_id']).data

    filter = {"subsample__subsample_id": subsample['subsample_id'], "limit": "0"}
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
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = ast.literal_eval(json.dumps(request.args))
    offset = request.args.get('offset', 0)
    filters['offset'] = offset

    data = api.chemical_analysis.get(params=filters)
    next, previous, last, total_count = paginate_model('chemical_analyses', data, filters)
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
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api
    
    response = api.chemical_analysis.get(id).data
    if 'subsample_id' not in response.keys():
        response['subsample_id'] = response['subsample'][18:-1]
    if 'sample_id' not in response.keys():
        response['sample_id'] = api.subsample.get(response['subsample_id']).data['sample'][15:-1]

    return render_template('chemical_analysis.html', data=response)


@app.route('/user/<int:id>')
def user(id):
    api = MetpetAPI(None, None).api
    user = api.user.get(id).data
    if user:
        return render_template('user.html', user=user)
    else:
        return HttpResponse("User does not Exist")


if __name__ == '__main__':
    dotenv.read_dotenv('../app_variables.env')
    app.run(debug=True)
