from indicators.fetch_complexity import pre_fetch_financial_complexity
from indicators.financial_metrics_instance import load_fetched_indicators, get_financial_metrics_instance, get_submitted_projects_info

print("Attempting to load indicators into Redis")
load_fetched_indicators()
print("Attempting to cache financial_metrics_instance into Redis")
get_financial_metrics_instance()
print("Attempting to cache submitted_projects_info into Redis")
get_submitted_projects_info()
print("Cache finished")