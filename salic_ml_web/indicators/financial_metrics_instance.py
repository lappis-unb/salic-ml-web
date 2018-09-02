from core.finance.financial_metrics import FinancialMetrics
from core.utils.get_project_info_from_pronac import GetProjectInfoFromPronac

# Instanciating FinancialMetrics global module
financial_metrics = FinancialMetrics()

# Uncomment line below when deploying
financial_metrics.save()

# Financial metrics module project list
submitted_projects_info = GetProjectInfoFromPronac()