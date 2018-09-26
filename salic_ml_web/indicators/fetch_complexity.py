from .views import financial_metrics, projects_to_analyse, register_project_indicator
from .models import Entity, Metric, Indicator

def get_financial_complexity(metrics):
    try:
        complexity = 100 - (metrics['easiness']['easiness'] * 100)
    except:
        complexity = 1

    return complexity


def pre_fetch_financial_complexity():        
    try:
        projects = projects_to_analyse(None)
    except:
        projects = [
        {"pronac": "90021", "complexity": 25,
            "project_name": "Indie 2009 - Mostra de Cinema Mundial", "analist": "Florentina"},
        {"pronac": "153833", "complexity": 75,
            "project_name": "TRES SOMBREROS DE COPA", "analist": "Chimbinha"},
        {"pronac": "160443", "complexity": 95,
            "project_name": "SERGIO REIS – CORAÇÃO ESTRADEIRO", "analist": "Cláudia Leitte"},
        {"pronac": "118593", "complexity": 15,
            "project_name": "ÁGUIA  CARNAVAL 2012: TROPICÁLIA! O MOVIMENTO QUE NÃO TERMINOU", "analist": "Ferdinando"},
        {"pronac": "161533", "complexity": 5,
            "project_name": "“Livro sobre Serafim Derenzi” (título provisório)", "analist": "Modelo"},
        {"pronac": "171372", "complexity": 5,
            "project_name": "“Paisagismo Brasileiro, Roberto Burle Marx e Haruyoshi Ono – 60 anos de história”.", "analist": "Modelo"},
        {"pronac": "92739", "complexity": 5,
            "project_name": "Circulação de oficinas e shows - Claudia Cimbleris", "analist": "Modelo"},
    ]

    metrics_list = [
        'items',
        'raised_funds',
        'verified_funds',
        'approved_funds',
        'common_items_ratio',
        'total_receipts',
        'new_providers',
        'proponent_projects',
        'easiness',
        'items_prices'
    ]

    for project in projects:
        try:
            entity = Entity.objects.get(pronac=int(project['pronac']))
        except:
            entity = Entity.objects.create(pronac=int(project['pronac']), name=project['project_name'])

        metrics = financial_metrics.get_metrics(project['pronac'])
        print(get_financial_complexity(metrics))
        financial_complexity_indicator = register_project_indicator(int(project['pronac']), 'complexidade_financeira', get_financial_complexity(metrics))
