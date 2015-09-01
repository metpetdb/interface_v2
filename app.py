import dotenv
import json
import drest
from ast import literal_eval
from getenv import env
from requests import get, post
from urllib import urlencode, urlopen
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
    PasswordResetForm
)
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
    api = drest.API(baseurl=env('API_DRF_HOST'))

    filters = {}
    for key in dict(request.args):
        if dict(request.args)[key][0] and key != 'resource':
            filters[key] = (',').join(dict(request.args)[key])

    if request.args.get('resource') == 'sample':
        return redirect(url_for('samples')+'?'+urlencode(filters))

    if request.args.get('resource') == 'chemicalanalysis':
        if 'minerals_and' in filters:
            del filters['minerals_and']
        filters['sample_filters'] = True
        return redirect(url_for('chemical-analyses')+'?'+urlencode(filters))

    regions = api.make_request('GET','/regions/', params={'fields': 'name', 'page_size': 2000, 'format': 'json'}).data['results']
    minerals = api.make_request('GET','/minerals/', params={'fields': 'name', 'page_size': 200, 'format': 'json'}).data['results']
    rock_types = api.make_request('GET','/rock_types/', params={'fields': 'name', 'page_size': 40, 'format': 'json'}).data['results']
    collectors = api.make_request('GET','/collectors/', params={'fields': 'name', 'page_size': 140, 'format': 'json'}).data['results']
    references = api.make_request('GET','/references/', params={'fields': 'name', 'page_size': 1100, 'format': 'json'}).data['results']
    metamorphic_grades = api.make_request('GET','/metamorphic_grades/', params={'fields': 'name', 'page_size': 30, 'format': 'json'}).data['results']
    metamorphic_regions = api.make_request('GET','/metamorphic_regions/', params={'fields': 'name', 'page_size': 240, 'format': 'json'}).data['results']

    samples = api.make_request('GET','/samples/',
        params={'fields': 'country', 'public_data': True, 'page_size': 1000, 'format': 'json'}).data['results']
    countries = set()
    for sample in samples:
        countries.add(sample['country'])

    api_samples = api.make_request('GET','/samples/', params={'fields': 'number', 'page_size': 2000, 'format': 'json'}).data
    numbers = api_samples['results']
    while api_samples['next']:
        api_samples = json.loads(urlopen(api_samples['next']).read())
        numbers += api_samples['results']

    return render_template('search_form.html',
        countries=countries,
        metamorphic_grades=metamorphic_grades,
        metamorphic_regions=metamorphic_regions,
        minerals=minerals,
        numbers=numbers,
        collectors=collectors,
        references=references,
        regions=regions,
        rock_types=rock_types
    )


@metpet_ui.route('/search-chemistry/')
def search_chemistry():
    api = drest.API(baseurl=env('API_DRF_HOST'))

    filters = {}
    for key in dict(request.args):
        if dict(request.args)[key][0] and key != 'resource':
            filters[key] = (',').join(dict(request.args)[key])

    if request.args.get('resource') == 'chemicalanalysis':
        return redirect(url_for('chemical-analyses')+'?'+urlencode(filters))

    if request.args.get('resource') == 'sample':
        filters['chemical_analyses_filters'] = True
        return redirect(url_for('samples')+'?'+urlencode(filters))

    oxides = api.make_request('GET','/oxides/', params={'fields': 'species', 'page_size': 100, 'format': 'json'}).data['results']
    elements = api.make_request('GET','/elements/', params={'fields': 'name,symbol', 'page_size': 120, 'format': 'json'}).data['results']
    minerals = api.make_request('GET','/minerals/', params={'fields': 'name', 'page_size': 200, 'format': 'json'}).data['results']

    return render_template('chemical_search_form.html',
        elements=elements,
        oxides=oxides,
        minerals=minerals)


@metpet_ui.route('/samples/')
def samples():
    api = drest.API(baseurl=env('API_DRF_HOST'))

    next = previous = last = total_count = None
    filters = literal_eval(json.dumps(request.args))
    filters['format'] = 'json'

    samples = api.make_request('GET','/samples/', params=filters).data
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
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    api = drest.API(baseurl=env('API_DRF_HOST'))

    sample = api.make_request('GET','/samples/'+id, params={'format': 'json'}, headers=headers).data
    if "detail" in sample:
        return render_template("warning.html", text=sample['detail'])

    pos = sample['location_coords'].split(" ")
    sample['location_coords'] = [round(float(pos[2].replace(")","")),5), round(float(pos[1].replace("(","")),5)]
    sample['metamorphic_regions'] = (', ').join([mmr['name'] for mmr in sample['metamorphic_regions']])
    sample['metamorphic_grades'] = (', ').join([mmg['name'] for mmg in sample['metamorphic_grades']])
    sample['references'] = (', ').join(sample['references'])
    sample['minerals'] = (', ').join([m['name'] for m in sample['minerals']])
    sample['aliases'] = (', ').join([a['name'] for a in sample['aliases']])
    sample['regions'] = (', ').join(sample['regions'])
    if sample['collection_date']:
        sample['collection_date'] = sample['collection_date'][:-10]

    subsamples = []
    for s in sample['subsample_ids']:
        subsamples.append(api.make_request('GET','/subsamples/'+s,
            params={'fields': 'subsample_type,name,id,public_data,owner', 'format': 'json'}, headers=headers).data)
    for s in subsamples:
        s['chemical_analyses'] = api.make_request('GET','/chemical_analyses/',
            params={'subsample_ids': s['id'], 'fields': 'id', 'format': 'json'}, headers=headers).data['results']

    return render_template('sample.html',
        sample=sample,
        subsamples=subsamples
    )


@metpet_ui.route('/edit-sample/<string:id>', methods=['GET','POST'])
def edit_sample(id):
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    else:
        return redirect(url_for('sample', id=id))
    api = drest.API(baseurl=env('API_DRF_HOST'))

    if len(dict(request.form)):
        new_sample = literal_eval(json.dumps(request.form))
        new_sample['minerals'] = []
        for key in new_sample.keys():
            if key[:9] == "minerals_":
                new_sample["minerals"].append({'id': key[9:], 'amount': new_sample[key]})
                del new_sample[key]
        new_sample['id'] = id

        new_sample['aliases'] = new_sample['aliases'].split(',')
        new_sample['location_coords'] = "SRID=4326;POINT ("+str(new_sample['location_coords1'])+" "+str(new_sample['location_coords0'])+")"
        del new_sample['location_coords0']
        del new_sample['location_coords1']

        api.make_request('POST','/samples/'+id, params=new_sample, headers=headers).data
        return redirect(url_for('sample', id=id))

    sample = api.make_request('GET','/samples/'+id, params={'format': 'json'}).data
    pos = sample['location_coords'].split(" ")
    sample['location_coords'] = [round(float(pos[2].replace(")","")),5), round(float(pos[1].replace("(","")),5)]

    regions = api.make_request('GET','/regions/', params={'page_size': 2000, 'format': 'json'}).data['results']
    minerals = api.make_request('GET','/minerals/', params={'page_size': 200, 'format': 'json'}).data['results']
    rock_types = api.make_request('GET','/rock_types/', params={'page_size': 40, 'format': 'json'}).data['results']
    references = api.make_request('GET','/references/', params={'page_size': 1100, 'format': 'json'}).data['results']
    metamorphic_grades = api.make_request('GET','/metamorphic_grades/', params={'page_size': 30, 'format': 'json'}).data['results']
    metamorphic_regions = api.make_request('GET','/metamorphic_regions/', params={'page_size': 240, 'format': 'json'}).data['results']

    return render_template('edit_sample.html',
        sample=sample,
        regions=regions,
        minerals=minerals,
        rock_types=rock_types,
        references=references,
        metamorphic_grades=metamorphic_grades,
        metamorphic_regions=metamorphic_regions
    )


@metpet_ui.route('/new-sample/', methods=['GET', 'POST'])
def new_sample():
    session['email'] = 'sibel@cs.rpi.edu'
    session['auth_token'] = 'e8a233e6cb9c32c0f8e0bf6979838e801303fc51'
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    else:
        return redirect(url_for('search'))
    api = drest.API(baseurl=env('API_DRF_HOST'))

    if len(dict(request.form)):
        new_sample = literal_eval(json.dumps(request.form))
        for key in new_sample.keys():
            if key[:9] == "minerals_":
                new_sample["minerals"].append({'id': key[9:], 'amount': new_sample[key]})
                del new_sample[key]

        new_sample['aliases'] = new_sample['aliases'].split(',')
        new_sample['location_coords'] = "SRID=4326;POINT ("+str(new_sample['location_coords1'])+" "+str(new_sample['location_coords0'])+")"
        del new_sample['location_coords0']
        del new_sample['location_coords1']

        new_sample = api.make_request('POST','/samples/', params=new_sample, headers=headers).data
        return redirect(url_for('sample',id=new_sample['id']))

    regions = api.make_request('GET','/regions/', params={'page_size': 2000, 'format': 'json'}).data['results']
    minerals = api.make_request('GET','/minerals/', params={'page_size': 200, 'format': 'json'}).data['results']
    rock_types = api.make_request('GET','/rock_types/', params={'page_size': 40, 'format': 'json'}).data['results']
    metamorphic_grades = api.make_request('GET','/metamorphic_grades/', params={'page_size': 30, 'format': 'json'}).data['results']
    metamorphic_regions = api.make_request('GET','/metamorphic_regions/', params={'page_size': 240, 'format': 'json'}).data['results']

    owner = api.make_request('GET','/users/', params={'email': session.get('email')}).data['results']
    if len(owner) > 1:
        owner = None
    else:
        owner = owner[0]

    return render_template('edit_sample.html',
        sample={'owner': owner},
        regions=regions,
        minerals=minerals,
        rock_types=rock_types,
        metamorphic_grades=metamorphic_grades,
        metamorphic_regions=metamorphic_regions
    )


@metpet_ui.route('/subsample/<string:id>')
def subsample(id):
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    api = drest.API(baseurl=env('API_DRF_HOST'))

    subsample = api.make_request('GET','/subsamples/'+id, params={'format': 'json'}, headers=headers).data
    print subsample
    if "detail" in subsample:
        return render_template("warning.html", text="Subsample "+id+" does not exist")

    subsample['sample']['number'] = api.make_request('GET','/samples/'+subsample['sample']['id'], params={'fields': 'number', 'format': 'json'}).data['number']
    chemical_analyses = api.make_request('GET','/chemical_analyses/', params={'subsample_ids': subsample['id'], 'format': 'json'}).data['results']

    return render_template('subsample.html',
        subsample=subsample,
        chemical_analyses=chemical_analyses
    )


@metpet_ui.route('/edit-subsample/<string:id>', methods=['GET', 'POST'])
def edit_subsample(id):
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    else:
        return redirect(url_for('subsample', id=id))
    api = drest.API(baseurl=env('API_DRF_HOST'))

    if len(dict(request.form)):
        new_subsample = literal_eval(json.dumps(request.form))
        new_subsample['id'] = id

        new_subsample = api.make_request('POST','/subsamples/'+id, params=new_subsample, headers=headers).data
        return redirect(url_for('subsample', id=id))

    subsample = api.make_request('GET','/subsamples/'+id, params={'format': 'json'}).data
    subsample['owner'] = api.make_request('GET','/users/'+subsample['owner'], params={'format': 'json'}).data

    return render_template('edit_subsample.html',
        subsample=subsample
    )


@metpet_ui.route('/new-subsample/', methods=['GET', 'POST'])
def new_subsample():
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    else:
        return redirect(url_for('search'))
    api = drest.API(baseurl=env('API_DRF_HOST'))

    if len(dict(request.form)):
        new_subsample = literal_eval(json.dumps(request.form))
        new_subsample = api.make_request('POST','/subsamples/', params=new_subsample, headers=headers).data
        return redirect(url_for('subsample', id=new_subsample['id']))

    owner = api.make_request('GET','/users/', params={'email': email}).data['results']
    if len(owner) > 1:
        owner = None
    else:
        owner = owner[0]

    return render_template('edit_subsample.html',
        subsample={'owner': owner, 'sample': ''}
    )


@metpet_ui.route('/chemical-analyses/')
def chemical_analyses():
    api = drest.API(baseurl=env('API_DRF_HOST'))

    next = previous = last = total_count = None
    filters = literal_eval(json.dumps(request.args))
    filters['format'] = 'json'

    chemicals = api.make_request('GET','/chemical_analyses/', params=filters).data
    chem_results = chemicals['results']
    next, previous, last, total_count = paginate_model('chemical-analyses', chemicals, filters)

    for c in chem_results:
        c['sample'] = api.make_request('GET','/samples/'+c['subsample']['sample'], params={'fields': 'number', 'format': 'json'}).data
        if c['analysis_date']:
            c['analysis_date'] = c['analysis_date'][:-10]

    return render_template('chemical_analyses.html',
        chemical_analyses=chem_results,
        next_url=next,
        prev_url=previous,
        total=total_count,
        first_page=url_for('chemical-analyses')+'?'+urlencode(filters),
        last_page=last
    )


@metpet_ui.route('/chemical-analysis/<string:id>')
def chemical_analysis(id):
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    api = drest.API(baseurl=env('API_DRF_HOST'))

    analysis = api.make_request('GET','/chemical_analyses/'+id, params={'format': 'json'}, headers=headers).data
    if "detail" in analysis:
        return render_template("warning.html", text="Chemical analysis "+id+" does not exist")
    analysis['sample'] = api.make_request('GET','/samples/'+analysis['subsample']['sample'], params={'fields': 'number', 'format': 'json'}).data

    return render_template('chemical_analysis.html',
        analysis=analysis
    )


@metpet_ui.route('/edit-chemical-analysis/<string:id>', methods=['GET','POST'])
def edit_chemical_analysis(id):
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    else:
        return redirect(url_for('chemical-analysis', id=id))
    api = drest.API(baseurl=env('API_DRF_HOST'))

    if len(dict(request.form)):
        new_analysis = literal_eval(json.dumps(request.form))
        new_analysis['id'] = id

        new_analysis['elements'] = []
        new_analysis['oxides'] = []
        for key in new_analysis.keys():
            if key[:9] == "elements_":
                e = new_analysis[key]
                new_analysis["elements"].append({'id': key[9:], 'amount': e[0], 'precision': e[1], 'precision_type': e[2], 'measurement_unit': e[3], 'min': e[4], 'max': e[5]})
                del new_analysis[key]
            if key[:7] == "oxides_":
                o = new_analysis[key]
                new_analysis["oxides"].append({'id': key[7:], 'amount': o[0], 'precision': o[1], 'precision_type': o[2], 'measurement_unit': o[3], 'min': o[4], 'max': o[5]})
                del new_analysis[key]

        new_analysis = api.make_request('POST','/chemical_analyses/'+id, params=new_analysis, headers=headers).data
        return redirect(url_for('chemical-analysis', id=id))

    analysis = api.make_request('GET','/chemical_analyses/'+id, params={'format': 'json'}).data
    analysis['sample'] = api.make_request('GET','/samples/'+analysis['subsample']['sample'], params={'fields': 'number', 'format': 'json'}).data

    minerals = api.make_request('GET','/minerals/', params={'page_size': 200, 'format': 'json'}).data['results']
    elements = api.make_request('GET','/elements/', params={'page_size': 50, 'format': 'json'}).data['results']
    oxides = api.make_request('GET','/oxides/', params={'page_size': 50, 'format': 'json'}).data['results']

    return render_template('edit_chemical_analysis.html',
        analysis=analysis,
        minerals=minerals,
        elements=elements,
        oxides=oxides
    )


@metpet_ui.route('/new-chemical-analysis/', methods=['GET', 'POST'])
def new_chemical_analysis():
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    else:
        return redirect(url_for('search-chemistry'))
    api = drest.API(baseurl=env('API_DRF_HOST'))

    if len(dict(request.form)):
        new_analysis = literal_eval(json.dumps(request.form))

        new_analysis['elements'] = []
        new_analysis['oxides'] = []
        for key in new_analysis.keys():
            if key[:9] == "elements_":
                e = new_analysis[key]
                new_analysis["elements"].append({'id': key[9:], 'amount': e[0], 'precision': e[1], 'precision_type': e[2], 'measurement_unit': e[3], 'min': e[4], 'max': e[5]})
                del new_analysis[key]
            if key[:7] == "oxides_":
                o = new_analysis[key]
                new_analysis["oxides"].append({'id': key[7:], 'amount': o[0], 'precision': o[1], 'precision_type': o[2], 'measurement_unit': o[3], 'min': o[4], 'max': o[5]})
                del new_analysis[key]

        new_analysis = api.make_request('POST','/chemical_analyses/'+id, params=new_analysis, headers=headers).data
        return redirect(url_for('search-chemistry'))

    minerals = api.make_request('GET','/minerals/', params={'page_size': 200, 'format': 'json'}).data['results']
    elements = api.make_request('GET','/elements/', params={'page_size': 50, 'format': 'json'}).data['results']
    oxides = api.make_request('GET','/oxides/', params={'page_size': 50, 'format': 'json'}).data['results']

    owner = api.make_request('GET','/users/', params={'email': email}).data['results']
    if len(owner) > 1:
        owner = None
    else:
        owner = owner[0]

    return render_template('edit_chemical_analysis.html',
        analysis={'owner': owner, 'sample': '', 'subsample': ''},
        minerals=minerals,
        elements=elements,
        oxides=oxides
    )


@metpet_ui.route('/login', methods=['GET', 'POST'])
def login():
    auth_token = session.get('auth_token', None)
    if auth_token:
        return redirect(url_for('search'))
    api = drest.TastyPieAPI(env('API_DRF_HOST'),auth_mech="basic")

    form = LoginForm()
    if form.validate_on_submit():
        auth_token = api.make_request('POST','/auth/login/', params={'email': form.email.data, 'password': form.password.data})
        print auth_token
        if 'auth_token' in auth_token:
            session['email'] = form.email.data
            session['auth_token'] = auth_token['auth_token']
            flash('Login successful!')
            return redirect(url_for('search'))
        else:
            flash('Authentication failed. Please try again.')
    return render_template('login.html', form=form)


@metpet_ui.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('auth_token', None)
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
            session['auth_token'] = data['auth_token']
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
    headers = None
    if session.get('auth_token', None):
        headers = {'email': session.get('email'), 'auth_token': session.get('auth_token')}
    api = drest.API(baseurl=env('API_DRF_HOST'))

    user = api.make_request('GET','/users/'+id, params={'format': 'json'}, headers=headers).data
    if "detail" in user:
        return render_template("warning.html", text="User "+id+" does not exist")
    return render_template('user.html', user=user)


if __name__ == '__main__':
    dotenv.read_dotenv('../app_variables.env')
    metpet_ui.run(debug=True)
