ga_irods - iRODS connector for Django with Celery
#################################################

`ga_irods`_ is a Django+Celery -> `iRODS`_ connector.  The idea is that you can
use this module to write webapps that call a data grid (iRODS) in a web-scale
manner.  Every iCommand is a `Celery`_ task.  All iRODS environments are stored
as model instances in a database.

.. _iRODS: http://www.irods.org
.. _Celery: http://www.celeryproject.org
.. _ga_irods: http://www.github.com/JeffHeard/ga_irods

This is all very well and good, but how to you use it?  Assuming you know a bit
about iRODS, have or know someone who has an account, and are familiar with the
icommands clients (these are commands analogous to the unix file system
commands, but with an i- prepended), then usage of this app is quite simple.
First, add 'ga_irods' to your list of INSTALLED_APPS in Django's settings.py.
Then run::

    $ python manage.py syncdb

That will add the RodsEnvironment model to the admin tool.  Now, assuming
you're an admin on your django installation (you should be if you can run
manage.py at all), then you can add RodsEnvironments for each User in the
system.  I capitalize User, because the owner of every RodsEnvironment must be
an actual User in the django.contrib.auth application.  Finally, make sure that
celeryd is running and that django-celery is installed and listed in
INSTALLED_APPS.

Once environments are setup, you can write a webapp that manipulates iRODS.  One
might attach a RodsEnvironment to a session object, then use this to accomplish
things in an example view like so in your views.py::

    from ga_irods import tasks as itasks

    @requires_login
    def my_view(request):
        if not 'rodsenvironment' in request.session:
            # redirect to allow the user to select from his/her environments
        else:
            stdout, stderr = itasks.ils.delay(request.GET['path']).get()
            return render(request, 'mytemplate.html', lsresults=stdout)

For more information on icommands see the project documentation.
