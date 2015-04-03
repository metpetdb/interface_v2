<a name="logo"/>
<div align="center">
<a href="http://metpetdb.rpi.edu/" target="_blank">
<img src="http://metpetdb.rpi.edu/metpetweb/images/mpdb-logo.gif" alt="mpdb Logo" width="201" height="148"></img>
</a>
</div>

##MetPetDB-interface

Front-end application for the Meptetb system built using Flask.
(metpetdb.rpi.edu)

The API is built in Django and can be found here: https://github.com/metpetdb/metpetdb-py

We will now set up the system and virtual environment for a new/clean meachine, which means `/usr/lib/python2.7/site-packages` is not modified globally for any application. Let's start from installing global applications to virtual environment.

**Before setting up everything:**

	$ sudo apt-get update
	$ sudo apt-get upgrade -y

**Note: This setup instruction is tested on ubuntu 14.04. If you are using different release of Linux, pre-installed dependencies may vary according to your OS**
	
Apache web server installation
------------------------------

####Install Apache
    $ sudo apt-get install apache2 -y
    $ sudo apt-get install apache2-threaded-dev python2.7-dev -y
	
####Install mod_wsgi

Install pip to "easy_install" mod_wsgi, virtualenv and Flask later on

	$ wget -c https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py
	

Now we can install an official release direct from PyPi, run:

	$ sudo pip install mod_wsgi

If you wish to use a version of Apache which is installed into a non standard location, you can set and export the APXS environment variable to the location of the Apache apxs script for your Apache installation before performing the installation.

To verify that the installation was successful, run the mod_wsgi-express script with the start-server command:

	$ mod_wsgi-express start-server
	
This will start up Apache/mod_wsgi on port 8000. You can then verify that the installation worked by pointing your browser at:
	`http://localhost:8000/`. When started in this way, the Apache web server will stay in the foreground. To stop the Apache server, use CTRL-C.

Then reload apache service:

	$ sudo service apache2 restart
	
## Python and Virtualenvwrapper setup

Virtualenv is probably what you want to use during development.
What problem does virtualenv solve? If you want to use Python for other projects besides Flask-based web applications. it is very likely that you will be working with different versions of Python itself, or different versions of Python libraries. Quite often, libraries break backwards compatibility, and it’s unlikely that any serious application will have zero dependencies. So we create virtual environment to keep different project environments isolated if two or more of your projects have conflicting dependencies.

**Python comes with the ubuntu 14.04, so there is no need to install python if you are using the newest ubuntu.**

If Python 2.7 is not installed, install it

`$ sudo apt-get install python2.7`
	
Install some required packages

	$ sudo apt-get install python-dev libpq-dev libxml2-dev libproj-dev libgeos-dev libgdal-dev

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
	
	# copy and paste these two lines at the end of the ~/.bashrc
	export WORKON_HOME=$HOME/.virtualenvs
	source /usr/local/bin/virtualenvwrapper_lazy.sh
	
**Starting a New Virtual Environment**

Virtualenvwrapper provides some nice commands we can use to play around with the environments.

To create a new virtual environment:

	$ mkvirtualenv metpetdb
	New python executable in metpetdb/bin/python
	Installing setuptools, pip...done.
	
As you mihgt notic, the command prompt contains the name before you username
	
	**(metpetdb)**user@xxxx:~$ python --version
	Python 2.7.6

To deactivate and exit the virtual environment, just do

	$ deactivate
	
Tht next time you come back, start you environment by doing:

	$ workon environment_name
	
Remove your current environment:

	$ rmvirtualenv environment_name
	Removing (environment_name)...

Other usage command:
- show a list of environments: `workon`

## Setting up MetpetDDB interface

If you have create a virtual environment for MetpetDB interface and you have not yet fooled around with it, start the virtual environment: `workon environment_name` 

If you are not sure, create a new clean virtual environment:
	
	# Deleting the previous virtual env is optional
	# $ rmvirtualenv environment_name #env name was "metpetdb" if you strictly follow the instruction
	
	$ mkvirtualenv metpetdb
	$ workon metpetdb
	
Create a directory for the project:

	$ mkdir metpetdb
	$ cd metpetdb
	
Under metpetdb directory, we are going to create our secret "app_variables.env" file that points to the API server.

	$ sudo nano app_variables.env
	# copy and paste the following keys into "app_variables.env"
	--------------------------------------------------------
	API_HOST=http://54.164.222.32
	SECRET_KEY=qqqqqqqqqqjjhuk8jl9l99l9l;;0o0o;0'0'
	--------------------------------------------------------
	
Then we clone the interface code from github, just do:
	
	$ sudo apt-get install git -y && git clone https://github.com/metpetdb/metpetdb_interface.git
	
Alright, we are so close to finishing setting up MetpetDB locally. Next, install required dependentcies for the interface.
		
	$ cd metpetdb_interface
	$ pip install -r requirements_new_ubuntu_14.04.txt
	
Finally, run app.py to test if we have set up the interface properly:

	$ python app.py

Visit `http://127.0.0.1:5000/` or `localhost:5000/` to view the project.
	

	
