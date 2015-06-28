import ast
import dotenv
import drest
from getenv import env
import json
from pathlib import Path
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
    EditChemForm
)
from lib.api import MetpetAPI
from utilities import paginate_model


mail = Mail()

metpet_ui = Flask(__name__)
metpet_ui.config.from_object('config')
mail.init_app(metpet_ui)
#mail = Mail(app)


@metpet_ui.route('/')
def index():
    return render_template('index.html')


@metpet_ui.route('/search/')
def search():
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    filters = dict(request.args)
    filter_dictionary = {}

    for key in filters:
        if filters[key][0]:
          if key != "resource":
            filter_dictionary[key] = ",".join(filters[key])

    #If View Samples selected
    if request.args.get('resource') == 'sample':
        #If minerals are selected, check for AND/OR
        #If AND, get samples with filters
        #If OR, union samples with mineral and samples with other filters
        if request.args.getlist('minerals__in'):

            #MINERAL AND
            if (request.args.get('mineralandor') == 'or'):
                url = url_for('samples') + '?' + urlencode(filter_dictionary)
                return redirect(url)

            #MINERAL OR
            elif request.args.get('mineralandor') == 'and':
                sample_results = []
                for key in filter_dictionary:
                    if (key != "minerals__in" and
                       key != "search_filters" and key != "fields" and key !=
                            "mineralandor"):
                        minerals = request.args.getlist('minerals__in')
                        for m in minerals:
                            samples = api.sample.get(
                                params={key : filter_dictionary[key],
                                        'minerals__in': m,
                                        'fields': 'sample_id,user__name,'
                                                  'collector,number,'
                                                  'public_data,'
                                                  'rock_type__rock_type,'
                                                  'subsample_count,'
                                                  'chem_analyses_count,'
                                                  'image_count,'
                                                  'minerals__name,'
                                                  'collection_date',
                                        'limit':0}).data['objects']
                            temp_list = [];
                            if not sample_results: 
                                sample_results = samples
                            else:
                                #intersect sample_results and samples
                                for s in sample_results:
                                    if s in samples:
                                        temp_list.append(s)
                                sample_results = temp_list

                #Build mineral list string for rendering results
                for sample in sample_results:
                    mineral_names = [str(m) for m in sample['minerals__name']]
                    sample['mineral_list'] = (', ').join(mineral_names)

                #Return data to samples template
                return render_template('samples_mineral_and_samples.html',
                                       samples=sample_results)

        #If no mineral, get samples with filters
        else:
            url = url_for('samples') + '?' + urlencode(filter_dictionary)
        return redirect(url)

    #If View Chemical Analyses selected
    elif request.args.get('resource') == 'chemicalanalysis':
    
        #If minerals are selected
        if request.args.getlist('minerals__in'):
            #MINERAL OR
            if (request.args.get('mineralandor') == 'or'):
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

            #MINERAL AND
            else:
                #Get sample IDs
                sample_results = []
                for key in filter_dictionary:
                    if key != "minerals__in" and key != "search_filters" and key != "fields" and key != "mineralandor":
                        minerals = request.args.getlist('minerals__in')
                        for m in minerals:
                            samples = api.sample.get(params={key : filter_dictionary[key], 'minerals__in': m,  'fields': 'sample_id', 'limit':0}).data['objects']
                            temp_list = [];
                            if not sample_results: 
                                sample_results = samples
                            else:
                                #intersect sample_results and samples
                                for s in sample_results:
                                    if s in samples:
                                        temp_list.append(s)
                                sample_results = temp_list
                
                sample_resources = ((',').join(str(s['sample_id']) for s in sample_results))

                #Get subsample IDs using sample IDs
                subsamples = api.subsample.get(params={'sample__in': sample_resources, 'fields': 'subsample_id', 'limit':0}).data['objects']
                subsample_resources = ((',').join(str(s['subsample_id']) for s in subsamples))
                #Get chemical analyses using subsample IDs
                chemical_analyses_results = api.chemical_analysis.get(params={'subsample__in': subsample_resources, 'fields': 'chemical_analysis_id,spot_id,public_data,analysis_method,where_done,analyst,analysis_date,reference_x,reference_y,total,mineral', 'limit': 0}).data['objects']  
                return render_template('samples_mineral_and_chemical_analyses.html', chemical_analyses=chemical_analyses_results)

        #If no minerals, get chemical analyses with get-chem-analyses-given-sample-filters
        else:
            request_obj = drest.api.API(baseurl=env('API_HOST'))
            if email and api_key:
                headers = {'email': email, 'api_key': api_key}
            else:
                headers = None
            response = (request_obj
                        .make_request('GET',
                           '/get-chem-analyses-given-sample-filters/',
                           params=filter_dictionary,
                           headers=headers
                        ))
            ids = response.data['chemical_analysis_ids']

            url = (url_for('chemical_analyses')
                   + '?'
                   + urlencode({'chemical_analysis_id__in': ids}))
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
    samples = api.sample.get(params={'fields': 'user__user_id,user__name,collector,number,sesar_number,country,public_data', 
                                     'limit': 0}).data['objects']
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

    m_list= []
    mineral_list = []
    m_list = parents.union(children)
    for (name, mid) in m_list:
        mineral_list.append({"name": name, "id": mid})

    mineralnodes = []
    for (name, mid) in mineralroots:
        mineralnodes.append({"id": name, "parent": "#", "text": name, "mineral_id": mid})
    for m in mineral_relationships:
        node = {"id": m['child_mineral__name'], "parent": m['parent_mineral__name'], "text": m['child_mineral__name'], "mineral_id": m['child_mineral__mineral_id']}
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

    owner_dict = {}
    if email:
        logged_in_user = api.user.get(params={'email': email,
                                              'fields': 'user_id,name'}).data['objects']
        owner_dict[logged_in_user[0]['user_id']] = logged_in_user[0]['name']

    for sample in samples:
        collector_list.append(unicode(sample['collector']))
        number_list.append(sample['number'])
        igsn_list.append(sample['sesar_number'])
        country_list.append(sample['country'])
        """The 'owners' list in the Provenance tab should contain only users
        with public samples"""
        if sample['public_data'] == 'Y':
            if not sample['user__user_id'] in owner_dict:
                owner_dict[sample['user__user_id']] = sample['user__name']

    collector_list = list (set ( collector_list ))
    country_list = list(set (country_list))
    return render_template('search_form.html',
                            query='',
                elements=element_list,
                oxides=oxide_list,
                            regions=region_list,
                mineralrelationships=json.dumps(mineral_relationships),
                mineral_nodes=json.dumps(mineralnodes),
                            minerals=mineral_list,
                            rock_types=rock_types,
                            provenances=collector_list,
                            references=reference_list,
                numbers=number_list,
                            igsns=igsn_list,
                countries=country_list,
                owners = owner_dict,
                            metamorphic_regions=metamorphic_region_list,
                            metamorphic_grades=metamorphic_grade_list)

@metpet_ui.route('/search-chemistry/')
def search_chemistry():
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
    if request.args :
        if 'squirrel' not in request.args and request.args.get('resource') == 'chemicalanalysis':
            return render_template('chem_search_chemical_analyses.html', can=request.args.get("results"))
        elif 'squirrel' not in request.args and request.args.get('resource') == 'sample':
            return render_template('chem_search_samples.html', samples=request.args.get("results"))
            #url = url_for('chem_search_chemical_analyses') + '?' + \
            #  urlencode({'chemical_analyses': request.args.get("chemical_analyses")})
            #return redirect(url)

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

        sample_resources = api.subsample.get(params={'subsample_id__in': (',').join(str(s) for s in subsample_ids), 'fields': 'sample', 'limit':0}).data['objects']
        sample_ids = set()
        for s in sample_resources:
            #Remove first 18 characters and trailing /
            sample_id = s['sample'].replace("Sample #", "")
            sample_ids.add(sample_id)
        sample_results = api.sample.get(params={'sample_id__in': (',').join(str(s) for s in sample_ids), 'fields': 'sample_id,user__name,collector,number,public_data,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date', 'limit':0}).data['objects']
        return json.dumps(sample_results)

    #Get samples for (O, M)
    elif 'oxides__oxide_id__in' in request.args and request.args.get('resource') == 'sample':
        subsample_resources = api.chemical_analysis.get(params={'oxides__oxide_id__in': oxide, 'minerals__in': mineral_ids, 'fields': 'subsample', 'limit': 0}).data['objects']
        subsample_ids = set()
        for s in subsample_resources:
            #Remove first 18 characters and trailing /
            subsample_id = s['subsample'].replace("Subsample #", "")
            subsample_ids.add(subsample_id)

        sample_resources = api.subsample.get(params={'subsample_id__in': (',').join(str(s) for s in subsample_ids), 'fields': 'sample', 'limit':0}).data['objects']
        sample_ids = set()
        for s in sample_resources:
            #Remove first 18 characters and trailing /
            sample_id = s['sample'].replace("Sample #", "")
            sample_ids.add(sample_id)
        sample_results = api.sample.get(params={'sample_id__in': (',').join(str(s) for s in sample_ids), 'fields': 'sample_id,user__name,collector,number,public_data,rock_type__rock_type,subsample_count,chem_analyses_count,image_count,minerals__name,collection_date', 'limit':0}).data['objects']
        return json.dumps(sample_results)

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

    rock_types = (api.rock_type.get(
                      params={'order_by': 'rock_type',
                              'limit': 0})
                  .data['objects'])

    regions = (api.region.get(
                   params={'order_by': 'name',
                           'limit': 0})
                .data['objects'])

    references = (api.reference.get(
                      params={'order_by': 'name',
                              'limit': 0})
                  .data['objects'])

    metamorphic_regions = (api.metamorphic_region.get(
                              params={'order_by': 'name',
                                      'limit': 0})
                          .data['objects'])

    metamorphic_grades = (api.metamorphic_grade.get(
                             params={'limit': 0})
                          .data['objects'])

    samples = (api.sample.get(
                   params={'fields': 'user__user_id,user__name,collector,'
                                     'number,sesar_number,country,public_data',
                           'limit': 0})
               .data['objects'])

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
    m_list= []
    mineral_list = []
    m_list = parents.union(children)
    for (name, mid) in m_list:
        mineral_list.append({"name": name, "id": mid})

    mineralnodes = []
    mineralnodes.append({"id": "Minerals",
                         "parent" : "#",
                         "text": "Minerals"})

    for (name, mid) in mineralroots:
        mineralnodes.append({"id": name,
                             "parent": "Minerals",
                             "text": name,
                             "mineral_id": mid})

    for m in mineral_relationships:
        node = {"id": m['child_mineral__name'],
                "parent": m['parent_mineral__name'],
                "text": m['child_mineral__name'],
                "mineral_id": m['child_mineral__mineral_id']}
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

    owner_dict = {}
    if email:
        logged_in_user = (api.user.get(params={'email': email,
                                              'fields': 'user_id,name'})
                                     .data['objects'])
        owner_dict[logged_in_user[0]['user_id']] = logged_in_user[0]['name']

    for sample in samples:
        collector_list.append(unicode(sample['collector']))
        number_list.append(sample['number'])
        igsn_list.append(sample['sesar_number'])
        country_list.append(sample['country'])
        """The 'owners' list in the Provenance tab should contain only users
        with public samples"""
        if sample['public_data'] == 'Y':
            if not sample['user__user_id'] in owner_dict:
                owner_dict[sample['user__user_id']] = sample['user__name']

    collector_list = list (set ( collector_list ))
    country_list = list(set (country_list))
    return render_template('chemical_search_form.html',
                            query='',
                            elements=element_list,
                            oxides=oxide_list,
                            regions=region_list,
                            mineralrelationships=json.dumps(mineral_relationships),
                            minerals=mineral_list,
                            mineral_nodes=json.dumps(mineralnodes),
                            rock_types=rock_types,
                            provenances=collector_list,
                            references=reference_list,
                            numbers=number_list,
                            igsns=igsn_list,
                            countries=country_list,
                            owners = owner_dict,
                            metamorphic_regions=metamorphic_region_list,
                            metamorphic_grades=metamorphic_grade_list)


@metpet_ui.route('/login', methods=['GET', 'POST'])
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
            print session
            flash('Login successful!')
            return redirect(url_for('search'))
        else:
            flash('Authentication failed. Please try again.')


    return render_template('login.html',
                            form=form)


@metpet_ui.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('api_key', None)
    flash('Logout successful.')
    return redirect(url_for('search'))


@metpet_ui.route('/request-password-reset', methods=['GET', 'POST'])
def request_reset_password():
    form = RequestPasswordResetForm()

    if form.validate_on_submit():
        payload = {'email': form.email.data}
        response = post(env('API_HOST') + '/reset-password/', data=payload)
        if response.status_code == 200:
            data = json.loads(response.text)
            message = Message("Metpetdb: Reset Password",
                               # sender = 'metpetdb@gmail.com',
                               sender=env('DEFAULT_MAIL_SENDER'),
                               recipients= [form.email.data])
            reset_url = url_for('reset_password', token=data['reset_token'],
                                 _external=True)
            message.body = render_template('reset_password_email.html',
                                           reset_url=reset_url)
            print message.recipients, message.sender, message.body
            mail.send(message)
            flash('Please check your email for a link to reset your password')
            return redirect(url_for('login'))
        else:
            flash("Invalid email. Please try again.")

    return render_template('request_password_reset.html', form=form)


@metpet_ui.route('/reset-password/<string:token>', methods=['GET', 'POST'])
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


@metpet_ui.route('/samples/')
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

        if 'minerals' in samples:
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


@metpet_ui.route('/edit_chemical/<int:id>', methods = ['GET','POST'])
def edit_chemical(id):
  form = EditChemForm()
  email = session.get('email', None)
  api_key = session.get('api_key', None)
  api = MetpetAPI(email,api_key).api
  payload = {'email': email, 'api_key': api_key}

  url = env('API_HOST') + '/chemical_analysis/{0}'.format(id)
  response = get(url, params=payload)
  data = response.json()

  filters = ast.literal_eval(json.dumps(request.args))
  offset = request.args.get('offset', 0)
  filters['offset'] = offset

  data2 = api.chemical_analysis.get(params=filters)
  next, previous, last, total_count = paginate_model('chemical_analyses',
                                                      data2, filters)
  oxide_list=[]
  element_list=[]
  oxides = api.oxide.get(params={'limit': 0}).data['objects']

  for oxide in oxides:
      oxide_list.append(oxide)

  elements = api.element.get(params={'limit': 0}).data['objects']
  for element in elements:
    element_list.append(element)
    print element



  if form.validate_on_submit():
    data['chemical_analysis']['owner_name'] = form.owner.data
    data['chemical_analysis']['public_data'] = form.public.data
    data['chemical_analysis']['analyst'] = form.analyst.data
    data['chemical_analysis']['analysis_material'] =form.analysis_material.data
    data['chemical_analysis']['total'] =form.total.data
    data['chemical_analysis']['stage_x']=form.StageX.data
    data['chemical_analysis']['stage_y']=form.StageY.data
    return redirect(url_for('search'))
  else:
    form.owner.data = data['chemical_analysis']['owner_name']
    form.public.data = data['chemical_analysis']['public_data']
    form.analyst.data = data['chemical_analysis']['analyst']
    form.analysis_material.data = data['chemical_analysis']['analysis_material']
    form.total.data = data['chemical_analysis']['total']
    form.StageX.data = data['chemical_analysis']['stage_x']
    form.StageY.data = data['chemical_analysis']['stage_y']

  return render_template('edit_chemical.html',
                          form = form,
                          data = data,
                          oxide_list = oxide_list,
                          element_list = element_list,
                          id = id,
                          api_key = api_key)

@metpet_ui.route('/edit_sample/<int:id>', methods = ['GET','POST'])
def edit_sample(id):
  form = EditForm(minerals=True)
  email = session.get('email', None)
  api_key = session.get('api_key', None)
  api = MetpetAPI(email,api_key).api
  api.auth(user=email,
           api_key=api_key)

  sample = api.sample.get(id).data
  sample2 = api.sample.get(id)
  rock_type_list = []
  rock_type = api.rock_type.get(
      params={'order_by': 'rock_type', 'limit': 0}).data['objects']
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

  metamorphic_regions = [metamorphic_region['name']
                         for metamorphic_region in sample['metamorphic_regions']]

  minerals = [mineral['name'] for mineral in sample['minerals']]
  new_regions = []

  form.minerals.choices = [(mineral, mineral) for mineral in minerals]

  if form.validate_on_submit():
    sample2.data['user']['name'] = form.owner.data
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
    print list_name
    sample2 = api.sample.put(id, sample2.data)

    return redirect(url_for('search'))
  else:
    form.owner.data = sample['user']['name']
    form.public.data = sample['public_data']
    form.location_text.data = sample['location_text']
    form.collector.data = sample['collector']
    form.rock_type.data = sample['rock_type']['rock_type']
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

@metpet_ui.route('/sample/<int:id>')
def sample(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)
    api = MetpetAPI(email, api_key).api

    sample = api.sample.get(id).data
    #sample_owner = sample['owner']
    #print sample
    sampleid = sample['sample_id']
    #print sample['user']['name']

    location = sample['location'].split(" ")
    longtitude = location[1].replace("(","")
    latitude = location[2].replace(")","")
    loc = [longtitude, latitude]

    filter = {"sample__sample_id": sample['sample_id'], "limit": "0"}

    subsamples = api.subsample.get(params=filter).data['objects']

    aliases = api.sample_alias.get(params=filter).data['objects']
    aliases_str = [alias['alias'] for alias in aliases]

    regions = [region['name'] for region in sample['regions']]
    metamorphic_regions = [metamorphic_region['name']
                           for metamorphic_region in sample['metamorphic_regions']]
    metamorphic_grades = [metamorphic_grade['name']
                          for metamorphic_grade in sample['metamorphic_grades']]
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
                                subsamples=subsamples,
                                sampleid=sampleid,
                                api_key=api_key)
    else:
        return ("Sample does not Exist", 404)


@metpet_ui.route('/subsample/<int:id>')
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
        return ("Subsample does not Exist", 404)


@metpet_ui.route('/chemical_analyses/')
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

    for a in chemical_analyses:
      print a

    first_page_filters = filters
    del first_page_filters['offset']

    if filters:
        first_page_url = (url_for('chemical_analyses')
                          + '?'
                          + urlencode(first_page_filters))
    else:
        first_page_url = (url_for('chemical_analyses')
                         + urlencode(first_page_filters))

    return render_template('chemical_analyses.html',
                            chemical_analyses=chemical_analyses,
                            next_url=next,
                            prev_url=previous,
                            total=total_count,
                            first_page=first_page_url,
                            last_page=last)


@metpet_ui.route('/chemical_analysis/<int:id>')
def chemical_analysis(id):
    email = session.get('email', None)
    api_key = session.get('api_key', None)

    payload = {'email': email, 'api_key': api_key}

    url = env('API_HOST') + '/chemical_analysis/{0}'.format(id)
    response = get(url, params=payload)
    data1 = response.json()
    print data1['chemical_analysis']['id']

    return render_template('chemical_analysis.html',
                            api_key = api_key, data=response.json())


@metpet_ui.route('/user/<int:id>')
def user(id):
    api = MetpetAPI(None, None).api
    user = api.user.get(id).data
    if sample:
        return render_template('user.html', user=user)
    else:
        return ("User does not Exist", 404)


if __name__ == '__main__':
    dotenv.read_dotenv(Path.cwd().joinpath('app_variables.env').as_posix())
    metpet_ui.run(debug=True)
