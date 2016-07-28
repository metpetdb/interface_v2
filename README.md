<a name="logo"/>
<div align="center">
<a href="http://metpetdb.rpi.edu/" target="_blank">
<img src="http://metpetdb.rpi.edu/metpetweb/images/mpdb-logo.gif" alt="mpdb Logo" width="201" height="148"></img>
</a>
</div>

##MetPetDB-interface

Front-end application for the Meptetb system built using Flask.
(metpetdb.rpi.edu)

The API is built in Django and can be found here: https://github.com/metpetdb/api_v2

We will now set up the system and virtual environment for a new/clean meachine, which means `/usr/lib/python2.7/site-packages` is not modified globally for any application. Let's start from installing global applications to virtual environment.

**Before setting up everything:**

	$ sudo apt-get update
	$ sudo apt-get upgrade -y

**Note: This setup instruction is tested on ubuntu 14.04. If you are using different release of Linux, pre-installed dependencies may vary according to your OS**
	
Apache Web Server Installation
------------------------------

####Install Apache
    $ sudo apt-get install apache2 -y
    $ sudo apt-get install apache2-threaded-dev python2.7-dev -y
	
####Install mod_wsgi

Now we install mod_wsgi by typing the following command

	$ sudo apt-get install libapache2-mod-wsgi python-dev

To enable mod_wsgi, run the following command:

	$ sudo a2enmod wsgi 
	
Restart Apache to get mod_wsgi to work.

	$ sudo service apache2 restart


## Python and Virtualenvwrapper setup

Virtualenv is probably what you want to use during development.
What problem does virtualenv solve? If you want to use Python for other projects besides Flask-based web applications. it is very likely that you will be working with different versions of Python itself, or different versions of Python libraries. Quite often, libraries break backwards compatibility, and it’s unlikely that any serious application will have zero dependencies. So we create virtual environment to keep different project environments isolated if two or more of your projects have conflicting dependencies.

**Python comes with the ubuntu 14.04, so there is no need to install python if you are using the latest ubuntu.**

If Python 2.7 is not installed, install it

`$ sudo apt-get install python2.7`
	
Install some required packages

	$ sudo apt-get install python-dev libpq-dev libxml2-dev -y
	$ sudo apt-get install  libproj-dev libgeos-dev libgdal-dev -y
	$ wget -c https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py

Install virtualenv:

	$ sudo pip install virtualenvwrapper
	
Check if virtualenvwrapper.sh and virtualenvwrapper_lazy.sh exist:

	$ which virtualenvwrapper.sh
	/usr/local/bin/virtualenvwrapper.sh
	
	$ which virtualenvwrapper_lazy.sh
	/usr/local/bin/virtualenvwrapper_lazy.sh
	
After this, we create a directory for the virtual evcironments:

	$ mkdir ~/.virtualenvs
	
Then, add the folowing lines to ~/.bashrc:

	$ sudo nano ~/.bashrc
	
	# add these two lines at the end of the ~/.bashrc
	export WORKON_HOME=$HOME/.virtualenvs
	source /usr/local/bin/virtualenvwrapper_lazy.sh
	
	$ source ~/.bashrc
	
####Starting a New Virtual Environment

Virtualenvwrapper provides some nice commands we can use to play around with the environments.

To create a new virtual environment:

	$ mkvirtualenv metpetdb
	New python executable in metpetdb/bin/python
	Installing setuptools, pip...done.
	
As you might notice, the command prompt contains the name before you username
	
	**(metpetdb)**user@xxxx:~$ python --version
	Python 2.7.6

To deactivate and exit the virtual environment, just do

	$ deactivate
	
Tht next time you come back, start you environment by doing:

	$ workon environment_name

Other usage command:
- Remove your current environment: `rmvirtualenv environment_name`
- show a list of environments: `workon`

## Setting up MetpetDB interface

If you have created a virtual environment for MetpetDB interface and you have not yet fooled around with its setting and packages, start the virtual environment: `workon environment_name` 

If you are not sure, create a new clean virtual environment:
	
	# Deleting the previous virtual env is optional
	# $ rmvirtualenv environment_name #(env name was "metpetdb" if you strictly follow the instruction)
	
	$ mkvirtualenv metpetdb
	$ workon metpetdb
	
Create a directory for the project:

	$ mkdir metpetdb
	$ cd metpetdb
	
Under metpetdb directory, where we place our secret "app_variables.env" file that points to the API server.

	$ sudo nano app_variables.env
	
	# copy and paste the following keys into "app_variables.env"
	--------------------------------------------------------
	API_HOST=<api-host-location> (e.g http://54.164.222.32)
	SECRET_KEY=qqqqqqqqqqjjhuk8jl9l99l9l;;0o0o;0'0'
	--------------------------------------------------------
	
Then we clone the interface code from github, just do:
	
	$ sudo apt-get install git -y && git clone https://github.com/metpetdb/interface_v2.git
	
Alright, we are so close to finishing setting up MetpetDB locally. Next, install required dependentcies for the interface.
		
	$ cd metpetdb_interface
	$ pip install -r requirements_new_ubuntu_14.04.txt

If you get an error when accessing edit/add sample/subsample/chemical analysis, install the latest version of requests:

	$ pip install requests
	
Finally, run app.py to test if we have set up the interface properly:

	$ python app.py

Visit `http://127.0.0.1:5000/` or `localhost:5000/` to view the project.
	
## Configuring Apache to Serve the Application
We are still in the virtual env, deactivate and exit the virtual environment first by do `deactivate`

**Configure and Enable default or a New Virtual Host**
	
Open the .conf file of your virtual host, in here, we directly modify the default virtual host's .conf. 

	$ sudo nano /etc/apache2/sites-available/000-default.conf

Add the following lines of code to the file to configure the virtual host. Be sure to change the ServerName to your domain or cloud server's IP address:
	
	<VirtualHost *:80>
        #ServerName metpetdb.rpi.edu    #optional
        ServerAdmin webmaster@localhost #change this

        WSGIScriptAlias / /home/ubuntu/metpetdb/metpetdb.wsgi

        <Directory /home/ubuntu/metpetdb/>
                Require all granted
        </Directory>

        ErrorLog ${APACHE_LOG_DIR}/error.log
        LogLevel warn
        CustomLog ${APACHE_LOG_DIR}/access.log combined

	</VirtualHost>

Save and close the file.

####Create the .wsgi File

Make sure you are at `~/metpetdb`. We need to create the .wsgi script file for Apace to uses to serve the Flask app.
	
	$ deactivate
	$ cd ~/metpetdb/
	$ sudo nano metpetdb.wsgi
	
Modify and add the following lines of conde to the metpetdb.wsgi according to you system setup

	activate_this = '/home/ubuntu/.virtualenvs/metpetdb/bin/activate_this.py'
	execfile(activate_this, dict(__file__=activate_this))
	
	import sys
	import logging
	logging.basicConfig(stream=sys.stderr)
	sys.path.insert(0,"/home/ubuntu/metpetdb/")
	sys.path.insert(0,"/home/ubuntu/metpetdb/interface_v2")
	sys.path.insert(0,"/home/ubuntu/.virtualenvs/metpetdb/lib/python2.7/site-packages")

	from metpetdb_interface import metpet_ui as application

Next rename app.py
    
    $ cd interface_v2/
    $ mv app.py __init__.py

Now your directory structure should look like this:

	|--------metpetdb
	|----------------interface_v2
	|-----------------------static
	|-----------------------templates
	|-----------------------__init__.py
	|-----------------------forms.py
	|-----------------------*.py
	|----------------app_variables.env  
	|----------------metpetdb.wsgi

####Set Proper Permission

Run the following commands to set permission.
	
	$ sudo chmod -R o+rx ~/metpetdb
	$ sudo chmod -R o+rx ~/.virtualenvs/metpetdb
	
## Restart Apache
Restart Apache with the following command to apply the changes:

	$ sudo service apache2 restart 
	
	
## Redeployment 
This process should be followed to replace an outdated front-end

Stop the apache server
    
    $ sudo service apache2 stop

Remove the old front-end
    
    $ sudo rm -r interface_v2/  	
	
Clone the latest version
    
    git clone https://github.com/metpetdb/interface_v2.git

Next rename app.py
    
    $ cd interface_v2/
    $ mv app.py __init__.py

Your directory structure should look like this:

	|--------metpetdb
	|----------------interface_v2
	|-----------------------static
	|-----------------------templates
	|-----------------------__init__.py
	|-----------------------forms.py
	|-----------------------*.py
	|----------------app_variables.env  
	|----------------metpetdb.wsgi

Restart the apache server
   
   $ sudo service apache2 start
	



## Changelog

- 0.1 Core Functionality

- 0.2 [7/24/2016] Bulk Upload Added
	
	
	
	
	
	
