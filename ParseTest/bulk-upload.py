###############################################################
# Author: Brandon Drumheller                                  #
# A generic basis for a bulk file uploader for MetPetDB       #
###############################################################

import upload_templates
import json
import sys
import urllib
from csv import reader

class Parser:
    def __init__(self, template):
        self.template = template #create new template object here
    
    def line_split(self, content):
        data = content.split('\r\n')[:-1]
        if len(data) < 2: data = content.split('\n')[:-1]
        if len(data) < 2: print 'ERROR: no data entries'; exit(1)    
        lined = [] # line separated data
        for entry in reader(data): lined.append(entry)
        return lined

    # Effects: Generates JSON file from passed template
    def parse(self, url):   
        #try to open the file
        try:
            url = url[:-1] +'1'
            content = urllib.urlopen(url).read()
        except:
            print 'ERROR: Unable to open file {0} for reading.'.format(url)
            exit(1)
        
        lined = self.line_split(content)
        return  self.template.parse(lined) # return the JSON ready file
    
##############################################################
# Effects: writes json formatted JSON to output_file_name    #
#          out.JSON if no file is specified                  #
##############################################################
def write_JSON(JSON, output_file_name='out.JSON'):
    json_data = json.dumps(JSON)
    try: 
        output_file = open(output_file_name, 'w+')
        output_file.write(json_data)
        output_file.close()
    except:
        print "ERROR: unable to write JSON to file {0}".format(output_file_name)

#####################################################
# Effects: Exits the program if the command         #
#          Line arguments are improperly formatted  #
#####################################################

def check_args():
    if len(sys.argv) != 3:
        print "ERROR: USAGE <dropbox_url> <template_name>"
        exit(1)

def main():
    check_args()
    input_file_name = sys.argv[1]
    template_name = sys.argv[2]
    template_instance = ''

    #Dynamically generate instance of template
    try: 
        module = __import__('upload_templates')
        class_ = getattr(module, template_name)
        template_instance = class_()
    except:
        print 'ERROR: Invalid template {0}'.format(template_name)
        exit(1)
         
    p = Parser(template_instance) 
    JSON = p.parse(input_file_name)
    write_JSON(JSON)

if __name__ == '__main__':
    main()
