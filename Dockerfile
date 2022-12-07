# TODO: remove docker image tagging and pull the image from dockerhub
# FROM hydroshare/hs_docker_base:release-1.13

# for now, multi-stage build with a git submodule:
# docker build -t hs_docker_base ./hs_docker_base/ && docker build -t hydroshare .

# FROM a645e386aa49757b0dcfc46c168ce0fc4edbefcf
# celery fails

# FROM c4f24c53a0739ac8556e240556b8763f508c05e0
# attempt to fix celery by unpinning it
# had to remove flower and still didn't work

# FROM df0863f4b577ec8d82e76be67fc0c283a1b1b51f
# TODO devin
# solr fails at end of local-dev... 
#RuntimeError: Model class django.contrib.sites.models.Site doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.
# ModuleNotFoundError: No module named 'autocomplete_light'

# FROM a3d9fe535fd4cdffc796e27cf000d580beb45261
# import defusedxml.ElementTree as ElementTree
#   File "/usr/local/lib/python3.6/site-packages/defusedxml/ElementTree.py", line 62, in <module>
#     _XMLParser, _iterparse, _IterParseIterator, ParseError = _get_py3_cls()
#   File "/usr/local/lib/python3.6/site-packages/defusedxml/ElementTree.py", line 56, in _get_py3_cls
#     _IterParseIterator = pure_pymod._IterParseIterator
# AttributeError: module 'xml.etree.ElementTree' has no attribute '_IterParseIterator'

# FROM af0337bab6c3b08a757cedc2cd24ceb1b15e6b38
# doesn't build

# FROM acbf15d3aa2be38a29bbb523bba74c87f3655ba9
# attempt celery 4.4.7
# django.contrib.sites

# FROM 905a3dff4cb20c9cbe8fb09068567edff2111aa0
# reqs from GH
# django.contrib.sites

# FROM ff1ae3cf5f5a485b5dbe640e12427ced6ddf7057
# pin only django
# Error: No such command 'flower'.
# removed flower
# irods password errors during build
#File "/hydroshare/hs_core/models.py", line 44, in <module>
# defaultworker    |     from django_irods.icommands import SessionException
# defaultworker    |   File "/hydroshare/django_irods/icommands.py", line 263, in <module>
# defaultworker    |     GLOBAL_SESSION.run('iinit', None, GLOBAL_ENVIRONMENT.auth)
# defaultworker    |   File "/hydroshare/django_irods/icommands.py", line 182, in run
# defaultworker    |     raise SessionException(proc.returncode, stdout, stderr)
# defaultworker    | django_irods.icommands.SessionException: (SessionException(...), "Error processing IRODS request: 1. stderr follows:\n\nb' ERROR: Save Password failure status = -909000 NO_PASSWORD_ENTERED\\n'")

# FROM 8122c156526416f35e34bcf1dc8efa0d5490ff85
# same as above, but pin celery for flower
# celery4 doesn't run on python 3.9

# FROM 685daf730880eef212922d1d885e109ae57fd825
# restarting
# File "/hydroshare/hydroshare/settings.py", line 265, in <module>
#     from PIL import ImageFile
#   File "/usr/local/lib/python3.9/site-packages/PIL/ImageFile.py", line 35, in <module>
#     from . import Image
#   File "/usr/local/lib/python3.9/site-packages/PIL/Image.py", line 43, in <module>
#     import defusedxml.ElementTree as ElementTree
#   File "/usr/local/lib/python3.9/site-packages/defusedxml/ElementTree.py", line 62, in <module>
#     _XMLParser, _iterparse, _IterParseIterator, ParseError = _get_py3_cls()
#   File "/usr/local/lib/python3.9/site-packages/defusedxml/ElementTree.py", line 56, in _get_py3_cls
#     _IterParseIterator = pure_pymod._IterParseIterator
# AttributeError: module 'xml.etree.ElementTree' has no attribute '_IterParseIterator'

# ^^HS

# defaultworker
# Traceback (most recent call last):
#   File "/usr/local/lib/python3.9/site-packages/kombu/utils/objects.py", line 42, in __get__
#     return obj.__dict__[self.__name__]
# KeyError: 'data'

# During handling of the above exception, another exception occurred:

# Traceback (most recent call last):
#   File "/usr/local/bin/celery", line 8, in <module>
#     sys.exit(main())

# FROM a686e1311da36ab6a84c6d7b704195ced1e5b2f3 
# same as above, PG 14
# Same as above

# FROM e1a76374484d43f1ead34dc9911f05620b2e30d1
# req in docker
# File "/usr/local/lib/python3.6/site-packages/django/db/models/base.py", line 116, in __new__
# hydroshare       |     "INSTALLED_APPS." % (module, name)
# hydroshare       | RuntimeError: Model class django.contrib.sites.models.Site doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.

# FROM aa50cd504ae638921f5dadae3b810be0b88e1921
# PG fix and docker install
# Traceback (most recent call last):
#   File "/hydroshare/manage.py", line 10, in <module>
#     execute_from_command_line(sys.argv)
#   File "/usr/local/lib/python3.9/site-packages/django/core/management/__init__.py", line 419, in execute_from_command_line
#     utility.execute()
#   File "/usr/local/lib/python3.9/site-packages/django/core/management/__init__.py", line 363, in execute
#     settings.INSTALLED_APPS
#   File "/usr/local/lib/python3.9/site-packages/django/conf/__init__.py", line 82, in __getattr__
#     self._setup(name)
#   File "/usr/local/lib/python3.9/site-packages/django/conf/__init__.py", line 69, in _setup
#     self._wrapped = Settings(settings_module)
#   File "/usr/local/lib/python3.9/site-packages/django/conf/__init__.py", line 170, in __init__
#     mod = importlib.import_module(self.SETTINGS_MODULE)
#   File "/usr/local/lib/python3.9/importlib/__init__.py", line 127, in import_module
#     return _bootstrap._gcd_import(name[level:], package, level)
#   File "<frozen importlib._bootstrap>", line 1030, in _gcd_import
#   File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
#   File "<frozen importlib._bootstrap>", line 986, in _find_and_load_unlocked
#   File "<frozen importlib._bootstrap>", line 680, in _load_unlocked
#   File "<frozen importlib._bootstrap_external>", line 850, in exec_module
#   File "<frozen importlib._bootstrap>", line 228, in _call_with_frames_removed
#   File "/hydroshare/hydroshare/settings.py", line 265, in <module>
#     from PIL import ImageFile
#   File "/usr/local/lib/python3.9/site-packages/PIL/ImageFile.py", line 35, in <module>
#     from . import Image
#   File "/usr/local/lib/python3.9/site-packages/PIL/Image.py", line 43, in <module>
#     import defusedxml.ElementTree as ElementTree
#   File "/usr/local/lib/python3.9/site-packages/defusedxml/ElementTree.py", line 62, in <module>
#     _XMLParser, _iterparse, _IterParseIterator, ParseError = _get_py3_cls()
#   File "/usr/local/lib/python3.9/site-packages/defusedxml/ElementTree.py", line 56, in _get_py3_cls
#     _IterParseIterator = pure_pymod._IterParseIterator
# AttributeError: module 'xml.etree.ElementTree' has no attribute '_IterParseIterator'

# -----------------------------
# FROM 0a441608a732f3565e846f7175e461349bdca640
# upgrade defusedxml
#  ModuleNotFoundError: No module named 'dal'
# fixed by adding autocomplete-light to settings.py

# Then get:
# File "<frozen importlib._bootstrap>", line 986, in _find_and_load_unlocked
# defaultworker    |     from django_irods.icommands import SessionException
# defaultworker    |   File "/hydroshare/django_irods/icommands.py", line 263, in <module>
# defaultworker    |     GLOBAL_SESSION.run('iinit', None, GLOBAL_ENVIRONMENT.auth)
# defaultworker    |   File "/hydroshare/django_irods/icommands.py", line 182, in run
# defaultworker    |   File "<frozen importlib._bootstrap>", line 680, in _load_unlocked
# defaultworker    |     raise SessionException(proc.returncode, stdout, stderr)
# defaultworker    | django_irods.icommands.SessionException: (SessionException(...), "Error processing IRODS request: 1. stderr follows:\n\nb' ERROR: Save Password failure status = -909000 NO_PASSWORD_ENTERED\\n'")

FROM dd0aac5b201b9180bc428dbb1173f7543146bb54
# install gdal

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
