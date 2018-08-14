# Remove this import when has a valid complexity value
import random
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Entity, User, ProjectFeedback, MetricFeedback, Metric, Indicator
from salic_db.utils import test_connection, make_query_from_db
from core.finance.financial_metrics import FinancialMetrics

# Instanciating FinancialMetrics global module
financial_metrics = FinancialMetrics()

# Uncomment line below when deploying
financial_metrics.save()

def index(request):
    # projects = [
    #     {"pronac": "1234", "complexity": 25,
    #         "project_name": "Show do Tiririca", "analist": "Florentina"},
    #     {"pronac": "4321", "complexity": 75,
    #         "project_name": "Show do ex Calipso", "analist": "Chimbinha"},
    #     {"pronac": "1324", "complexity": 95,
    #         "project_name": "Projeto da Cláudia Leitte", "analist": "Cláudia Leitte"},
    #     {"pronac": "1243", "complexity": 15,
    #         "project_name": "Tourada", "analist": "Ferdinando"},
    #     {"pronac": "2143", "complexity": 5,
    #         "project_name": "Projeto modelo", "analist": "Modelo"},
    # ]
    projects = projects_to_analyse(request)

    return render(request, 'index.html', {'projects': projects})


def show_metrics(request, pronac):
    pronac = int(pronac)
    try:
        project = Entity.objects.get(pronac=pronac)
    except:
        string_pronac = "{:06}".format(pronac)
        project_query = "SELECT CONCAT(AnoProjeto, Sequencial), NomeProjeto \
        FROM SAC.dbo.Projetos WHERE CONCAT(AnoProjeto, Sequencial) = '{0}'".format(string_pronac)
        project_raw_data = make_query_from_db(project_query)
        project_data = {
                'pronac': project_raw_data[0][0],
                'project_name': project_raw_data[0][1]
        }

        # project_data = {
        #     'pronac': pronac,
        #     'project_name': 'Mock'
        # }
        project = Entity.objects.create(pronac=int(project_data['pronac']), name=project_data['project_name'])

    current_user = None
    metrics = []
    return render(request, 'show_metrics.html', {'project': project, 'user': current_user, 'metrics': metrics})

def db_connection_test(request):
    connection_result = test_connection()
    return HttpResponse(connection_result)


def projects_to_analyse(request):
    end_situations = " \
        'A09', 'A13', 'A14', 'A16', 'A17', 'A18', 'A20', 'A23', 'A24', 'A26', \
        'A40', 'A41', 'A42', 'C09', 'D18', 'E04', 'E09', 'E36', 'E47', 'E49', \
        'E63', 'E64', 'E65', 'G16', 'G25', 'G26', 'G29', 'G30', 'G56', 'K00', \
        'K01', 'K02', 'L01', 'L02', 'L03', 'L04', 'L05', 'L06', 'L08', 'L09', \
        'L10', 'L11' \
    "

    query = "SELECT CONCAT(AnoProjeto, Sequencial), NomeProjeto, Analista \
             FROM SAC.dbo.Projetos WHERE DtFimExecucao < GETDATE() \
             AND Situacao NOT IN ({})".format(end_situations)

    query_result = make_query_from_db(query)

    filtered_data = [{'pronac': each[0],
                      'complexity': random.randint(0, 100),
                      'project_name': each[1],
                      'analist': each[2]}
                      for each in query_result]

    return filtered_data

def get_items_interval(mean, std):
    start = 0
    if mean - (1.5 * std) > 0:
        start = mean - (1.5 * std)

    end = mean + (1.5 * std)

    result = {
        'start': int(start),
        'end': int(end)
    }

    return result

def get_outlier_color(is_outlier):
    if is_outlier:
        return 'Metric-bad'
    else:
        return 'Metric-good'

def float_to_money(value):
    us_value = '{:,.2f}'.format(value)
    v_value = us_value.replace(',','v')
    c_value = v_value.replace('.',',')
    return 'R$' + c_value.replace('v','.')

def register_project_indicator(pronac, name, value):
    entity = Entity.objects.get(pronac=pronac)
    indicator = Indicator.objects.get_or_create(entity=entity, name=name)
    indicator = indicator[0]
    indicator.value = value
    indicator.save()
    
    return indicator

def register_project_metric(name, value, reason, indicator_name, pronac):
    entity = Entity.objects.get(pronac=pronac)
    indicator = Indicator.objects.get(name=indicator_name, entity=entity)
    metric = Metric.objects.get_or_create(name=name, indicator=indicator)
    metric = metric[0]
    metric.value = value
    metric.reason = reason
    metric.save()
    
    return metric

def fetch_user_data(request):
    user_email = request.POST['user_email'] + '@cultura.gov.br'
    try:
        user = User.objects.get(email=user_email)
    except:
        user_name = str(request.POST['user_first_name'])

        user = User.objects.create(email=user_email, name=user_name)

    pronac = request.POST['project_pronac']
    project = get_object_or_404(Entity, pronac=int(pronac))

    metrics_list = [
        'items',
        'raised_funds',
        'verified_funds',
        'approved_funds',
        'common_items_ratio',
        'total_receipts',
        'new_providers',
        'proponent_projects'
        ]

    metrics = {}

    for metric_name in metrics_list:
        try:
            metrics[metric_name] = financial_metrics.get_metrics(int(pronac), [metric_name])[metric_name]
        except:
            metrics[metric_name] = None

    result = {
        'pronac': pronac,
        'received_metrics': metrics
    }

    #complexidade_financeira
    financial_complexity_indicator = register_project_indicator(int(pronac), 'complexidade_financeira', 0)

    # itens_orcamentarios
    items = {
            'total_items': 0,
            'interval_start': 0,
            'interval_end': 0,
            'outlier_check': get_outlier_color(False)
    }

    if metrics['items'] is not None:
        items_interval = get_items_interval(metrics['items']['mean'], metrics['items']['std'])
        items = {
            'total_items': metrics['items']['value'],
            'interval_start': items_interval['start'],
            'interval_end': items_interval['end'],
            'outlier_check': get_outlier_color(metrics['items']['is_outlier'])
        }

    result['itens_orcamentarios'] = items

    register_project_metric('itens_orcamentarios', items['total_items'], str(items), financial_complexity_indicator.name, int(pronac))

    # valor_captado
    raised_funds = {
        'value': float_to_money(0.0),
        'float_value': 0.0,
        'maximum_expected_value': float_to_money(0.0),
        'outlier_check': get_outlier_color(False)
    }

    if metrics['raised_funds'] is not None:
        raised_funds = {
            'value': float_to_money(metrics['raised_funds']['total_verified_funds']),
            'float_value': metrics['raised_funds']['total_verified_funds'],
            'maximum_expected_value': float_to_money(metrics['raised_funds']['maximum_expected_funds']),
            'outlier_check': get_outlier_color(metrics['raised_funds']['is_outlier'])
        }

    result['valor_captado'] = raised_funds

    register_project_metric('valor_captado', raised_funds['float_value'], str(raised_funds), financial_complexity_indicator.name, int(pronac))

    # valor_comprovado
    verified_funds = {
        'value': float_to_money(0.0),
        'float_value': 0.0,
        'maximum_expected_value': float_to_money(0.0),
        'outlier_check': get_outlier_color(False)
    }

    if metrics['verified_funds'] is not None:
        verified_funds = {
            'value': float_to_money(metrics['verified_funds']['total_verified_funds']),
            'float_value': metrics['verified_funds']['total_verified_funds'],
            'maximum_expected_value': float_to_money(metrics['verified_funds']['maximum_expected_funds']),
            'outlier_check': get_outlier_color(metrics['verified_funds']['is_outlier'])
        }

    result['valor_comprovado'] = verified_funds

    register_project_metric('valor_comprovado', verified_funds['float_value'], str(verified_funds), financial_complexity_indicator.name, int(pronac))

    project_indicators = [
        {
            'name': 'complexidade_financeira',
            'value': '80',
            'metrics': [
                {
                    'name': 'itens_orcamentarios',
                    'value': result['itens_orcamentarios']['total_items'],
                    'reason': 'any reason',
                    'outlier_check': result['itens_orcamentarios']['outlier_check'],
                    'interval_start': result['itens_orcamentarios']['interval_start'],
                    'interval_end': result['itens_orcamentarios']['interval_end']
                },
                {
                    'name': 'itens_orcamentarios_fora_do_comum',
                    'value': '20',
                    'reason': 'any reason',
                    'outlier_check': 'Metric-average',
                    'expected_itens': [
                        {
                            'name': 'Nome do Item 1',
                            'link': '#',
                        },
                        {
                            'name': 'Nome do Item 2',
                            'link': '#',
                        },
                        {
                            'name': 'Nome do Item 3',
                            'link': '#',
                        },
                        {
                            'name': 'Nome do Item 4',
                            'link': '#',
                        },
                        {
                            'name': 'Nome do Item 5',
                            'link': '#',
                        },
                    ],
                    'missing_itens': [
                        {
                            'name': 'Nome do Item 1',
                            'link': '#',
                        },
                        {
                            'name': 'Nome do Item 2',
                            'link': '#',
                        },
                        {
                            'name': 'Nome do Item 3',
                            'link': '#',
                        },
                        {
                            'name': 'Nome do Item 4',
                            'link': '#',
                        },
                        {
                            'name': 'Nome do Item 5',
                            'link': '#',
                        },
                    ]
                },
                {
                    'name': 'comprovantes_pagamento',
                    'value': '30',
                    'reason': 'any reason',
                    'outlier_check': 'Metric-bad',
                },
                {
                    'name': 'precos_acima_media',
                    'value': '40',
                    'reason': 'any reason',
                    'outlier_check': ''
                },
                {
                    'name': 'valor_comprovado',
                    'value': result['valor_comprovado']['value'],
                    'reason': result['valor_comprovado']['maximum_expected_value'],
                    'outlier_check': result['valor_comprovado']['outlier_check']
                },
                {
                    'name': 'valor_captado',
                    'value': result['valor_captado']['value'],
                    'reason': result['valor_captado']['maximum_expected_value'],
                    'outlier_check': result['valor_captado']['outlier_check']
                },
                {
                    'name': 'mudancas_planilha_orcamentaria',
                    'value': '70',
                    'reason': 'any reason',
                    'outlier_check': '',
                    'document_version': 14,
                },
                {
                    'name': 'projetos_mesmo_proponente',
                    'value': '80',
                    'reason': 'any reason',
                    'outlier_check': '',
                    'proponent_projects': [
                        {
                            'name': 'Projeto 1',
                            'link': '#',
                        },
                        {
                            'name': 'Projeto 2',
                            'link': '#',
                        },
                        {
                            'name': 'Projeto 3',
                            'link': '#',
                        },
                    ],
                },
                {
                    'name': 'novos_fornecedores',
                    'value': '90',
                    'reason': 'any reason',
                    'outlier_check': '',
                    'providers': [
                        {
                            'name': 'Ferdinando',
                            'itens_list': [
                                {
                                    'name': 'Nome do Item 1',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 2',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 3',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 4',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 5',
                                    'link': '#',
                                },
                            ]
                        },
                        {
                            'name': 'Bruce Wayne',
                            'itens_list': [
                                {
                                    'name': 'Nome do Item 1',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 2',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 3',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 4',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 5',
                                    'link': '#',
                                },
                            ]
                        },
                        {
                            'name': 'Frank Castle',
                            'itens_list': [
                                {
                                    'name': 'Nome do Item 1',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 2',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 3',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 4',
                                    'link': '#',
                                },
                                {
                                    'name': 'Nome do Item 5',
                                    'link': '#',
                                },
                            ]
                        },
                    ]
                },
                {
                    'name': 'valor_aprovado',
                    'value': '100',
                    'reason': 'any reason',
                    'outlier_check': ''
                },
                {
                    'name': 'nome_da_métrica',
                    'value': '12',  # É porcentagem? Dinheiro? Confirmar informações
                    'reason': 'any reason',  # Texto se necessário
                    'outlier_check': 'Metric-bad'  # E outlier?
                },
            ]
        },
    ]
    project_feedback_list = ['Muito simples',
                             'Simples', 'Normal', 'Complexo', 'Muito complexo']

    # return render(request, 'show_metrics.html', {'project': project, 'user': user, 'project_indicators': project_indicators, 'project_feedback_list': project_feedback_list})
    return HttpResponse(str(result))

def post_metrics_feedback(request):

    entity = Entity.objects.get(pronac=request.POST['project_pronac'])
    user = User.objects.get(email=request.POST['user_email'])
    indicators = Indicator.objects.filter(entity=entity)

    saved_data = {}

    # Creates project feedback object
    project_feedback_grade = request.POST['project_feedback_grade']
    saved_project_feedback = ProjectFeedback.objects.create(
        user=user, entity=entity, grade=project_feedback_grade)

    saved_data['project_feedback'] = saved_project_feedback.grade

    saved_data['metrics_feedback'] = []

    ratings = list(request.POST['all_ratings'])
    ratings.reverse()

    # Creates metric feedback objects
    for indicator in indicators:
        for metric in indicator.metrics.all():
            metric_feedback_text_tag = metric.name + '_text'

            metric_feedback_rating = ratings.pop()
            metric_feedback_text = request.POST[metric_feedback_text_tag]

            saved_metric_feedback = MetricFeedback.objects.create(
                user=user, metric=metric, grade=int(metric_feedback_rating), reason=metric_feedback_text)

            saved_data['metrics_feedback'].append({
                'metric_name': saved_metric_feedback.metric.name,
                'grade': saved_metric_feedback.grade,
                'reason': saved_metric_feedback.reason
            })

    return HttpResponse(status=201)
