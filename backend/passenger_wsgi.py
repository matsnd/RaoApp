import os
import sys

# Add venv site-packages to path
_base = os.path.dirname(__file__)
_venv = os.path.join(_base, '.venv', 'lib', 'python3.11', 'site-packages')
if os.path.isdir(_venv):
    sys.path.insert(0, _venv)
sys.path.insert(0, _base)

import imp
wsgi = imp.load_source('wsgi', os.path.join(_base, 'wsgi.py'))
application = wsgi.application
