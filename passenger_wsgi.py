import os
import sys

# Add project root directory to sys.path so Passenger can import project modules
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bharatshop.settings')

from bharatshop.wsgi import application

