from core.finance.financial_metrics import FinancialMetrics
from core.utils.get_project_info_from_pronac import GetProjectInfoFromPronac
from .models import Entity
import redis
import pickle

# Redis instance
redis_connection = redis.Redis(host='redis', port=6379, db=0)

def cache_fractions(base_name, fractions):
    global redis_connection
    number_of_fractions = len(fractions)

    redis_connection.set('number_of_{0}_fractions'.format(base_name), number_of_fractions)

    for index, fraction in enumerate(fractions):
            redis_connection.set('{0}_{1}'.format(index, base_name), fraction)

def recover_fractions(base_name):
    global redis_connection
    recovered_fractions = b""

    number_of_fractions = int(redis_connection.get('number_of_{0}_fractions'.format(base_name)))

    for index in range(0, number_of_fractions):
        recovered_fractions += redis_connection.get('{0}_{1}'.format(index, base_name))

    return recovered_fractions

# Financial metrics instance
financial_metrics = None
try:
    financial_metrics = pickle.loads(recover_fractions('financial_metrics'))
except:
    pass

# Submitted project info instance
submitted_projects_info = None
try:
    submitted_projects_info = pickle.loads(recover_fractions('submitted_projects_info'))
except:
    pass

def split_string_into_10(string):
    step_size = int(len(string)/10)
    print(step_size)
    array_of_strings = [string[i:i+step_size] for i in range(0, len(string), step_size)]

    return array_of_strings

def load_fetched_indicators():
    global redis_connection
    for project in Entity.objects.all():
        try:
            redis_connection.set("{0}".format(project.pronac), project.indicators.get(name='complexidade_financeira').value)
        except:
            continue

def fetch_project_complexity(pronac):
    try:
        indicator_value = int(redis_connection.get("{0}".format(pronac)))
    except:
        indicator_value = 0

    return indicator_value
    
def get_financial_metrics_instance():
    global financial_metrics
    if financial_metrics is None:
        financial_metrics = FinancialMetrics()
        financial_metrics.save()
    
        financial_metrics_dump = pickle.dumps(financial_metrics)

        splitted_financial_metrics_dump = split_string_into_10(financial_metrics_dump)

        cache_fractions('financial_metrics', splitted_financial_metrics_dump)

def get_submitted_projects_info():
    global submitted_projects_info
    if submitted_projects_info is None:
        submitted_projects_info = GetProjectInfoFromPronac()

        submitted_projects_info_dump = pickle.dumps(submitted_projects_info)

        splitted_submitted_projects_info_dump = split_string_into_10(submitted_projects_info_dump)

        cache_fractions('submitted_projects_info', splitted_submitted_projects_info_dump)