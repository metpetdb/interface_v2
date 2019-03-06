from flask import url_for
from urllib import urlencode

def paginate_model(model_name, data, filters):
    if 'count' in data:
        count = data['count']
    else:
        count = 0
    page = 1
    if 'page' in filters:
    	page = int(filters['page'])
    	del filters['page']
    size = 20
    if 'page_size' in filters:
        size = int(filters['page_size'])
    previous = None
    if 'previous' in data and data['previous']:
	    previous = url_for(model_name)+'?page='+str(page-1)+'&'+urlencode(filters)
    nextt = None
    if 'next' in data and data['next']:
        nextt = url_for(model_name)+'?page='+str(page+1)+'&'+urlencode(filters)
        print "=== NEXT IN DATA IS TRUE ===="
    last = url_for(model_name)+'?page='+str((count/size)+bool(count%size))+'&'+urlencode(filters)


    return (nextt, previous, last, count, page)

def combine_identical_parameters(paramsIn):
    paramsOut = {}
    listParams = ['rock_types', 'metamorphic_grades', 'minerals', 'fields', 'ordering', 'elements', 'oxides', 'countries', 'metamorphic_regions', 'regions']
    for param in paramsIn:
        if param[0] in listParams:
            if param[0] in paramsOut:
                paramsOut[param[0]] += ',' + param[1]
            else:
                paramsOut[param[0]] = param[1]
        else:
            paramsOut[param[0]] = param[1]
    return paramsOut

def handle_fields(filters,sample_search):
    def_sample = 'Subsamples,Chemical Analyses,Images,Minerals,Latitude,Longitude'
    def_chem = 'Analysis Method,Analysis Material,Elements,Oxides,Owner,Analysis Date,Total'
    if sample_search:
        fields_dict = {'Sample Number':'number','Subsamples':'subsample_ids', 'Chemical Analyses':'chemical_analyses_ids', 'Images':'images', 'Owner':'owner', 'Regions':'regions', \
                    'Country':'country','Metamorphic Grades':'metamorphic_grades', 'Metamorphic Regions':'metamorphic_regions', 'Minerals':'minerals', \
                    'References':'references', 'Latitude':'latitude', 'Longitude':'longitude', 'Collection Date':'collection_date', 'Rock Type':'rock_type'}
    else: # chemistry search
        fields_dict = {'Sample Number':'sample','Subsample':'subsample','Point':'spot_id','Analysis Method':'analysis_method','Analysis Material':'mineral', \
                        'Analysis Location':'where_done','Elements':'elements','Oxides':'oxides','Owner':'owner', \
                        'Analyst':'analyst','Analysis Date':'analysis_date','Total':'total'}

    # default values 
    if 'fields' not in filters:
        filters['fields'] = [def_sample] if (sample_search) else [def_chem]
    if type(filters['fields']) is str:
        filters['fields'] = [filters['fields']]
    # if sorting_name not in filters['fields'][0]:
    #     filters['fields'][0] += ','
    #     filters['fields'][0] += sorting_name # always show field used for sort
    # flip args back for pages

    if (filters['fields'][0].split(',')[0] == 'id') or filters['fields'][0].split(',')[0] == 'sample':
        rev_fields_dict = dict((v, k) for k, v in fields_dict.iteritems())
        field_vars = filters['fields'][0].split(',')[1:] if (sample_search) else filters['fields'][0].split(',')[3:] # skip ids
        field_names = []
        for var in field_vars:
            field_names.append(rev_fields_dict[var])
    else:
        # replace title values with variable names
        print "**** SAMPLE SEARCH: ",sample_search
        field_names = ['Sample Number'] if (sample_search) else ['Sample Number','Subsample','Point']  # always show sample number
        field_names += filters['fields'][0].split(',')
        field_vars = 'id' if sample_search else 'id,sample_id,subsample_id' # need sample id for link
        for name in field_names:
            if name in fields_dict:
                field_vars += ',' + fields_dict[name]
        filters['fields'] = [field_vars]



    return (filters['fields'], fields_dict, field_names)