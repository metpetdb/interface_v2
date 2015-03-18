<a name="logo"/>
<div align="center">
<a href="http://metpetdb.rpi.edu/" target="_blank">
<img src="http://metpetdb.rpi.edu/metpetweb/images/mpdb-logo.gif" alt="mpdb Logo" width="201" height="148"></img>
</a>
</div>

##metpetdb-interface

Front-end application for the Meptetb system built using Flask.
(metpetdb.rpi.edu)

The API is built in Django and can be found here: https://github.com/metpetdb/metpetdb-py

We will now set up the system and virtual environment for a new/clean meachine, which means `/usr/lib/python2.7/site-packages` is not modified globally for any application. Let's start from installing global applications to virtual environment.

**Before setting up everything:**

	$ sudo apt-get update
	$ sudo apt-get upgrade

Apache web server installation
------------------------------

####Install Apache
    $ sudo apt-get install apache2
    $ sudo apt-get install apache2-threaded-dev python2.7-dev

####Install mod_wsgi
    $ wget http://modwsgi.googlecode.com/files/mod_wsgi-3.4.tar.gz && tar xvfz mod_wsgi-3.4.tar.gz
    $ cd mod_wsgi-3.4
    $ ./configure
    $ make
    $ sudo make install
    $ echo "LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so" | sudo tee /etc/apache2/mods-available/wsgi.load
    $ sudo a2enmod wsgi
    $ sudo a2dissite default

**Note:**If you get error message:`ERROR: Site default does not exist!`

1. Because the .conf under `/etc/apache2/sites-available/` maybe `000-default`. If so, we enter: `sudo a2dissite 000-default`

2. `ls /etc/apache2/sites-available/` You will have either `default` or `000-default` directory, inside the directory, we need to set `default/000-default` to `default.conf/000-default.conf` by:
`sudo mv /etc/apache2/sites-available/default /etc/apache2/sites-available/default.conf`

Then reload apache service:

	$ sudo service apache2 restart
	
## Python and virutalenv setup

Virtualenv is probably what you want to use during development.
What problem does virtualenv solve? If you want to use Python for other projects besides Flask-based web applications. it is very likely that you will be working with different versions of Python itself, or different versions of Python libraries. Quite often, libraries break backwards compatibility, and it’s unlikely that any serious application will have zero dependencies. So we create virtual environment to keep different project environments isolated if two or more of your projects have conflicting dependencies.

**Python comes with the ubuntu 14.04, so there is no need to install python if you are using the newest ubuntu.**

If Python 2.7 is not installed, install it

	$ sudo apt-get install python2.7
	
Install some required packages

	$ sudo apt-get install python-dev libpq-dev libxml2-dev libproj-dev libgeos-dev libgdal-dev
	
Install pip for easy_install virtualenv and Flask later on

	$ wget -c https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py

Install virtualenv:

	$ sudo pip install virtualenv
	
Once you have virtualenv installed, just fire up a shell and create your own environment. Create a project folder and a venv folder within:

	$ mkdir myproject
	$ cd myproject
	$ virtualenv metpetdb
	New python executable in myproject/bin/python
	Installing setuptools, pip...done.

Now, whenever you want to work on a project, you only have to activate the corresponding environment

	$ . metpetdb/bin/activate

**note:** The complete dir is `~/myproject/metpetdb/bin/activate`. If you wish to have only `metpetdb` folder, just create a virtual environment in you home directory. `virtualenv metpetdb` will create a folder named "metpetdb" for it self.
	
To deactivate and exit the virtual environment, just do

	$ deactivate
	