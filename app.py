import dotenv
import json
from getenv import env
from requests import get, put, post, codes
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
from utilities import paginate_model

mail = Mail()
metpet_ui = Flask(__name__)
metpet_ui.config.from_object("config")
mail.init_app(metpet_ui)


@metpet_ui.route("/")
def index():
    return render_template("index.html",
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/search/")
def search():
    #filters sent as parameters to API calls
    filters = {}
    for key in dict(request.args):
        if dict(request.args)[key][0] and key != "resource":
            filters[key] = (",").join(dict(request.args)[key])

    if request.args.get("resource") == "sample":
        #resource value set in search_form.html
        #appends samples.html to bottom of page
        return redirect(url_for("samples")+"?"+urlencode(filters))

    if request.args.get("resource") == "chemicalanalysis":
        #minerals_and option not valid parameter for analyses
        #sets sample_filters b/c search samples only has sample filters
        #appends chemical_analyses.html to bottom of page
        if "minerals_and" in filters:
            del filters["minerals_and"]
        filters["sample_filters"] = True
        return redirect(url_for("chemical_analyses")+"?"+urlencode(filters))

    #get all filter options from API
    #use format=json and minimum page sizes to speed it up
    regions = get(env("API_DRF_HOST")+"/regions/", params={"fields": "name", "page_size": 2000, "format": "json"}).json()["results"]
    minerals = get(env("API_DRF_HOST")+"/minerals/", params={"fields": "name", "page_size": 200, "format": "json"}).json()["results"]
    rock_types = get(env("API_DRF_HOST")+"/rock_types/", params={"fields": "name", "page_size": 40, "format": "json"}).json()["results"]
    collectors = get(env("API_DRF_HOST")+"/collectors/", params={"fields": "name", "page_size": 140, "format": "json"}).json()["results"]
    references = get(env("API_DRF_HOST")+"/references/", params={"fields": "name", "page_size": 1100, "format": "json"}).json()["results"]
    metamorphic_grades = get(env("API_DRF_HOST")+"/metamorphic_grades/", params={"fields": "name", "page_size": 30, "format": "json"}).json()["results"]
    metamorphic_regions = get(env("API_DRF_HOST")+"/metamorphic_regions/", params={"fields": "name", "page_size": 240, "format": "json"}).json()["results"]

    #get countries and sample numbers
    #endpoints for these should be deployed soon so it's not so slow
    samples = get(env("API_DRF_HOST")+"/samples/",
        params={"fields": "country", "public_data": True, "page_size": 1000, "format": "json"}).json()["results"]
    countries = set()
    for sample in samples:
        countries.add(sample["country"])

    api_samples = get(env("API_DRF_HOST")+"/samples/", params={"fields": "number", "page_size": 2000, "format": "json"}).json()
    numbers = api_samples["results"]
    while api_samples["next"]:
        api_samples = json.loads(urlopen(api_samples["next"]).read())
        numbers += api_samples["results"]

    return render_template("search_form.html",
        countries=countries,
        metamorphic_grades=metamorphic_grades,
        metamorphic_regions=metamorphic_regions,
        minerals=minerals,
        numbers=numbers,
        collectors=collectors,
        references=references,
        regions=regions,
        rock_types=rock_types,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/search-chemistry/")
def search_chemistry():
    #basically the same as search samples but with analysis filter options
    filters = {}
    for key in dict(request.args):
        if dict(request.args)[key][0] and key != "resource":
            filters[key] = (",").join(dict(request.args)[key])

    if request.args.get("resource") == "chemicalanalysis":
        return redirect(url_for("chemical_analyses")+"?"+urlencode(filters))

    if request.args.get("resource") == "sample":
        filters["chemical_analyses_filters"] = True
        return redirect(url_for("samples")+"?"+urlencode(filters))

    oxides = get(env("API_DRF_HOST")+"/oxides/", params={"fields": "species", "page_size": 100, "format": "json"}).json()["results"]
    elements = get(env("API_DRF_HOST")+"/elements/", params={"fields": "name,symbol", "page_size": 120, "format": "json"}).json()["results"]
    minerals = get(env("API_DRF_HOST")+"/minerals/", params={"fields": "name", "page_size": 200, "format": "json"}).json()["results"]

    return render_template("chemical_search_form.html",
        elements=elements,
        oxides=oxides,
        minerals=minerals,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/samples/")
def samples():
    #set filters to dict of input arguments (likely from search filters)
    #only return public data samples if not logged in
    filters = dict(request.args)
    filters["format"] = "json"
    if not session.get("auth_token", None):
        filters['public_data'] = ['True']

    #get sample data and use meta data to get pagination urls
    samples = get(env("API_DRF_HOST")+"/samples/", params=filters).json()
    sample_results = samples["results"]
    next, previous, last, total_count = paginate_model("samples", samples, filters)

    #split location into (rounded!) latitude and longitude
    #make string of minerals for ... look and clean up date
    for s in sample_results:
        pos = s["location_coords"].split(" ")
        s["location_coords"] = [round(float(pos[2].replace(")","")),5),round(float(pos[1].replace("(","")),5)]
        s["minerals"] = (", ").join([m["name"] for m in s["minerals"]])
        if s["collection_date"]:
            s["collection_date"] = s["collection_date"][:-10]

    return render_template("samples.html",
        samples=sample_results,
        showmap="showmap" in filters,
        next_url=next,
        prev_url=previous,
        total=total_count,
        first_page=url_for("samples")+"?"+urlencode(filters),
        last_page=last,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/sample/<string:id>")
def sample(id):
    #headers! to authenticate user during API calls (for private data and to add/edit their samples)
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}

    #get the sample the usual way and return error message if something went wrong
    sample = get(env("API_DRF_HOST")+"/samples/"+id, params={"format": "json"}, headers=headers).json()
    if "detail" in sample:
        flash(sample["detail"])
        return redirect(url_for("search"))

    #make lat/long and date nice
    pos = sample["location_coords"].split(" ")
    sample["location_coords"] = [round(float(pos[2].replace(")","")),5), round(float(pos[1].replace("(","")),5)]
    if sample["collection_date"]:
        sample["collection_date"] = sample["collection_date"][:-10]

    #get subsample and analysis data for tables
    subsamples = []
    for s in sample["subsample_ids"]:
        subsamples.append(get(env("API_DRF_HOST")+"/subsamples/"+s,
            params={"fields": "subsample_type,name,id,public_data,owner", "format": "json"}, headers=headers).json())
    for s in subsamples:
        s["chemical_analyses"] = get(env("API_DRF_HOST")+"/chemical_analyses/",
            params={"subsample_ids": s["id"], "fields": "id", "format": "json"}, headers=headers).json()["results"]

    return render_template("sample.html",
        sample=sample,
        subsamples=subsamples,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/edit-sample/<string:id>", methods=["GET", "POST"])
def edit_sample(id):
    #this time redirect to sample page if not logged in
    headers = None
    if session.get("auth_token", None):
        print session.get("auth_token")
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("sample", id=id))

    #edit_sample.html is a form with mostly the right input names
    new_sample = dict(request.form)
    if new_sample:
        #minerals are named by id, make it into a nested list of dictionaries
        new_sample["minerals"] = []
        for key in new_sample.keys():
            if key[:9] == "minerals_":
                new_sample["minerals"].append({"id": key[9:], "amount": new_sample[key][0]})
                del new_sample[key]
            elif (not new_sample[key] or not new_sample[key][0]) and key != "minerals":
                del new_sample[key]
            elif key[-1] != "s":
                new_sample[key] = new_sample[key][0]

        #make lat/long back into point
        new_sample["location_coords"] = "SRID=4326;POINT ("+str(new_sample["location_coords1"])+" "+str(new_sample["location_coords0"])+")"
        del new_sample["location_coords0"]
        del new_sample["location_coords1"]

        #send data to API with PUT call and return error message if any
        new_sample['owner'] = '3144472b-42af-4fbb-94e2-19d2443d07dc'
        print json.dumps(new_sample)
        new_sample = put(env("API_DRF_HOST")+"/samples/"+id, data=json.dumps(new_sample), headers=headers)
        print new_sample.json()
        if new_sample.status_code != codes.ok:
            flash(new_sample.json().values()[0][0])
        return redirect(url_for("sample", id=id))

    #get sample data and make lat/long separate
    sample = get(env("API_DRF_HOST")+"/samples/"+id, params={"format": "json"}, headers=headers).json()
    pos = sample["location_coords"].split(" ")
    sample["location_coords"] = [float(pos[2].replace(")","")), float(pos[1].replace("(",""))]

    #get all the other data
    regions = get(env("API_DRF_HOST")+"/regions/", params={"page_size": 2000, "format": "json"}).json()["results"]
    minerals = get(env("API_DRF_HOST")+"/minerals/", params={"page_size": 200, "format": "json"}).json()["results"]
    rock_types = get(env("API_DRF_HOST")+"/rock_types/", params={"page_size": 40, "format": "json"}).json()["results"]
    references = get(env("API_DRF_HOST")+"/references/", params={"page_size": 1100, "format": "json"}).json()["results"]
    metamorphic_grades = get(env("API_DRF_HOST")+"/metamorphic_grades/", params={"page_size": 30, "format": "json"}).json()["results"]
    metamorphic_regions = get(env("API_DRF_HOST")+"/metamorphic_regions/", params={"page_size": 240, "format": "json"}).json()["results"]

    return render_template("edit_sample.html",
        sample=sample,
        regions=regions,
        minerals=minerals,
        rock_types=rock_types,
        references=references,
        metamorphic_grades=metamorphic_grades,
        metamorphic_regions=metamorphic_regions,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/new-sample/", methods=["GET", "POST"])
def new_sample():
    #basically the same as edit sample
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("search"))

    new_sample = dict(request.form)
    if new_sample:
        new_sample["minerals"] = []
        for key in new_sample.keys():
            if key[:9] == "minerals_":
                new_sample["minerals"].append({"id": key[9:], "amount": new_sample[key][0]})
                del new_sample[key]
            elif (not new_sample[key] or not new_sample[key][0]) and key != "minerals":
                del new_sample[key]
            elif key[-1] != "s":
                new_sample[key] = new_sample[key][0]
        if not new_sample['minerals']:
            del new_sample['minerals']

        new_sample["location_coords"] = "SRID=4326;POINT ("+str(new_sample["location_coords1"])+" "+str(new_sample["location_coords0"])+")"
        del new_sample["location_coords0"]
        del new_sample["location_coords1"]

        new_sample['owner'] = '3144472b-42af-4fbb-94e2-19d2443d07dc'
        new_sample = {
            "minerals": [
                {
                    "id": "0010184b-28aa-4816-89c0-5137773883d8",
                    "amount": "x"
                },
                {
                    "id": "feb8da1f-c2d1-4af8-b675-9b2fd62ba9c2",
                    "amount": "y"
                }
            ],
            "owner": "930dfb18-433f-4a9c-be02-0475d42b4d3f",
            "public_data": True,
            "number": "GF-63:2007-110722",
            "aliases": [
                "Mysample1",
                "Mysample2"
            ],
            "collection_date": None,
            "description": "Creating a sample",
            "location_name": "Montreal",
            "location_coords": "SRID=4326;POINT (-118.4008865356450002 49.1695137023925994)",
            "location_error": None,
            "date_precision": None,
            "country": "Canada",
            "regions": [
                "British Columbia",
                "Shuswap",
                "Footwall of Granby Fault",
                "The Grand Forks Complex"
            ],
            "references": [
                "2007-110722"
            ],
            "collector_name": None,
            "sesar_number": None,
            "rock_type_id": "0d4504cf-f965-4eb7-8a2a-31272825bb54",
            "collector_id": None,
            "metamorphic_region_ids": [
                "e43059ba-d33f-41d6-a226-b58c5ef93ada",
                "002cdc09-5e33-421b-be7d-89f400da438a"
            ],
            "metamorphic_grade_ids": [
                "0e4e0c52-169d-49a9-8e5c-657b9f6c84c8"
            ]
        }
        print new_sample
        new_sample = post(env("API_DRF_HOST")+"/samples/", data=new_sample, headers=headers)
        print new_sample.json()
        if new_sample.status_code != codes.ok:
            flash(new_sample.json().values()[0][0])
        return redirect(url_for("search"))

    regions = get(env("API_DRF_HOST")+"/regions/", params={"page_size": 2000, "format": "json"}).json()["results"]
    minerals = get(env("API_DRF_HOST")+"/minerals/", params={"page_size": 200, "format": "json"}).json()["results"]
    rock_types = get(env("API_DRF_HOST")+"/rock_types/", params={"page_size": 40, "format": "json"}).json()["results"]
    references = get(env("API_DRF_HOST")+"/references/", params={"page_size": 1100, "format": "json"}).json()["results"]
    metamorphic_grades = get(env("API_DRF_HOST")+"/metamorphic_grades/", params={"page_size": 30, "format": "json"}).json()["results"]
    metamorphic_regions = get(env("API_DRF_HOST")+"/metamorphic_regions/", params={"page_size": 240, "format": "json"}).json()["results"]

    #get user data
    owner = get(env("API_DRF_HOST")+"/users/", params={"fields": "name"}, headers=headers).json()["results"]
    if len(owner) > 1:
        owner = None
    else:
        owner = owner[0]

    return render_template("edit_sample.html",
        sample=sample,
        regions=regions,
        minerals=minerals,
        rock_types=rock_types,
        references=references,
        metamorphic_grades=metamorphic_grades,
        metamorphic_regions=metamorphic_regions,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/subsample/<string:id>")
def subsample(id):
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}

    #get subsample info
    subsample = get(env("API_DRF_HOST")+"/subsamples/"+id, params={"format": "json"}, headers=headers).json()
    if "detail" in subsample:
        flash(subsample['detail'])
        return redirect(url_for("search"))

    #get sample and analysis info
    subsample["sample"]["number"] = get(env("API_DRF_HOST")+"/samples/"+subsample["sample"]["id"],
        params={"fields": "number", "format": "json"}, headers=headers).json()["number"]
    chemical_analyses = get(env("API_DRF_HOST")+"/chemical_analyses/", params={"subsample_ids": subsample["id"], "format": "json"}).json()["results"]

    return render_template("subsample.html",
        subsample=subsample,
        chemical_analyses=chemical_analyses,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/edit-subsample/<string:id>", methods=["GET", "POST"])
def edit_subsample(id):
    #similar to but much simpler than edit sample
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("subsample", id=id))

    if dict(request.form):
        new_subsample = put(env("API_DRF_HOST")+"/subsamples/"+id, data=dict(request.form), headers=headers).json()
        if 'detail' in new_subsample:
            flash(new_subsample['detail'])
        return redirect(url_for("subsample", id=id))

    subsample = get(env("API_DRF_HOST")+"/subsamples/"+id, params={"format": "json"}, headers=headers).json()
    subsample["owner"] = get(env("API_DRF_HOST")+"/users/"+subsample["owner"]["id"], params={"format": "json"}, headers=headers).json()
    types = [subsample["subsample_type"]]#api type request

    return render_template("edit_subsample.html",
        subsample=subsample,
        types=types,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/new-subsample/", methods=["GET", "POST"])
def new_subsample():
    #basically the same as edit subsample
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("search"))

    if dict(request.form):
        new_subsample = post(env("API_DRF_HOST")+"/subsamples/", data=dict(request.form), headers=headers).json()
        if 'detail' in new_subsample:
            flash(new_subsample['detail'])
        return redirect(url_for("subsample", id=new_subsample["id"]))

    #theoretically there'll be an endpoint for subsample types
    types = []

    owner = get(env("API_DRF_HOST")+"/users/", params={"fields": "name"}, headers=headers).json()["results"]
    if len(owner) > 1:
        owner = None
    else:
        owner = owner[0]

    return render_template("edit_subsample.html",
        subsample={"owner": owner, "sample": {}},
        types=types,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/chemical-analyses/")
def chemical_analyses():
    #similar to samples
    filters = dict(request.args)
    filters["format"] = "json"

    chemicals = get(env("API_DRF_HOST")+"/chemical_analyses/", params=filters).json()
    chem_results = chemicals["results"]
    next, previous, last, total_count = paginate_model("chemical_analyses", chemicals, filters)

    #hopefully analyses will have sample numbers instead of just ids to skip this step
    for c in chem_results:
        c["sample"] = get(env("API_DRF_HOST")+"/samples/"+c["subsample"]["sample"],
            params={"fields": "number", "format": "json"}, headers={"Authorization": "Token "+session.get("auth_token", '')}).json()
        if c["analysis_date"]:
            c["analysis_date"] = c["analysis_date"][:-10]

    return render_template("chemical_analyses.html",
        chemical_analyses=chem_results,
        next_url=next,
        prev_url=previous,
        total=total_count,
        first_page=url_for("chemical_analyses")+"?"+urlencode(filters),
        last_page=last,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/chemical-analysis/<string:id>")
def chemical_analysis(id):
    #similar to sample and subsample
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}

    analysis = get(env("API_DRF_HOST")+"/chemical_analyses/"+id, params={"format": "json"}, headers=headers).json()
    if "detail" in analysis:
        flash(analysis['detail'])
        return redirect(url_for("search_chemistry"))

    #have to get sample number still
    analysis["sample"] = get(env("API_DRF_HOST")+"/samples/"+analysis["subsample"]["sample"],
        params={"fields": "number", "format": "json"}, headers=headers).json()

    return render_template("chemical_analysis.html",
        analysis=analysis,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/edit-chemical-analysis/<string:id>", methods=["GET", "POST"])
def edit_chemical_analysis(id):
    #again, similar to edit sample and edit subsample
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("chemical_analysis", id=id))

    if dict(request.form):
        new_analysis = dict(request.form)

        #this part is just like minerals from edit sample
        new_analysis["elements"] = []
        new_analysis["oxides"] = []
        for key in new_analysis.keys():
            if key[:9] == "elements_":
                e = new_analysis[key]
                new_analysis["elements"].append({"id": key[9:],
                                                "amount": e[0],
                                                "precision": e[1],
                                                "precision_type": e[2],
                                                "measurement_unit": e[3],
                                                "min": e[4], "max": e[5]})
                del new_analysis[key]
            if key[:7] == "oxides_":
                o = new_analysis[key]
                new_analysis["oxides"].append({"id": key[7:],
                                                "amount": o[0],
                                                "precision": o[1],
                                                "precision_type": o[2],
                                                "measurement_unit": o[3],
                                                "min": o[4], "max": o[5]})
                del new_analysis[key]

        new_analysis = put(env("API_DRF_HOST")+"/chemical_analyses/"+id, data=new_analysis, headers=headers).json()
        return redirect(url_for("chemical_analysis", id=id))

    #again, still have to get sample number
    analysis = get(env("API_DRF_HOST")+"/chemical_analyses/"+id, params={"format": "json"}, headers=headers).json()
    analysis["sample"] = get(env("API_DRF_HOST")+"/samples/"+analysis["subsample"]["sample"],
        params={"fields": "number", "format": "json"}, headers=headers).json()

    minerals = get(env("API_DRF_HOST")+"/minerals/", params={"page_size": 200, "format": "json"}).json()["results"]
    elements = get(env("API_DRF_HOST")+"/elements/", params={"page_size": 50, "format": "json"}).json()["results"]
    oxides = get(env("API_DRF_HOST")+"/oxides/", params={"page_size": 50, "format": "json"}).json()["results"]

    return render_template("edit_chemical_analysis.html",
        analysis=analysis,
        minerals=minerals,
        elements=elements,
        oxides=oxides,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/new-chemical-analysis/", methods=["GET", "POST"])
def new_chemical_analysis():
    #basically the same as edit analysis
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}
    else:
        return redirect(url_for("search_chemistry"))

    if dict(request.form):
        new_analysis = dict(request.form)

        new_analysis["elements"] = []
        new_analysis["oxides"] = []
        for key in new_analysis.keys():
            if key[:9] == "elements_":
                e = new_analysis[key]
                new_analysis["elements"].append({"id": key[9:],
                                                "amount": e[0],
                                                "precision": e[1],
                                                "precision_type": e[2],
                                                "measurement_unit": e[3],
                                                "min": e[4], "max": e[5]})
                del new_analysis[key]
            if key[:7] == "oxides_":
                o = new_analysis[key]
                new_analysis["oxides"].append({"id": key[7:],
                                                "amount": o[0],
                                                "precision": o[1],
                                                "precision_type": o[2],
                                                "measurement_unit": o[3],
                                                "min": o[4], "max": o[5]})
                del new_analysis[key]

        new_analysis = post(env("API_DRF_HOST")+"/chemical_analyses/"+id, data=new_analysis, headers=headers).json()
        return redirect(url_for("search_chemistry"))

    minerals = get(env("API_DRF_HOST")+"/minerals/", params={"page_size": 200, "format": "json"}).json()["results"]
    elements = get(env("API_DRF_HOST")+"/elements/", params={"page_size": 50, "format": "json"}).json()["results"]
    oxides = get(env("API_DRF_HOST")+"/oxides/", params={"page_size": 50, "format": "json"}).json()["results"]

    owner = get(env("API_DRF_HOST")+"/users/", params={"auth_token": session.get("auth_token", None)}, headers=headers).json()["results"]
    if len(owner) > 1:
        owner = None
    else:
        owner = owner[0]

    return render_template("edit_chemical_analysis.html",
        analysis={"owner": owner, "sample": "", "subsample": ""},
        minerals=minerals,
        elements=elements,
        oxides=oxides,
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/login", methods=["GET", "POST"])
def login():
    #redirect to index if already logged in
    if session.get("auth_token", None):
        return redirect(url_for("index"))

    login = dict(request.form)
    if login:
        #get email/password/(other info if registering)
        for l in login.keys():
            if not login[l]:
                del login[l]
        register = False
        if login["login"] == "Register":
            register = True
        del login["login"]

        #try to login/register
        auth_token = {}
        if register:
            #auth_token = post(env("API_DRF_HOST")+"/auth/register/", params=login).json()
            auth_token = {"detail": "hi"}
        else:
            auth_token = post(env("API_DRF_HOST")+"/auth/login/", data=login).json()

        if not auth_token or "auth_token" not in auth_token:
            flash(auth_token.values()[0][0])
        else:
            flash("Login successful!")
            session["auth_token"] = auth_token["auth_token"]
            return redirect(url_for("index"))

    return render_template("login.html",
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/logout")
def logout():
    #just pop the data from the session
    del session['auth_token']
    flash("Logout successful.")
    return redirect(url_for("index"))


@metpet_ui.route("/request-password-reset", methods=["GET", "POST"])
def request_password_reset():
    #get data from form
    form = dict(request.form)
    if form:
        #get email data
        email_data = post(env("API_DRF_HOST")+"/auth/password/reset/", data=form).json()
        if not email_data or "detail" in email_data:
            flash("Invalid email. Please try again.")
        else:
            #send email
            message = Message("Metpetdb: Reset Password", sender=env("DEFAULT_MAIL_SENDER"), recipients=[form["email"]])
            reset_url = url_for("reset_password", token=email_data["link"], _external=True)
            message.body = render_template("reset_password_email.html", reset_url=reset_url)
            mail.send(message)
            flash("Please check your email for a link to reset your password")
            return redirect(url_for("login"))

    return render_template("request_password_reset.html",
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/reset-password/<string:token>", methods=["GET", "POST"])
def reset_password(token):
    #get password data
    password = request.form.get("password",None)
    if password:
        #send new password to API
        reset_data = post(env("API_DRF_HOST")+"/auth/password/reset/confirm/", data={"token": token, "password": password}).json()
        if not reset_data or "detail" in reset_data:
            flash("Password reset failed. Please try again.")
            return redirect(url_for("request_password_reset"))
        else:
            session["auth_token"] = reset_data["auth_token"]
            flash("Password reset successful! You are now logged in.")
            return redirect(url_for("index"))

    return render_template("reset_password.html",
        auth_token=session.get("auth_token",None)
    )


@metpet_ui.route("/user/<string:id>")
def user(id):
    headers = None
    if session.get("auth_token", None):
        headers = {"Authorization": "Token "+session.get("auth_token")}

    #get user data, potentially add samples/analyses owned by user
    user = get(env("API_DRF_HOST")+"/users/"+id, params={"format": "json"}, headers=headers).json()
    if "detail" in user:
        flash(user['detail'])
        return redirect(url_for("index"))
    return render_template("user.html",
        user=user,
        auth_token=session.get("auth_token",None)
    )


if __name__ == "__main__":
    dotenv.read_dotenv("../app_variables.env")
    metpet_ui.run(debug=True)
