import dotenv, commands, json, os 
from getenv import env
from requests import get, put, post, codes
from urllib import urlencode, urlopen
from flask import (
    Flask,
    request,
    render_template,
    url_for,
    redirect,
    request,
    jsonify,
    flash,
    session
)
from flask_mail import Mail, Message
from utilities import paginate_model, combine_identical_parameters, handle_fields

mail = Mail()
metpet_ui = Flask(__name__)
metpet_ui.config.from_object("config")
mail.init_app(metpet_ui)

dotenv.read_dotenv("../app_variables.env")

@metpet_ui.route("/")
def index():
    return render_template("index.html",
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/search/")
def search():
    print "search Arguments: ",request.args
    print "session data: ", session
    #get all filter options from API, use format = json and minimum page sizes to speed it up
    if request.args.get("resource") == "samples":
        #resource value set in search_form.html, appends samples.html to bottom of page
        fixedListArgs = combine_identical_parameters(request.args.iteritems(multi=True))
        return redirect(url_for("samples")+"?"+urlencode(fixedListArgs))

    if request.args.get("resource") == "chemical_analyses":
        #minerals_and option not valid parameter for analyses
        #sets sample_filters b/c search samples only has sample filters
        #appends chemical_analyses.html to bottom of page
        fixedListArgs = combine_identical_parameters(request.args.iteritems(multi=True))
        return redirect(url_for("chemical_analyses")+"?"+urlencode(fixedListArgs)+"&sample_filters=True")

    #get all filter options from API, use format = json and minimum page sizes to speed it up
    regions = get(env("API_HOST")+"regions/", params = {"fields": "name", "page_size": 2000, "format": "json"}).json()["results"]
    minerals = get(env("API_HOST")+"minerals/", params = {"fields": "name", "page_size": 200, "format": "json"}).json()["results"]
    rock_types = get(env("API_HOST")+"rock_types/", params = {"fields": "name", "page_size": 40, "format": "json"}).json()["results"]
    collectors = get(env("API_HOST")+"collectors/", params = {"fields": "name", "page_size": 140, "format": "json"}).json()["results"]
    references = get(env("API_HOST")+"references/", params = {"fields": "name", "page_size": 2000, "format": "json"}).json()["results"]
    metamorphic_grades = get(env("API_HOST")+"metamorphic_grades/", params = {"fields": "name", "page_size": 30, "format": "json"}).json()["results"]
    metamorphic_regions = get(env("API_HOST")+"metamorphic_regions/", params = {"fields": "name", "page_size": 240, "format": "json"}).json()["results"]
    fields_dict = {'Subsamples':'subsample_ids', 'Chemical Analyses':'chemical_analyses_ids', 'Images':'images', 'Owner':'owner', 'Regions':'regions', \
                'Country':'country','Metamorphic Grades':'metamorphic_grades', 'Metamorphic Regions':'metamorphic_regions', 'Minerals':'minerals', \
                'References':'references','Latitude':'latitude', 'Longitude':'longitude', 'Collection Date':'collection_date', 'Rock Type':'rock_type'}
    sorting_dict = {'Sample Number':'number','Subsamples':'subsamples', 'Collection Date':'collection_date','Subsamples':'subsamples', 'Country':'country', \
                'Images':'images','Metamorphic Grades':'metamorphic_grades','Owner':'owner__name', 'References':'references__name', \
                'Rock Type':'rock_type__name', \
                'Chemical Analyses':'chemical_analyses'}
    countries = get(env("API_HOST")+"country_names/", params = {"format": "json"}).json()["country_names"]
    numbers = get(env("API_HOST")+"sample_numbers/", params = {"format": "json"}).json()["sample_numbers"]
    owners = get(env("API_HOST")+"sample_owner_names/", params = {"format": "json"}).json()["sample_owner_names"]
 
    return render_template("search_form.html",
        regions = regions,
        minerals = minerals,
        rock_types = rock_types,
        collectors = collectors,
        references = references,
        metamorphic_grades = metamorphic_grades,
        metamorphic_regions = metamorphic_regions,
        sorting_dict = sorted(sorting_dict),
        fields = sorted(fields_dict.keys()),
        countries = countries,
        numbers = sorted(numbers),
        owners = sorted(set(owners)),
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/search-chemistry/")
def search_chemistry():
    #basically the same as search samples but with analysis filter options
    if request.args.get("resource") == "chemical_analyses":
        fixedListArgs = combine_identical_parameters(request.args.iteritems(multi=True))
        return redirect(url_for("chemical_analyses")+"?"+urlencode(fixedListArgs))

    if request.args.get("resource") == "sample":
        fixedListArgs = combine_identical_parameters(request.args.iteritems(multi=True))
        return redirect(url_for("samples")+"?"+urlencode(fixedListArgs)+"&chemical_analyses_filters=True")
    #Add headers for authentication of 


    oxides = {}
    elements = {}
    minerals = {}
    try:
        headers = {"Authorization":"Token "+session["auth_token"]}
        print "private search chemistry"
        print "HEADER:",headers
        oxides = get(env("API_HOST")+"oxides/", params = {"fields": "species", "page_size": 100, "format": "json"},headers = headers).json()["results"]
        elements = get(env("API_HOST")+"elements/", params = {"fields": "name,symbol", "page_size": 120, "format": "json"},headers=headers).json()["results"]
        minerals = get(env("API_HOST")+"minerals/", params = {"fields": "name", "page_size": 200, "format": "json"},headers = headers).json()["results"]
        fields_dict = {'Analysis Method':'analysis_method','Analysis Material':'mineral','Subsample Type':'subsample_type', \
                        'Stage X':'stage_x','Stage Y':'stage_y','Reference X':'reference_x','Reference Y':'reference_y', \
                        'Analysis Location':'where_done','Elements':'elements','Oxides':'oxides','Owner':'owner', \
                        'Analyst':'analyst','Analysis Date':'analysis_date','Total':'total'}
    except:
        print "public search chemistry"
        headers = {}
        oxides = get(env("API_HOST")+"oxides/", params = {"fields": "species", "page_size": 100, "format": "json"}).json()["results"]
        elements = get(env("API_HOST")+"elements/", params = {"fields": "name,symbol", "page_size": 120, "format": "json"}).json()["results"]
        minerals = get(env("API_HOST")+"minerals/", params = {"fields": "name", "page_size": 200, "format": "json"}).json()["results"]
        fields_dict = {'Analysis Method':'analysis_method','Analysis Material':'mineral','Subsample Type':'subsample_type', \
                        'Stage X':'stage_x','Stage Y':'stage_y','Reference X':'reference_x','Reference Y':'reference_y', \
                        'Analysis Location':'where_done','Elements':'elements','Oxides':'oxides','Owner':'owner', \
                        'Analyst':'analyst','Analysis Date':'analysis_date','Total':'total'}

    print 'len',len(oxides),len(elements),len(minerals)
    return render_template("chemical_search_form.html",
        oxides = oxides,
        elements = elements,
        minerals = minerals,
        fields_dict = sorted(fields_dict),
        fields = sorted(fields_dict.keys()),
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/samples/")
def samples():
    #filters sent as parameters to API calls
    #only return public data samples if not logged in
    # put header data here
    headers = None
    #this ideally should do nothing if passed to the metpetdb api

    filters = dict(request.args)
    tmp_var = 0
    print("tokens")
    print(session)
    print("Pre-processing filters")
    print(filters)

    # handle sorting
    sorting_dict = {'Sample Number':'number','Subsample Count':'subsamples', 'Collection Date':'collection_date','Subsamples':'subsamples', 'Country':'country', \
                'Images':'images','Metamorphic Grades':'metamorphic_grades','Owner':'owner__name', 'References':'references__name', 'Rock Type':'rock_type__name', \
                'Chemical Analyses':'chemical_analyses'}
    if 'ordering' in filters and filters['ordering'] != ['']:
        sorting_name = filters['ordering'][0]
    else:
        sorting_name = 'Sample Number' # default
    if sorting_name in sorting_dict: #b all but second page
        filters['ordering'] = [sorting_dict[sorting_name]]
    else: # second page
        rev_sorting_dict = dict((v, k) for k, v in sorting_dict.iteritems())
        sorting_name = rev_sorting_dict[filters['ordering'][0]]
    print 'sorting by: ',sorting_name

    # format fields in request and keep list of titles for interface
    filters['fields'], fields_dict, field_names = handle_fields(filters,True)
    # print 'filters after handling: ', filters['fields']
    # print 'field_names after handling: ', field_names

    for key in filters.keys():
        # Key is a map polygon
        if key == "polygon_coords" and filters[key][0]:
            # List of coordinate point strings; remove trailing comma, starting/trailing bracket,
            #   and split into coordinate points
            coords = filters[key][0].strip(',').strip('[').strip(']').split('],[')
            # Tack the first coordinate on to the end of the list so that the coordinates
            #   form a closed loop
            coords.append(coords[0])
            # Reassemble coordinates to be a list of two-element lists
            coords = '[[' + ('],[').join(coords) + ']]'
            filters[key] = coords
            print "FINAL POLY COORDS: "
            print(filters[key])
            print(key)
        # Strip unused time values for start & end date queries
        if (key == "start_date" or key == "end_date") and filters[key]:
            filters[key] = filters[key][0][0:10]
        # Unnecessary, empty, or blank key
        elif key == "polygon_coord": # or not filters[key] or filters[key] == '' or filters[key][0] == '':
            del filters[key]
        # Any other key
        else:
            # Turn list into a comma-separated string
            filters[key] = (',').join([e for e in filters[key] if e and e[0]])

    print("Post-processing filters:")
    print(filters)
    filters["format"] = "json"
    samples = {}
    try:   

        headers = {"Authorization":"Token "+session["auth_token"]} 
        print "HEADER:",headers
        samples = get(env("API_HOST")+"samples/", params = filters,headers= headers).json()
        print "URL: ",get(env("API_HOST")+"samples/", params = filters,headers= headers)
    except KeyError:
        samples = get(env("API_HOST")+"samples/",params = filters).json()

    # print samples
    try:
        sample_results = samples["results"]
    except:
        try:
            error = samples["error"]
            print error
            samples = {}
            sample_results = {}
        except: 
            samples = {}
            sample_results = {}

    next_url, prev_url, last_page, total, page_num = paginate_model("samples", samples, filters)


    # clean up values for samples view
    for s in sample_results:
        if "metamorphic_grades" in s:
            s["metamorphic_grades"] = (", ").join([g for g in sorted(s["metamorphic_grades"])])
        if "metamorphic_regions" in s:
            s["metamorphic_regions"] = (", ").join([r for r in sorted(s["metamorphic_regions"])])
        if "minerals" in s:
            s["minerals"] = (", ").join([m for m in sorted(s["minerals"])])
        if "references" in s:
            s["references"] = (", ").join([r for r in sorted(s["references"])])
        if "regions" in s:
            s["regions"] = (", ").join([m for m in sorted(s["regions"])])

    csv_url = env("API_HOST") + "samples/?" + urlencode(filters) + "&format=csv"        


    return render_template("samples.html",
        samples = sample_results,
        field_names = field_names,
        fields_dict = fields_dict,
        sorting_dict = sorting_dict,
        sorting_name = sorting_name,
        showmap = "showmap" in filters,
        extends = "render" in filters,
        total = total,
        page_num = page_num,
        next_url = next_url,
        prev_url = prev_url,
        first_page = url_for("samples")+"?"+urlencode(filters),
        last_page = last_page,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None),
        csv_url = csv_url
    )


@metpet_ui.route("/sample/<string:id>")
def sample(id):
    #headers! to authenticate user during API calls (for private data and to add/edit their samples)
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}

    #get the sample the usual way and return error message if something went wrong
    sample = get(env("API_HOST")+"samples/"+id+"/", params = {"format": "json"}, headers = headers).json()
    if "detail" in sample:
        flash(sample["detail"])
        return redirect(url_for("search"))

    #make lat/long and date nice
    # pos = sample["location_coords"].split(" ")
    # sample["location_coords"] = [round(float(pos[2].replace(")","")),5), round(float(pos[1].replace("(","")),5)]
    # if sample["collection_date"]:
    #     sample["collection_date"] = sample["collection_date"][:-10]

    #get subsample and analysis data for tables
    subsamples = []
    for s in sample["subsample_ids"]:
        subsamples.append(get(env("API_HOST")+"subsamples/"+s,
            params = {"fields": "subsample_type,name,id,public_data,owner", "format": "json"}, headers = headers).json())
    for s in subsamples:
        s["chemical_analyses"] = get(env("API_HOST")+"chemical_analyses/",
            params = {"subsample_ids": s["id"], "fields": "id", "format": "json"}, headers = headers).json()["results"]

    return render_template("sample.html",
        sample = sample,
        subsamples = subsamples,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/edit-sample/<string:id>", methods = ["GET", "POST"])
def edit_sample(id):
    #this time redirect to sample page if not logged in
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("sample", id = id))
    print "edit sample:",headers
    errors = []
    new = (id.lower() == "new")

    #edit_sample.html is a form with mostly the right input names
    sample = dict(request.form)
    response_text = "" # have sample response text in case of a forbidden access (403) error
    if sample:
        #minerals are named by id, make it into a nested list of dictionaries
        sample["minerals"] = []
        for key in sample.keys():
            if key[:9] == "minerals_":
                sample["minerals"].append({"id": key[9:], "amount": sample[key][0]})
                del sample[key]
            elif key[-1] != "s" and sample[key]:
                sample[key] = sample[key][0]
            elif key[-1] == "s":
                sample[key] = filter(lambda k: k != "", sample[key])

        if not sample["collection_date"]:
            del sample["collection_date"]

        sample['latitude'] = sample['location_coords1']
        sample['longitude'] = sample['location_coords0']
        del sample["location_coords0"]
        del sample["location_coords1"]

        if new:
            print "new edit-sample headers", headers
            print "new edit-sample sample", sample
            response = post(env("API_HOST")+"samples/", json = sample, headers = headers)
        else:
            response = put(env("API_HOST")+"samples/"+id+"/", json = sample, headers = headers)
            print "old edit-sample headers", headers
            print "old edit-sample sample", sample
        print "edit-sample status code:",response.status_code
        print "edit-sample response:",response.json()
        if response.status_code < 300:
            return redirect(url_for("sample", id = response.json()["id"]))
        if response.status_code == 403:
            response_text = response.json()['detail']
        errors = response.json()

    #get sample data and split point into lat/long
    if new:
        sample["owner"] = get(env("API_HOST")+"users/"+session.get("id")+"/", headers = headers).json()
    else:
        sample = get(env("API_HOST")+"samples/"+id+"/", params = {"format": "json"}, headers = headers).json()
        # pos = sample["location_coords"].split(" ")
        # sample["location_coords"] = [float(pos[2].replace(")","")), float(pos[1].replace("(",""))]
        sample["references"] = [r for r in sample["references"]]

    #get all the other data
    regions = get(env("API_HOST")+"regions/", params = {"page_size": 2000, "format": "json"}).json()["results"]
    minerals = get(env("API_HOST")+"minerals/", params = {"page_size": 200, "format": "json"}).json()["results"]
    rock_types = get(env("API_HOST")+"rock_types/", params = {"page_size": 40, "format": "json"}).json()["results"]
    references = get(env("API_HOST")+"references/", params = {"page_size": 2000, "format": "json"}).json()["results"]
    metamorphic_grades = get(env("API_HOST")+"metamorphic_grades/", params = {"page_size": 30, "format": "json"}).json()["results"]
    metamorphic_regions = get(env("API_HOST")+"metamorphic_regions/", params = {"page_size": 240, "format": "json"}).json()["results"]
    countries = get(env("API_HOST")+"country_names/").json()["country_names"]

    return render_template("edit_sample.html",
        sample = sample,
        regions = regions,
        minerals = minerals,
        rock_types = rock_types,
        references = references,
        metamorphic_grades = metamorphic_grades,
        metamorphic_regions = metamorphic_regions,
        countries = countries,
        errors = errors,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None),
        response_code = response_text
    )


@metpet_ui.route("/subsample/<string:id>")
def subsample(id):
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}

    #get subsample info
    subsample = get(env("API_HOST")+"subsamples/"+id+"/", params = {"format": "json"}, headers = headers).json()
    if "detail" in subsample:
        flash(subsample['detail'])
        return redirect(url_for("search"))

    #get sample and analysis info
    # (unnecessary with new serializer)
    # subsample["sample"]["number"] = get(env("API_HOST")+"samples/"+subsample["sample"]["id"],
    #     params = {"fields": "number", "format": "json"}, headers = headers).json()["number"]
    chemical_analyses = get(env("API_HOST")+"chemical_analyses/", params = {"subsample_ids": subsample["id"], "format": "json"},headers=headers).json()["results"]

    return render_template("subsample.html",
        subsample = subsample,
        chemical_analyses = chemical_analyses,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/edit-subsample/<string:id>", methods = ["GET", "POST"])
def edit_subsample(id):
    #similar to but much simpler than edit sample
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("subsample", id = id))
    new = (id == "new")

    if new:
        sample = get(env("API_HOST")+"samples/"+request.args.get("sample_id")+"/", params = {"fields": "id,number,owner"}, headers = headers).json()
    subsample = dict(request.form)
    print subsample
    if subsample:
        for key in subsample.keys():
            if subsample[key] and subsample[key][0]:
                subsample[key] = subsample[key][0]


        if new:
            subsample["owner"] = get(env("API_HOST")+"users/", params = {"email": session.get("email")}, headers = headers).json()
            subsample["sample"] = sample["id"]
            response = post(env("API_HOST")+"subsamples/", json = subsample, headers = headers)
        else:
            response = put(env("API_HOST")+"subsamples/"+id+"/", json = subsample, headers = headers)
        if response.status_code < 300:
            return redirect(url_for("subsample", id = response.json()["id"]))
        try:
            errors = response.json()
        except:
            errors = []
    else:
        errors = []

    if new:
        subsample = {"owner": sample["owner"], "sample": subsample}
    else:
        subsample = get(env("API_HOST")+"subsamples/"+id+"/", params = {"format": "json"}, headers = headers).json()
        subsample["owner"] = get(env("API_HOST")+"users/"+subsample["owner"]["id"], params = {"format": "json"}, headers = headers).json()
    types = get(env("API_HOST")+"subsample_types/", headers = headers).json()["results"]

    return render_template("edit_subsample.html",
        subsample = subsample,
        types = types,
        errors = errors,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/chemical-analyses/")
def chemical_analyses():
    #similar to samples
    filters = dict(request.args)

    for key in filters.keys():
        f = ""
        for i in range(len(filters[key])):
            if filters[key][i]:
                f += str(filters[key][i])+','
        if f:
            filters[key] = f[:-1]
        else:
            del filters[key]
    filters["format"] = "json"
    if "minerals_and" in filters:
        del filters["minerals_and"]

    # dynamic fields
    fields_dict = {'Sample Number':'sample','Subsample':'subsample','Point':'spot_id','Analysis Method':'analysis_method','Analysis Material':'mineral', \
                    'Stage X':'stage_x','Stage Y':'stage_y','Reference X':'reference_x','Reference Y':'reference_y','Subsample Type':'subsample_type', \
                    'Analysis Location':'where_done','Elements':'elements','Oxides':'oxides','Owner':'owner', \
                    'Analyst':'analyst','Analysis Date':'analysis_date','Total':'total'}
    fields_list, fields_dict, field_names = handle_fields(filters,False)
    filters['fields'] = fields_list[0]
    print '*** filters after handling: ', filters['fields']
    print '*** field names after handling: ', field_names

    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        filters["public_data"] = True

    ##MAKES Chemicals private visible to uploaders
    chemicals = get(env("API_HOST")+"chemical_analyses/", params = filters,headers=headers).json()
    chem_results = chemicals["results"]

    # if 'page' in filters:
    #     page_num = int(filters['page'])
    next_url, prev_url, last_page, total, page_num = paginate_model("chemical_analyses", chemicals, filters)

    print "length is ",len(chem_results)

    for c in chem_results:
        # c["sample"] = numbers[c["subsample"]["sample"]]
        if "analysis_date" in c and c['analysis_date']:
            c["analysis_date"] = c["analysis_date"][:-10]

    csv_url = env("API_HOST") + "chemical_analyses/?" + urlencode(filters) + "&format=csv"

    return render_template("chemical_analyses.html",
        chemical_analyses = chem_results,
        field_names = field_names,
        fields_dict = fields_dict,
        total = total,
        page_num = page_num,
        next_url = next_url,
        prev_url = prev_url,
        first_page = url_for("chemical_analyses")+"?"+urlencode(filters),
        extends = "render" in filters,
        last_page = last_page,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None),
        csv_url = csv_url
    )


@metpet_ui.route("/chemical-analysis/<string:id>")
def chemical_analysis(id):
    #similar to sample and subsample
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}

    analysis = get(env("API_HOST")+"chemical_analyses/"+id+"/", params = {"format": "json"}, headers = headers).json()
    if "detail" in analysis:
        flash(analysis['detail'])
        return redirect(url_for("search_chemistry"))

    return render_template("chemical_analysis.html",
        analysis = analysis,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/edit-chemical-analysis/<string:id>,<string:subsample_id>", methods = ["GET", "POST"])
def edit_chemical_analysis(id, subsample_id):
    #again, similar to edit sample and edit subsample
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("chemical_analysis", id = id))
    errors = []
    new = (id == "new")

    analysis = dict(request.form)
    if analysis:
        #this part is just like minerals from edit sample
        analysis["elements"] = []
        analysis["oxides"] = []
        for key in analysis.keys():
            if key[:9] == "elements_":
                e = analysis[key]
                analysis["elements"].append({"id": key[9:],
                                                "amount": e[0],
                                                "precision": e[1],
                                                "precision_type": e[2],
                                                "measurement_unit": e[3],
                                                "min_amount": e[4], "max_amount": e[5]})
                del analysis[key]
            elif key[:7] == "oxides_":
                o = analysis[key]
                analysis["oxides"].append({"id": key[7:],
                                                "amount": o[0],
                                                "precision": o[1],
                                                "precision_type": o[2],
                                                "measurement_unit": o[3],
                                                "min_amount": o[4], "max_amount": o[5]})
                del analysis[key]
            elif key[-1] != "s" and analysis[key]:
                analysis[key] = analysis[key][0]

        if analysis["total"] == '':
            del analysis["total"]
        # if analysis["stage_x"] == '':
        #     del analysis["stage_x"]
        # if analysis["stage_y"] == '':
        #     del analysis["stage_y"]
        # if analysis["reference_x"] == '':
        #     del analysis["reference_x"]
        # if analysis["reference_y"] == '':
        #     del analysis["reference_y"]

        print "analysis: ",analysis

        if new:
            analysis["subsample_id"] = request.args.get("subsample_id")
            response = post(env("API_HOST")+"chemical_analyses/", json = analysis, headers = headers)
        else:
            response = put(env("API_HOST")+"chemical_analyses/"+id+"/", json = analysis, headers = headers)
        if response.status_code < 300:
            return redirect(url_for("chemical_analysis", id = response.json()["id"]))
        errors = response.json()
        print errors

    if new:
        subsample = get(env("API_HOST")+"subsamples/"+subsample_id+"/", params = {"fields": "id,name,owner,sample"},headers = headers).json()
        subsample["sample"] = subsample["sample"]["id"]
        analysis = {"owner": subsample["owner"], "sample": subsample["sample"], "subsample": subsample}
    else:
        #again, still have to get sample number
        analysis = get(env("API_HOST")+"chemical_analyses/"+id+"/", params = {"format": "json"}, headers = headers).json()

    minerals = get(env("API_HOST")+"minerals/", params = {"page_size": 200, "format": "json"}).json()["results"]
    elements = get(env("API_HOST")+"elements/", params = {"page_size": 50, "format": "json"}).json()["results"]
    oxides = get(env("API_HOST")+"oxides/", params = {"page_size": 50, "format": "json"}).json()["results"]

    return render_template("edit_chemical_analysis.html",
        analysis = analysis,
        minerals = minerals,
        elements = elements,
        oxides = oxides,
        errors = errors,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/login", methods = ["GET", "POST"])
def login():
    #redirect to index if already logged in
    if session.get("auth_token", None):
        return redirect(url_for("index"))

    login = dict(request.form)
    if login:
        #get email/password/(other info if registering)
        for l in login.keys():
            if login[l]:
                login[l] = login[l][0]
            else:
                del login[l]
        register = (login["login"] == "Register")
        del login["login"]

        #try to login/register
        auth_token = {}
        if register:
            auth_token = post(env("API_HOST")+"auth/users/create/", data = login).json()
            flash("Activation email sent to: {}".format(login['email']))
        else:
            auth_token = post(env("API_HOST")+"auth/token/create/", data = login).json()

            if not auth_token or "auth_token" not in auth_token:
                flash((',').join(auth_token.values()[0]))
            else:
                flash("Login successful!")
                session["auth_token"] = auth_token["auth_token"]
                session["email"] = login["email"]
                session["id"] = auth_token["user_id"]
                session["name"] = get(env("API_HOST")+"users/"+session["id"],
                    params = {"fields": "name"}, headers = {"Authorization": "Token "+session["auth_token"]}).json()["name"]

                return redirect(url_for("index"))

    return render_template("login.html",
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/logout")
def logout():
    #just pop the data from the session
    del session['auth_token']
    del session["email"]
    del session["name"]
    del session["id"]
    flash("Logout successful.")
    return redirect(url_for("index"))

@metpet_ui.route("/activate", methods = ["POST"])
def activate_account():
    # send request for account activation
    form = dict(request.form)
    # try to activate the account
    response = post(env("API_HOST") + "auth/users/activate/", data=form)
    success =(response.status_code == 200)
    return jsonify({'success' : success})

@metpet_ui.route("/request-password-reset", methods = ["GET", "POST"])
def request_password_reset():
    #get data from form
    form = dict(request.form)
    if form:
        #get email data
        response = post(env("API_HOST")+"auth/password/reset/", data = form)
        if response.status_code != 204:
            flash("Invalid email. Please try again.")
        else:
            flash("Please check your email for a link to reset your password")
            return redirect(url_for("login"))

    return render_template("request_password_reset.html",
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/reset-password", methods = ["GET", "POST"])
def reset_password():
    #get password data
    form = dict(request.form)
    print form
    password = request.form.get("new_password",None)
    if password:
        #send new password to API
        response = post(env("API_HOST")+"auth/password/reset/confirm/", data = form)
        if response.status_code != 204:
            flash("Password reset failed. Please try again.")
            return redirect(url_for("request_password_reset"))
        else:
            flash("Password reset successful!")
            return redirect(url_for("login"))

    return render_template("reset_password.html",
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )


@metpet_ui.route("/user")
def user():
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("index"))

    user = get(env("API_HOST")+"users/"+session.get("id"), params = {"format": "json"}, headers = headers).json()
    if "detail" in user:
        flash(user['detail'])
        return redirect(url_for("index"))
    return render_template("user.html",
        user = user,
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )

#Handle the bulk upload URL
@metpet_ui.route("/bulk-upload")
def bulk_upload():
    return render_template('bulk_upload.html',
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None),
        owner = session.get("owner",None)
    )


@metpet_ui.route("/test", methods=['POST'])

def test():
    #Capture bulk upload details inputted by user (url, filetype) formatted as
    #JSON that was sent from JavaScript
    #auth_token = session.get("auth_token",None),
    UserInput = request.json
    response = None
    print "Type received from user input: ", type(UserInput)
    if (UserInput != None):
        UserInput = dict([(str(k), str(v)) for k, v in UserInput.items()])
        headers = None
        # if session.get("auth_token", None):
        print "User auth_token:",session.get("auth_token")
        print "User id:",session.get("user_id")
        print "UserInput:",UserInput
        headers = {"Authorization": "Token "+session.get("auth_token")}
        UserInput["owner"]=session.get("id")

        
        # print response.json()

        # print "Owner:",UserInput["owner"]

        # else:
            # pass
            # return render_template('index.html')
        response = post(env("API_HOST")+"bulk_upload/", json = UserInput, headers = headers)
        # response_dict = dict(response.json()[0])
        # new_response = dict()
        # for key in response_dict:
        #     # new_key = key.replace('_', " ")
        #     new_key = key
        #     new_response[new_key] = response_dict[key] 
        #     print key, new_key, len(new_response)
        # # print "new response:", new_response
        # json_response = jsonify(new_response)
        print response
        # print "Keys:", new_response.keys()
        print "Response status code:",response.status_code
        print "Response:",response
        print "Response content (json):",response.json()
    '''
    return render_template('bulk_upload_results.html',
        bulk_upload_output = response.json(),
        auth_token = session.get("auth_token",None),
        email = session.get("email",None),
        name = session.get("name",None)
    )
    '''
    return jsonify(results=response.json())

if __name__ == "__main__":
    dotenv.read_dotenv("../app_variables.env")
    metpet_ui.run(debug = True)