import urllib
import sys

def readURL(url):
    #replace the last character with a 1 for download
    #temporary hack
    url = url[:-1] +'1'
    try:
        f = urllib.urlopen(url).read()
        #pass this to the json creation stuff
        
    except e:
        print 'UNABLE TO OPEN FILE FOR READING'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "ERROR: USAGE <drop_box_url>" 
        exit(1)
    url = sys.argv[1];
    readURL(url)
