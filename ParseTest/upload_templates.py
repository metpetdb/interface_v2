"""
Templates for Uploading Files to MetPetDB

ChemicalAnalysesTemplate and SampleTemplate extend Template     
and initialize their own of the following types:
    
    Complex: types to be stored in a list  [<field>]
        e.g. comments
    
    Required: these fields must be in each entry [<field>]
        e.g. sample_number
    
    DB_Types: fields related to other db_objects [<field>]  
        e.g. subsample related through subsample_id

    Types: mapping of fields to expected types  {<field>: <expected_type>} 
        e.g. {"analyst": str}

Additionally, SampleTemplate has an additional type:
    
    Selected {<field>: []}: fields that should only be included if checked 

All other fields are assumed to be simple, i.e. directly mapped
    e.g. where_done = "Rensselaer Polytechnic Institute"

"""
import copy

class Template:
    def __init__(self, c_types = [], required = [], db_types = []): 
        self.complex_types = c_types
        self.required = required 
        self.db_types = db_types
        self.data = ''

    ################################################################
    # Check that the file is not empty                             #
    # Check that the length of each line is the same as the header #
    ################################################################
    def check_line_len(self):
        data = self.data
        if(len(data) == 0): 
            print "ERROR: empty file"
            exit(1)

        for i in range(1,len(data)):
            #print data
            if (len(data[i]) != len(data[i-1])):             
                print "prev: " + str(len(data[i-1]))
                print "curr: " + str(len(data[i]))
                print "ERROR: inconsistent line length"
                exit(1)

    #######################################################
    # Print an error and exit the program if required     #
    # fields are missing from the data                    #
    #######################################################
    def check_required(self):
        data = self.data
        header = data[0]
        for i in range(0, len(header)):
            if self.is_required(header[i]):
                for j in range(0, len(data)):
                    if data[j][i] == '':
                        print "Missing required field: {0} on line {1}".format(header[i], j+1)
                        exit(1)

    def check_type(self):
        pass
    
    class TemplateResult:
        def __init__(self, r_template): 
            self.rep = r_template

        def set_field_simple(self, field, value): 
            self.rep[field] = value
        
        def set_field_complex(self, field, value):
            self.rep[field].append(value)

        def get_rep(self): return self.rep

    def check_data(self):
        self.check_line_len()
        self.check_required()
        self.check_type()

    def parse(self, data):
        self.data = data
        self.check_data()
     
        header = data[0]
        result = []
        
        result_template = {}
        for heading in header:
            if self.is_complex(heading): result_template[heading] = []
            else: result_template[heading] = ''
                
        for i in range(1, len(data)):
            tmp_result = self.TemplateResult(copy.deepcopy(result_template))
            for j in range(0,len(data[i])):
                heading = header[j]
                field = data[i][j]
                if self.is_complex(heading): 
                    tmp_result.set_field_complex(heading,field)  
                else: tmp_result.set_field_simple(heading, field)
            result.append(tmp_result.get_rep())    
        return result

    def is_complex(self, name): return name in self.complex_types
    def is_required(self, name): return name in self.required
    def is_db_type(self, name): return name in self.db_types

class ChemicalAnalysesTemplate(Template):
    def __init__(self):
        complex_types = ["comment", "elements", "oxides"]
        required = ["subsample_id", "spot_id", "mineral_id", "analysis_method"]
        db_types = ["elements", "oxides"]
        types = {"comment": str, "stage_x" : float, "stage_y" : float} #TODO finish these, ask about this
        Template.__init__(self, complex_types, required, db_types) 

class SampleTemplate(Template):
    def __init__(self):
        complex_types = ["comment", "references", "minerals"]
        required = ["number", "location_coords", "rock_type_id"]
        types = {"comment": str} #TODO finish these, ask about this
        db_types = ["minerals"] 
        selected_types = {'minerals': ['el1', 'el2', 'el3']} 
        Template.__init__(self, complex_types, required, db_types)
