import ast
import StringIO
import base64
from urllib import urlencode
from requests import get, post
import json
from itsdangerous import URLSafeTimedSerializer

from flask import Flask, request, render_template, url_for, redirect, flash, \
                  session
from flask_mail import Mail, Message
import dotenv
from getenv import env
import drest

from api import MetpetAPI
from forms import LoginForm, RequestPasswordResetForm, PasswordResetForm
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
          if key != "resource":
            filter_dictionary[key] = ",".join(filters[key])

    if request.args.get('resource') == 'sample':
        url = url_for('samples') + '?' + urlencode(filter_dictionary)
        return redirect(url)
    elif request.args.get('resource') == 'chemicalanalysis':
        if request.args.get('search_filters') == 'samples':
            request_obj = drest.api.API(baseurl=env('API_HOST'))
            if email and api_key:
                headers = {'email': email, 'api_key': api_key}
            else:
                headers = None
            response = request_obj.\
                           make_request('GET',
                           '/get-chem-analyses-given-sample-filters/',
                           params=filter_dictionary,
                           headers=headers)
            ids = response.data['chemical_analysis_ids']
            url = url_for('chemical_analyses') + '?' + \
                  urlencode({'chemical_analysis_id__in': ids})
            return redirect(url)
        else:
            #url = url_for('chemical_analyses') + '?' + urlencode(filter_dictionary)
            #return redirect(url)

            element_ids = (',').join(request.args.getlist('elements__element_id__in'))
            oxide_ids = (',').join(request.args.getlist('oxides__oxide_id__in'))
            mineral_ids = (',').join(request.args.getlist('minerals__in'))

            e_chem_analysis_ids = api.chemical_analysis.get(params={'elements__element_id__in': element_ids, 'minerals__in': mineral_ids, 'fields':'chemical_analysis_id'}).data['objects']
            o_chem_analysis_ids = api.chemical_analysis.get(params={'oxides__oxide_id__in': oxide_ids, 'minerals__in': mineral_ids, 'fields':'chemical_analysis_id'}).data['objects']

            cid_list = []
            for cid in e_chem_analysis_ids:
                cid_list.append(cid['chemical_analysis_id'])
            for cid in o_chem_analysis_ids:
                cid_list.append(cid['chemical_analysis_id'])
            print cid_list
            url = url_for('chemical_analyses') + '?' + \
                  urlencode({'chemical_analysis_id__in': (',').join(str(c) for c in cid_list)})
            #url = url_for('chemical_analyses') + '?' + \
            #      urlencode({'elements__element_id__in': element_ids, 'minerals__in': mineral_ids})
            return redirect(url)
            
    
    owner_list = []
    region_list = []
    rock_type_list = []
    collector_list = []
    country_list = []
    reference_list = []
    number_list = []
    igsn_list = []
    metamorphic_region_list = []
    metamorphic_grade_list = []
    element_list = []
    oxide_list = []

    oxides = api.oxide.get(params={'limit': 0}).data['objects']
    elements = api.element.get(params={'limit': 0}).data['objects']
    rock_types = api.rock_type.get(params={'order_by': 'rock_type', 'limit': 0}).data['objects']
    regions = api.region.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    references = api.reference.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    metamorphic_regions = api.metamorphic_region.get(params={'order_by': 'name', 'limit': 0}).data['objects']
    metamorphic_grades = api.metamorphic_grade.get(params={'limit': 0}).data['objects']
    samples = api.sample.get(params={'fields': 'collector,number,sesar_number,country', 'limit': 0}).data['objects']
    users = api.user.get(params={'limit': 0}).data['objects']
    mineral_relationships = api.mineral_relationship.get(params={'limit': 0}).data['objects']

    mineralroots = []
    parents = set()
    children = set()
    for m in mineral_relationships:
        parents.add((m['parent_mineral']['name'], m['parent_mineral']['mineral_id']))
        children.add((m['child_mineral']['name'], m['child_mineral']['mineral_id']))
    mineralroots = set(parents) - set(children)


    mineralnodes = []
    for (name, mid) in mineralroots:
	mineralnodes.append({"id": name, "parent": "#", "text": name, "mineral_id": mid})
    for m in mineral_relationships:
        node = {"id": m['child_mineral']['name'], "parent": m['parent_mineral']['name'], "text": m['child_mineral']['name'], "mineral_id": m['child_mineral']['mineral_id']}
        mineralnodes.append(node)

    for element in elements:
        element_list.append(element)
    for oxide in oxides:
        oxide_list.append(oxide)
    for region in regions:
        region_list.append(region['name'])
    for rock_type in rock_type_list:
        rock_type_list.append(rock_type['name'])
    for ref in references:
        reference_list.append(ref['name'])
    for mmr in metamorphic_regions:
        metamorphic_region_list.append(mmr['name'])
    for mmg in metamorphic_grades:
        metamorphic_grade_list.append(mmg['name'])
    for sample in samples:
        collector_list.append(unicode(sample['collector']))
        number_list.append(sample['number'])
        igsn_list.append(sample['sesar_number'])
        country_list.append(sample['country'])
    for user in users:
        owner_list.append(user)
    collector_list = list (set ( collector_list ))
    country_list = list(set (country_list))
    return render_template('search_form.html',
                            query='',
			    elements=element_list,
			    oxides=oxide_list,
                            regions=region_list,
			    mineralrelationships=json.dumps(mineral_relationships),
			    mineral_nodes=json.dumps(mineralnodes),
                            rock_types=rock_types,
                            provenances=collector_list,
                            references=reference_list,
			    numbers=number_list,
                            igsns=igsn_list,
			    countries=country_list,
			    owners = owner_list,
                            metamorphic_regions=metamorphic_region_list,
                            metamorphic_grades=metamorphic_grade_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('api_key'):
        return redirect(url_for('search'))

    form = LoginForm()

    if form.validate_on_submit():
        payload = {'email': form.email.data,
                   'password': form.password.data}
        response =  post(env('API_HOST') + '/authenticate/', data=payload)
        if response.status_code == 200:
            data = json.loads(response.text)
            session['email'] = data['email']
            session['api_key'] = data['api_key']
            flash('Login successful!')
            return redirect(url_for('search'))
        else:
            flash('Authentication failed. Please try again.')


    return render_template('login.html',
                            form=form)


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
            message = Message("Metpetdb: Reset Password",
                               sender=env('DEFAULT_MAIL_SENDER'),
                               recipients=[form.email.data])
            reset_url = url_for('reset_password', token=data['reset_token'],
                                 _external=True)
            message.body = render_template('reset_password_email.html',
                                           reset_url=reset_url)
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
        payload = {'token': form.token.data,
                   'password': form.password.data}
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
    data = api.sample.get(params=filters)

    next, previous, last, total_count = paginate_model('samples', data, filters)

    samples = data.data['objects']
    for sample in samples:
        mineral_names = [str(m) for m in sample['minerals__name']]
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
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = ast.literal_eval(json.dumps(request.args))
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
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    payload = {'email': email, 'api_key': api_key}

    url = env('API_HOST') + '/chemical_analysis/{0}'.format(id)
    response = get(url, params=payload)

    return render_template('chemical_analysis.html',
                            data=response.json())


@app.route('/user/<int:id>')
def user(id):
    api = MetpetAPI(None, None).api
    user = api.user.get(id).data
    if sample:
        return render_template('user.html', user=user)
    else:
        return HttpResponse("User does not Exist")


if __name__ == '__main__':
    dotenv.read_dotenv('../app_variables.env')
    app.run(debug=True)
