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
          if key != "resource" and key != "all_results" and key != "prev" and key != "total":
            filter_dictionary[key] = (',').join(filters[key])

    #If minerals and AND are selected, intersect samples for each mineral with other filters
    all_results = 'all_results' in filters.keys()
    if all_results or (request.args.getlist('minerals__in') and len(request.args.getlist('minerals__in')) > 1 and request.args.get('mineralandor') == 'and'):
        showmap = 'showmap' in filter_dictionary.keys()
        prev = 'prev' in filters.keys()
        total = int(request.args.get('total',0))
        offset = request.args.get('offset','0')
        url = request.url.replace("&all_results=True","").replace("&prev=True","").replace("&offset="+offset,"").replace("&total="+str(total),"")
        minerals = [m for m in request.args.getlist('minerals__in') if m != '']
        fields = 'sample_id,minerals__mineral_id'
        if request.args.get('resource') == 'sample':
            fields += ',user__name,collector,number,public_data,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date'
        if showmap:
            fields += ',location'

        params = {'fields': fields, 'limit': 100}
        for key in filter_dictionary:
            if key != "minerals__in" and key != "search_filters" and key != "fields" and key != "mineralandor":
                params[key] = filter_dictionary[key]
        params['offset'] = int(offset)
        max_res = 20
        if all_results:
            params['offset'] = 0
            max_res = 20000
            del params['limit']
        elif prev:
            params['offset'] -= 100
        if minerals:
            params['minerals__in'] = minerals[0]

        sample_results = []
        while len(sample_results) < max_res:
            samples = api.sample.get(params=params).data['objects']
            while prev and not samples:
                params['offset'] -= 100
                samples = api.sample.get(params=params).data['objects']
            if not samples:
                break
            if prev:
                samples.reverse()
            i = 0
            while i < len(samples):
                good = True
                for m in minerals:
                    if 'minerals__mineral_id' not in samples[i].keys() or int(m) not in samples[i]['minerals__mineral_id']:
                        good = False
                if good:
                    sample_results.append(samples[i])
                    if len(sample_results) == max_res:
                        offset = str(params['offset'])
                        break
                i += 1
            if not prev:
                params['offset'] += i
                if not all_results:
                    params['offset'] += 1
            else:
                params['offset'] = max(params['offset']-i,0)

        total += len(sample_results)
        if prev:
            sample_results.reverse()
            params['offset'] = request.args.get("offset",'0')
            total = None
        prev_url = next_url = None
        if offset != '0':
            prev_url = url+"&prev=True&offset="+offset
        if offset != '10000':
            next_url = url+"&offset="+str(params['offset'])+"&total="+str(total)

        if request.args.get('resource') == 'sample':
            #Build mineral list string for rendering results
            for s in sample_results:
                s['mineral_list'] = (', ').join(s['minerals__name'])
                if showmap:
                    pos = s['location'].split(" ")
                    s['lat'] = float(pos[2].replace(")",""))
                    s['lon'] = float(pos[1].replace("(",""))
                    del s['location']
            return render_template('samples.html',
                samples=sample_results,
                showmap=showmap,
                runningtotal=total,
                first_page=url,
                prev_url=prev_url,
                next_url=next_url,
                last_page=url+"&prev=True&offset=10000")

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
                runningtotal=total,
                first_page=url,
                prev_url=prev_url,
                next_url=next_url,
                last_page=url+"&prev=True&offset=10000")

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
            filter_dictionary[key] = (",").join(filters[key])

    if 'resource' in request.args:
        showmap = 'showmap' in filter_dictionary.keys()
        minerals = [m for m in request.args.getlist('minerals__in') if m != '']
        elements = [e for e in request.args.getlist('elements__element_id__in') if e != '']
        oxides = [o for o in request.args.getlist('oxides__oxide_id__in') if o != '']
        fields = 'elements__element_id,oxides__oxide_id'
        if request.args.get('resource') == 'chemicalanalysis':
            fields += ',chemical_analysis_id,spot_id,public_data,analysis_method,mineral__name,where_done,analyst,analysis_date,reference_x,reference_y,total'
        elif request.args.get('resource') == 'sample':
            fields += ',subsample'
        params = {'fields': fields, 'limit': 0}
        if elements:
            params['elements__element_id__in'] = elements[0]
        if oxides:
            params['oxides__oxide_id__in'] = oxides[0]
        if not minerals:
            minerals.append((",").join([str(i) for i in range(184)]))

        chem_results = []
        for i in range(len(minerals)):
            params['minerals__in'] = minerals[i]
            chem = api.chemical_analysis.get(params=params).data['objects']
            for i in range(len(chem)):
                good = True
                for e in elements:
                    if 'elements__element_id' not in chem[i].keys() or int(e) not in chem[i]['elements__element_id']:
                        good = False
                for o in oxides:
                    if 'oxides__oxide_id' not in chem[i].keys() or int(o) not in chem[i]['oxides__oxide_id']:
                        good = False
                if good:
                    chem_results.append(chem[i])

        if request.args.get('resource') == 'chemicalanalysis':
            return render_template('chemical_analyses.html',
                chemical_analyses=chem_results,
                total=len(chem_results))

        elif request.args.get('resource') == 'sample':
            subsamples = set()
            for c in chem_results:
                subsamples.add(c['subsample'].replace("Subsample #", ""))
            subsamples = (',').join(str(s) for s in subsamples)

            params = {'subsample_id__in': subsamples, 'fields': 'sample', 'limit': 0}
            ids = api.subsample.get(params=params).data['objects']
            samples = set()
            for i in ids:
                samples.add(i['sample'].replace("Sample #", ""))
            samples = (',').join(str(s) for s in samples)

            del params['subsample_id__in']
            params['sample_id__in'] = samples
            params['fields'] = 'sample_id,user__name,collector,number,public_data,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date'
            if showmap:
                params['fields'] += ',location'
            sample_results = api.sample.get(params=params).data['objects']

            if showmap:
                for s in sample_results:
                    pos = s['location'].split(" ")
                    s['lat'] = float(pos[2].replace(")",""))
                    s['lon'] = float(pos[1].replace("(",""))
                    del s['location']

            return render_template('samples.html',
                samples=sample_results,
                showmap=showmap,
                total=len(sample_results))

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

    showmap = 'showmap' in filters.keys()
    if showmap:
        filters['fields'] += ',location'

    data = api.sample.get(params=filters)
    next, previous, last, total_count = paginate_model('samples', data, filters)

    locations = []
    samples = data.data['objects']
    for s in samples:
        s['mineral_list'] = (', ').join(s['minerals__name'])
        if showmap:
            pos = s['location'].split(" ")
            s['lat'] = float(pos[2].replace(")",""))
            s['lon'] = float(pos[1].replace("(",""))
            del s['location']

    first_page_url = url_for('samples') + '?' + urlencode(filters)

    return render_template('samples.html',
        samples=samples,
        showmap=showmap,
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


@app.route('/edit_sample/<int:id>', methods = ['GET','POST'])
def edit_sample(id):
    form = EditForm(minerals=True)
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email,api_key).api
    api.auth(user=email,api_key=api_key)

    sample = api.sample.get(id).data
    sample2 = api.sample.get(id)
    rock_type_list = []
    rock_type = api.rock_type.get(params={'order_by': 'rock_type', 'limit': 0}).data['objects']
    for rock in rock_type:
        rock_type_list.append(rock['rock_type'])
    form.rock_type.choices = [(rock,rock) for rock in rock_type_list]

    metamorphic_grade_list = []
    metamorphic_grades = api.metamorphic_grade.get(
      params={'limit': 0}).data['objects']

    for mmg in metamorphic_grades:
        metamorphic_grade_list.append(mmg['name'])
    form.metamorphic_grades.choices = [(m,m) for m in metamorphic_grade_list]

    regions = [region['name'] for region in sample['regions']]
    location = sample['location'].split(" ")
    longtitude = location[1].replace("(","")
    latitude = location[2].replace(")","")
    loc = [longtitude, latitude]
    test = "POINT (" + str(longtitude) + " " + str(latitude) + ")"
    print test, sample['location']
    if (test == sample['location']):
        print "same"

    mineral_relationships = (api.mineral_relationship.get(
                              params={'limit': 0,
                                      'fields':'parent_mineral__mineral_id,'
                                               'parent_mineral__name,'
                                               'child_mineral__mineral_id,'
                                               'child_mineral__name'})
                                                .data['objects'])
    parents = set()
    children = set()
    for m in mineral_relationships:
        parents.add((m['parent_mineral__name'], m['parent_mineral__mineral_id']))
        children.add((m['child_mineral__name'], m['child_mineral__mineral_id']))
    mineralroots = set(parents) - set(children)

    mineralnodes = []
    for (name, mid) in mineralroots:
        mineralnodes.append({"id": name,
                           "parent": "#",
                           "text": name,
                           "mineral_id": mid})

    for m in mineral_relationships:
        node = {"id": m['child_mineral__name'],
              "parent": m['parent_mineral__name'],
              "text": m['child_mineral__name'],
              "mineral_id": m['child_mineral__mineral_id']}
        mineralnodes.append(node)

    form.region.min_entries = len(regions)+1

    metamorphic_regions = [metamorphic_region['name'] for metamorphic_region in sample['metamorphic_regions']]

    minerals = [mineral['name'] for mineral in sample['minerals']]
    new_regions = []

    form.minerals.choices = [(mineral, mineral) for mineral in minerals]

    print sample2.data['rock_type']
    print sample2.data['rock_type']['rock_type']

    if form.validate_on_submit():
        sample2.data['user']['name'] = form.owner.data
        sample2.data['public_data'] = form.public.data
        sample2.data['location_text'] = form.location_text.data
        sample2.data['collector'] = form.collector.data

        rocktype = form.rock_type.data
        value = ''
        for rock in rock_type:
            if (rock['rock_type'] == rocktype):
                value = rock
        sample2.data['rock_type'] = value

        sample2.data['country'] = form.country.data
        print sample2.data['collection_date']
        if (form.date_collected.data != ""):
            sample2.data['collection_date'] = form.date_collected.data
        else:
            sample2.data['collection_date'] = None
        print sample2.data['rock_type']['rock_type']

        metgrade = form.metamorphic_grades.data
        value = []
        metamorphic_grades2 = api.metamorphic_grade.get(params={'limit': 0}).data['objects']
        for met in metamorphic_grades2:
            if (metgrade == met['name']):
                value = []
                value.append(met)
        print sample2.data['metamorphic_grades']
        for x in sample2.data['metamorphic_grades']:
            del x
        print value
        #sample2.data['metamorphic_grades']
        sample2.data['metamorphic_grades'] = value

        print sample2.data['metamorphic_grades']
        loc[0] = form.longitude.data
        loc[1] = form.latitude.data
        new_loc = "POINT (" + str(longtitude) + " " + str(latitude) + ")"
        sample2.data['location'] = new_loc
        '''sample2.data['user']['name'] = form.owner.data
        sample2.data['public_data'] = form.public.data
        sample2.data['location_text'] = form.location_text.data
        sample2.data['collector'] = form.collector.data
        sample2.data['rock_type']['rock_type'] = form.rock_type.data
        sample2.data['metamorphic_grades'][0]['name'] = form.metamorphic_grades.data
        sample2.data['country'] = form.country.data
        sample2.data['collection_date'] = form.date_collected.data
        minerals = form.minerals.data
        print minerals
        for x in range(0,len(form.region)):
            new_regions.append(form.region.pop_entry())
        loc[0] = form.longitude.data
        loc[1] = form.latitude.data
        regions = []
        for r in new_regions:
            regions.append(r)
            #fix regions
        #print sample2.data['user']['name']
        #print len(regions)
        list_name = request.args.get("list_name")
        #listx = get_list(list_name)
        print list_name'''
        #sample2 = api.sample.put(id, sample2.data)
        sample2 = api.sample.put(id, sample2.data)
        print sample2
        redurl = '/sample/4999'
        return redirect(url_for('sample', id=id))
    else:
        form.owner.data = sample['user']['name']
        form.public.data = sample['public_data']
        form.location_text.data = sample['location_text']
        form.collector.data = sample['collector']
        form.rock_type.data = sample['rock_type']['rock_type']
        if (sample['metamorphic_grades']):
            form.metamorphic_grades.data = sample['metamorphic_grades'][0]['name']
        form.country.data = sample['country']
        form.date_collected.data = sample['collection_date']
        form.longitude.data = loc[0]
        form.minerals.data = minerals
        for r in regions:
            form.region.append_entry(r)
        form.latitude.data = loc[1]

    #change location in sample
    return render_template('edit_sample.html',
        form = form,
        region_list = regions,
        location = loc,
        rock_types = rock_type_list,
        sample = sample,
        mineral_roots = mineralroots,
        mineral_nodes = mineralnodes,
        region_size = len(regions),
        metamorphic_regions=(', ').join(metamorphic_regions),
        minerals = minerals,
        test=json.dumps(minerals),
        api_key = api_key)


@app.route('/new_sample/', methods = ['GET', 'POST'])
def new_sample():
    form = NewSample();
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api
    rock_type_list = []
    rock_type = api.rock_type.get(params={'order_by': 'rock_type', 'limit': 0}).data['objects']
    for rock in rock_type:
        rock_type_list.append(rock['rock_type'])
    form.rock_type.choices = [(rock,rock) for rock in rock_type_list]

    metamorphic_grade_list = []
    metamorphic_grades = api.metamorphic_grade.get(params={'limit': 0}).data['objects']
    for mmg in metamorphic_grades:
        metamorphic_grade_list.append(mmg['name'])
    form.metamorphic_grades.choices = [(m,m) for m in metamorphic_grade_list]

    mineral_relationships = api.mineral_relationship.get(\
                              params={'limit': 0,
                                      'fields':'parent_mineral__mineral_id,parent_mineral__name,child_mineral__mineral_id,child_mineral__name'}).\
                                                  data['objects']

    mineralroots = []
    parents = set()
    children = set()
    for m in mineral_relationships:
        parents.add((m['parent_mineral__name'], m['parent_mineral__mineral_id']))
        children.add((m['child_mineral__name'], m['child_mineral__mineral_id']))
    mineralroots = set(parents) - set(children)

    mineralnodes = []
    for (name, mid) in mineralroots:
        mineralnodes.append({"id": name, "parent": "#", "text": name, "mineral_id": mid})
    for m in mineral_relationships:
        node = {"id": m['child_mineral__name'], "parent": m['parent_mineral__name'], "text": m['child_mineral__name'], "mineral_id": m['child_mineral__mineral_id']}
        mineralnodes.append(node)

    if form.validate():
        print "validated"
    print form.errors

    '''
    {u'rock_type_id': 10, u'rock_type': u'Amphibolite', u'resource_uri': u'/api/v1/rock_type/10/'}
    '''
    if form.validate_on_submit():
        sample_data = {}
        sample_data[u'user'] = form.owner.data
        sample_data[u'public_data'] = form.public.data
        longitude = form.longitude.data
        latitude = form.latitude.data
        new_loc = u"POINT (" + str(longitude) + " " + str(latitude) + ")"
        sample_data[u'location'] = new_loc
        sample_data[u'location_text'] = form.location_text.data
        rock_type = {}
        rock_type[u'rock_type_id'] = 10
        rock_type[u'rock_type'] = u'Amphibolite'
        rock_type[u'resource_uri'] = u'/api/v1/rock_type/10/'
        sample_data[u'rock_type'] = rock_type
        sample_data[u'collection_date'] = form.date_collected.data
        print sample_data
        #print sample_data['user']
        sample_data = api.sample.post(sample_data)
        return redirect(url_for('search'))

    #change location in sample
    return render_template('new_sample.html',
        form = form,
        mineral_nodes =mineralnodes,
        api_key = api_key)


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


@app.route('/edit_chemical/<int:id>', methods = ['GET','POST'])
def edit_chemical(id):
    form = EditChemForm()
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email,api_key).api
    payload = {'email': email, 'api_key': api_key}

    url = env('API_HOST') + 'api/v1/chemical_analysis/{0}'.format(id)
    url+='?format=json'
    response = get(url, params=payload)
    data = response.json()

    filters = ast.literal_eval(json.dumps(request.args))
    offset = request.args.get('offset', 0)
    filters['offset'] = offset

    data2 = api.chemical_analysis.get(params=filters)
    next, previous, last, total_count = paginate_model('chemical_analyses',
                                                     data2, filters)
    chemical_analyses = data2.data['objects']

    sample2 = api.chemical_analysis.get(id)
    print sample2.data

    oxide_list=[]
    element_list=[]
    oxides = api.oxide.get(params={'limit': 0}).data['objects']

    for oxide in oxides:
        oxide_list.append(oxide)

    elements = api.element.get(params={'limit': 0}).data['objects']
    for element in elements:
        element_list.append(element)

    selected_oxide_list = []
    for o in data['oxides']:
        oxideurl = env('API_HOST') + o + '?format=json'
        oxideresponse = get(oxideurl, params=payload)
        oxidedata = oxideresponse.json()
        selected_oxide_list.append(oxidedata)

    suburl = env('API_HOST') + data['subsample'] + '?format=json'
    response2 = get(suburl, params=payload)
    subdata = response2.json()

    sampleurl = env('API_HOST') + subdata['sample'] + '?format=json'
    sampleresponse = get(sampleurl, params=payload)
    sampledata = sampleresponse.json()

    userurl = env('API_HOST') + data['user'] + '?format=json'
    response3 = get(userurl, params=payload)
    userdata = response3.json()

    if form.validate_on_submit():
        #userdata['name'] = form.owner.data
        sample2.data['public_data'] = form.public.data
        sample2.data['analyst'] = form.analyst.data
        sample2.data['total'] = form.total.data
        sample2.data['stage_x'] = form.StageX.data
        sample2.data['stage_y'] = form.StageY.data
        sample2 = api.chemical_analysis.put(id, sample2.data)
        return redirect(url_for('chemical_analysis', id=id))
    else:
        form.owner.data = userdata['name']
        form.public.data = data['public_data']
        form.analyst.data = data['analyst']
        #form.analysis_material.data = data['analysis_material']
        form.total.data = data['total']
        form.StageX.data = data['stage_x']
        form.StageY.data = data['stage_y']

    return render_template('edit_chemical.html',
        form = form,
        data = data,
        subdata = subdata,
        sampledata = sampledata,
        userdata = userdata,
        selected_oxide_list = selected_oxide_list,
        oxide_list = oxide_list,
        element_list = element_list,
        id = id,
        api_key = api_key)


@app.route('/new_chemical/', methods = ['GET', 'POST'])
def new_chemical():
    form = NewChem()
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api
    filters = ast.literal_eval(json.dumps(request.args))
    offset = request.args.get('offset',0)
    filters['offset'] = offset

    data = api.chemical_analysis.get(params=filters)
    oxide_list = []
    element_list = []
    oxides = api.oxide.get(params={'limit':0}).data['objects']

    for oxide in oxides:
        oxide_list.append(oxide)
    elements = api.element.get(params={'limit':0}).data['objects']
    for element in elements:
        element_list.append(element)

    print data.data

    return render_template('new_chemical.html',
        form = form,
        oxide_list = oxide_list,
        element_list = element_list,
        api_key = api_key)


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
