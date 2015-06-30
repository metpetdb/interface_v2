import ast
import dotenv
import drest
from getenv import env
import json
from requests import get, post
from urllib import urlencode

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
    EditChemForm,
    NewSample,
    NewChem
)
from api import MetpetAPI
from utilities import paginate_model

app = Flask(__name__)
app.config.from_object('config')
mail = Mail(app)


@app.route('/')
def index():
    return render_template('index.html')


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
          if key != "resource" and key != "all_results":
            filter_dictionary[key] = (',').join(filters[key])

    #If minerals and AND are selected, intersect samples for each mineral with other filters
    all_results = 'all_results' in filters.keys()
    if all_results or (request.args.getlist('minerals__in') and len(request.args.getlist('minerals__in')) > 1 and request.args.get('mineralandor') == 'and'):
        showmap = 'showmap' in filter_dictionary.keys()
        minerals = [m for m in request.args.getlist('minerals__in') if m != '']
        fields = 'sample_id,minerals__mineral_id'
        if request.args.get('resource') == 'sample':
            fields += ',collector,number,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date,location'

        params = {'fields': fields}
        for key in filter_dictionary:
            if key != "search_filters" and key != "fields" and key != "mineralandor":
                params[key] = filter_dictionary[key]
        params['offset'] = 0
        if minerals:
            params['minerals__in'] = minerals[0]

        sample_results = []
        while True:
            samples = api.sample.get(params=params).data['objects']
            if not samples:
                break
            i = 0
            while i < len(samples):
                good = True
                for m in minerals:
                    if 'minerals__mineral_id' not in samples[i].keys() or int(m) not in samples[i]['minerals__mineral_id']:
                        good = False
                if good:
                    sample_results.append(samples[i])
                i += 1
            params['offset'] += i

        if request.args.get('resource') == 'sample':
            #Build mineral list string for rendering results
            for s in sample_results:
                s['mineral_list'] = (', ').join(s['minerals__name'])
                pos = s['location'].split(" ")
                s['location'] = [round(float(pos[2].replace(")","")),5),round(float(pos[1].replace("(","")),5)]
            return render_template('samples.html',
                samples=sample_results,
                showmap=showmap,
                total=len(sample_results),
                first_page=request.url,
                last_page=request.url)

        elif request.args.get('resource') == 'chemicalanalysis':
            #Get subsample IDs using sample IDs
            samples = ((',').join(str(s['sample_id']) for s in sample_results))
            subsamples = api.subsample.get(params={'sample__in': samples, 'fields': 'subsample_id', 'limit': 0}).data['objects']
            subsamples = ((',').join(str(s['subsample_id']) for s in subsamples))
            #Get chemical analyses using subsample IDs
            fields = 'chemical_analysis_id,spot_id,public_data,analysis_method,where_done,analyst,analysis_date,reference_x,reference_y,total,mineral'
            chem_results = api.chemical_analysis.get(params={'subsample__in': subsamples, 'fields': fields, 'limit': 0}).data['objects']
            return render_template('chemical_analyses.html',
                chemical_analyses=chem_results,
                total=total+len(chem_results),
                first_page=request.url,
                last_page=request.url)

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
        ids = request_obj.make_request('GET','/get-chem-analyses-given-sample-filters/',params=filter_dictionary,headers=headers).data['chemical_analysis_ids']
        url = url_for('chemical_analyses') + '?' + urlencode({'chemical_analysis_id__in': ids})
        return redirect(url)

    rock_types = api.rock_type.get(params={'order_by': 'rock_type', 'limit': 0}).data['objects']
    regions = api.region.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    references = []
    params = {'order_by': 'name', 'offset': 0, 'limit': 0}
    l = -1
    while len(references)-l > 0:
        l = len(references)
        references += api.reference.get(params=params).data['objects']
        params['offset'] += 10000
    metamorphic_regions = api.metamorphic_region.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    metamorphic_grades = api.metamorphic_grade.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    samples = []
    params = {'fields': 'user__user_id,user__name,collector,number,sesar_number,country,public_data', 'offset': 0, 'limit': 0}
    l = -1
    while len(samples)-l > 0:
        l = len(samples)
        samples += api.sample.get(params=params).data['objects']
        params['offset'] += 10000
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


@app.route('/search_chemistry/')
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
          if key != "resource" and key != "all_results":
            filter_dictionary[key] = (",").join(filters[key])

    elements = [e for e in request.args.getlist('elements__element_id__in') if e != '']
    oxides = [o for o in request.args.getlist('oxides__oxide_id__in') if o != '']
    minerals = [m for m in request.args.getlist('minerals__in') if m != '']
    params = {'limit': 0}
    if elements:
        params['elements__element_id__in'] = elements[0]
    if oxides:
        params['oxides__oxide_id__in'] = oxides[0]
    if minerals:
        params['minerals__in'] = (',').join(minerals)
    chem_results = []

    if 'all_results' in filters.keys() or len(elements) > 1 or len(oxides) > 1:
        fields = 'elements__element_id,oxides__oxide_id,subsample'
        if request.args.get('resource') == 'chemicalanalysis':
            fields += ',chemical_analysis_id,analysis_method,mineral__name,analyst,analysis_date,reference_x,reference_y,total'
        params['fields'] = fields
        params['offset'] = 0
        if not minerals:
            params['minerals__in'] = (',').join(str(i) for i in range(185))

        while True:
            chem = api.chemical_analysis.get(params=params).data['objects']
            if not chem:
                break
            for j in range(len(chem)):
                good = True
                for e in elements:
                    if 'elements__element_id' not in chem[j].keys() or int(e) not in chem[j]['elements__element_id']:
                        good = False
                for o in oxides:
                    if 'oxides__oxide_id' not in chem[j].keys() or int(o) not in chem[j]['oxides__oxide_id']:
                        good = False
                if good:
                    chem_results.append(chem[j])
            params['offset'] += 1000

        if request.args.get('resource') == 'chemicalanalysis':
            for c in chem_results:
                sample_id = api.subsample.get(c['subsample'].replace("Subsample #","")).data['sample'][15:-1]
                c['sample_number'] = api.sample.get(sample_id).data['number']
            return render_template('chemical_analyses.html',
                chemical_analyses=chem_results,
                total=len(chem_results),
                first_page=request.url,
                last_page=request.url)

    #If one or no elements/oxides
    if request.args.get('resource') == 'chemicalanalysis':
        url = url_for('chemical_analyses') + '?' + urlencode(filter_dictionary)
        return redirect(url)

    elif request.args.get('resource') == 'sample':
        all_results = False
        if not chem_results:
            params['fields'] = 'subsample'
            chem_results = api.chemical_analysis.get(params=params).data['objects']
            all_results = True

        subsamples = (',').join(c['subsample'].replace("Subsample #","") for c in chem_results)

        params = {'subsample_id__in': subsamples, 'fields': 'sample', 'offset': 0, 'limit': 0}
        samples = api.subsample.get(params=params).data['objects']
        sample_results = (',').join(s['sample'].replace("Sample #", "") for s in samples)

        url = url_for('samples') + '?' + urlencode({'sample_id__in':sample_results})
        return redirect(url)

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


@app.route('/samples/')
def samples():
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = ast.literal_eval(json.dumps(request.args))
    offset = request.args.get('offset', 0)
    filters['offset'] = offset
    filters['fields'] = 'sample_id,number,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date,location'

    data = api.sample.get(params=filters)
    next, previous, last, total_count = paginate_model('samples', data, filters)

    samples = data.data['objects']
    for s in samples:
        s['mineral_list'] = (', ').join(s['minerals__name'])
        pos = s['location'].split(" ")
        s['location'] = [round(float(pos[2].replace(")","")),5),round(float(pos[1].replace("(","")),5)]
        if s['collection_date']:
            s['collection_date'] = s['collection_date'][:-9]

    return render_template('samples.html',
        samples=samples,
        showmap='showmap' in filters.keys(),
        next_url=next,
        prev_url=previous,
        total=total_count,
        first_page=url_for('samples')+'?'+urlencode(filters),
        last_page=last)


@app.route('/sample/<int:id>')
def sample(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    sample = api.sample.get(id).data
    if not sample:
        return HttpResponse("Sample does not exist")

    pos = sample['location'].split(" ")
    location = [round(float(pos[2].replace(")","")),5), round(float(pos[1].replace("(","")),5)]

    filter = {"sample__sample_id": sample['sample_id'], "limit": "0"}
    subsamples = api.subsample.get(params=filter).data['objects']
    alias_list = api.sample_alias.get(params=filter).data['objects']
    aliases = (', ').join([alias['alias'] for alias in alias_list])

    regions = (', ').join([region['name'] for region in sample['regions']])
    metamorphic_regions = (', ').join([metamorphic_region['name'] for metamorphic_region in sample['metamorphic_regions']])
    metamorphic_grades = (', ').join([metamorphic_grade['name'] for metamorphic_grade in sample['metamorphic_grades']])
    references = (', ').join([reference['name'] for reference in sample['references']])
    minerals = (', ').join([mineral['name'] for mineral in sample['minerals']])

    if sample['collection_date']:
        sample['collection_date'] = sample['collection_date'][:-9]

    return render_template('sample.html',
        sample=sample,
        location=location,
        minerals=minerals,
        regions=regions,
        references=references,
        metamorphic_grades=metamorphic_grades,
        metamorphic_regions=metamorphic_regions,
        aliases=aliases,
        subsamples=subsamples)


@app.route('/subsample/<int:id>')
def subsample(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    subsample = api.subsample.get(id).data
    if not subsample:
        return HttpResponse("Subsample does not exist")

    user = api.user.get(subsample['user']['user_id']).data
    filter = {"subsample__subsample_id": subsample['subsample_id'], "limit": "0"}
    chemical_analyses = api.chemical_analysis.get(params=filter).data['objects']

    return render_template('subsample.html',
        subsample=subsample,
        user=user,
        chemical_analyses=chemical_analyses,
        sample_id=subsample['sample'].split('/')[-2])


@app.route('/edit_sample/<int:id>')
def edit_sample(id):
    return render_template('index.html')


@app.route('/new_sample/')
def new_sample():
    return render_template('index.html')


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

    for c in chemical_analyses:
        sample_id = api.subsample.get(c['subsample'][18:-1]).data['sample'][15:-1]
        c['sample_number'] = api.sample.get(sample_id).data['number']
        if c['analysis_date']:
            c['analysis_date'] = c['analysis_date'][:-9]

    del filters['offset']
    return render_template('chemical_analyses.html',
        chemical_analyses=chemical_analyses,
        next_url=next,
        prev_url=previous,
        total=total_count,
        first_page=url_for('chemical_analyses') + '?' + urlencode(filters),
        last_page=last)


@app.route('/chemical_analysis/<int:id>')
def chemical_analysis(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api
    
    response = api.chemical_analysis.get(id).data
    if not response:
        return HttpResponse("Chemical analysis does not exist")

    response['subsample_id'] = response['subsample'][18:-1]
    subsample = api.subsample.get(response['subsample_id']).data
    response['subsample_number'] = subsample['name']
    response['sample_id'] = subsample['sample'][15:-1]
    response['sample_number'] = api.sample.get(response['sample_id']).data['number']

    elements = []
    oxides = []

    return render_template('chemical_analysis.html',
        data=response,
        element_list=elements,
        oxide_list=oxides)


@app.route('/edit_chemical/<int:id>')
def edit_chemical(id):
    return render_template('index.html')


@app.route('/new_chemical/')
def new_chemical():
    return render_template('index.html')


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


@app.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        payload = {'email': form.email.data}
        response = post(env('API_HOST') + '/reset_password/', data=payload)
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


@app.route('/reset_password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    form = PasswordResetForm()
    if form.validate_on_submit():
        payload = {'token': form.token.data, 'password': form.password.data}
        response = post(env('API_HOST') + '/reset_password/', data=payload)
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
        response = get(env('API_HOST') + '/reset_password/' + token)
        if response.status_code == 200:
            form = PasswordResetForm(token=token)
            return render_template('reset_password.html', form=form)

    flash('Password reset failed. Please try again.')
    return redirect(url_for('request_reset_password'))


@app.route('/user/<int:id>')
def user(id):
    api = MetpetAPI(None, None).api
    user = api.user.get(id).data
    if not user:
        return HttpResponse("User does not exist")
    return render_template('user.html', user=user)


if __name__ == '__main__':
    dotenv.read_dotenv('../app_variables.env')
    app.run(debug=True)
