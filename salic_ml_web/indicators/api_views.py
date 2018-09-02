from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from indicators.views import projects_to_analyse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import generic
from django.http import JsonResponse
import json
import difflib
from indicators.financial_metrics_instance import financial_metrics, submitted_projects_info
from core.utils.get_project_info_from_pronac import GetProjectInfoFromPronac
from indicators.models import Entity, Indicator, Metric, User
from django.shortcuts import get_object_or_404

def fetch_entity(pronac):
    string_pronac = "{:06}".format(pronac)
    try:
        project = Entity.objects.get(pronac=pronac)
    except:
        # project_query = "SELECT CONCAT(AnoProjeto, Sequencial), NomeProjeto \
        # FROM SAC.dbo.Projetos WHERE CONCAT(AnoProjeto, Sequencial) = '{0}'".format(string_pronac)
        # project_raw_data = make_query_from_db(project_query)
        # project_data = {
        #         'pronac': project_raw_data[0][0],
        #         'project_name': project_raw_data[0][1]
        # }

        # project_data = {
        #     'pronac': pronac,
        #     'project_name': 'Mock'
        # }

        info = submitted_projects_info.get_projects_name([string_pronac])

        project_data = {
            'pronac': pronac,
            'project_name': info[string_pronac]
        }

        project = Entity.objects.create(pronac=int(project_data['pronac']), name=project_data['project_name'])

    return project


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

def set_width_bar(min_interval, max_interval, value):
    max_value = max_interval*2

    if max_value is 0:
        max_value = 1

    return {
        'max_value': max_value, 
        'min_interval': (min_interval/max_value)*100, 
        'project': ((value/max_value)*100),
        'interval': (max_interval-min_interval)
    }

def calculate_search_cutoff(keyword_len):
    if keyword_len >= 6:
        cutoff = 0.3
    else:
        cutoff = keyword_len * 0.05
    
    return cutoff

def paginate_by_10(full_list):
    paginated_list = [full_list[i:i+10] for i in range(0, len(full_list), 10)]
    
    return paginated_list

def get_page(paginated_list, page):
    try:
        required_list = paginated_list[page - 1]
    except:
        required_list = []

    return required_list

class ProjectsView(APIView):
    """
    A view that returns a list containing all the projects
    """
    renderer_classes = (JSONRenderer, )
    @csrf_exempt
    def get(self, request, format=None, **kwargs):
        
        try:
            projects = projects_to_analyse(request)
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

        paginated_list = paginate_by_10(projects)

        projects_list = get_page(paginated_list, int(kwargs['page']))

        content = {'projects': projects_list, 'last_page':len(paginated_list)}
        
        return JsonResponse(content)

class SearchProjectView(APIView):
    """
    A view that returns a list containing projects that match the given keyword
    """
    renderer_classes = (JSONRenderer, )
    @csrf_exempt
    def get(self, request, format=None, **kwargs):
        
        try:
            projects = projects_to_analyse(request)
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

        projects_processed = [{
            "pronac": project['pronac'], 
            "complexity": project['complexity'],
            "project_name": project['project_name'],
            "project_name_lowered": project['project_name'].lower(), 
            "analist": project['analist']
        } for project in projects]

        NAME_CUTOFF = calculate_search_cutoff(len(kwargs['keyword']))

        name_matches_list = difflib.get_close_matches(
            kwargs['keyword'].lower(), 
            [project['project_name_lowered'] for project in projects_processed], 
            n=len(projects), 
            cutoff=NAME_CUTOFF
            )

        pronac_matches_list = difflib.get_close_matches(
            kwargs['keyword'], 
            [project['pronac'] for project in projects], 
            n=len(projects), 
            cutoff=0.2
            )

        result_list = [project for project in projects_processed if project['pronac'] in pronac_matches_list or project['project_name_lowered'] in name_matches_list]

        paginated_list = paginate_by_10(result_list)

        projects_list = get_page(paginated_list, int(kwargs['page']))
        
        content = {'projects': projects_list, 'last_page': len(paginated_list)}
        
        return JsonResponse(content)

class ProjectInfoView(APIView):
    """
    A view that creates or sets an user and returns a single project information (indicators, metrics, feedbacks...)
    """
    renderer_classes = (JSONRenderer, )
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, format=None, **kwargs):
        user_data = json.loads(request.body)

        user_email = user_data['email'] + '@cultura.gov.br'
        try:
            user = User.objects.get(email=user_email)
        except:
            user_name = user_data['name']

            user = User.objects.create(email=user_email, name=user_name)

        pronac = kwargs['pronac']
        project = fetch_entity(int(pronac))

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

        metrics = {}

        total_metrics = financial_metrics.get_metrics("{:06}".format(int(pronac)))

        for metric_name in metrics_list:
            try:
                metrics[metric_name] = total_metrics[metric_name]
            except:
                if metric_name is '':
                    metrics[metric_name] = total_metrics[metric_name]
                else:
                    metrics[metric_name] = None

        result = {
            'pronac': pronac,
            'received_metrics': metrics
        }

        # return HttpResponse(str(result))

        #complexidade_financeira
        financial_complexity_indicator = register_project_indicator(int(pronac), 'complexidade_financeira', 0)

        easiness = {
            'value': 0,
        }

        if metrics['easiness'] is not None:
            easiness = {
                'value': float("{0:.2f}".format(metrics['easiness']['easiness'] * 100))
            }

        result['easiness'] = easiness

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
                'total_items': int(metrics['items']['value']),
                'interval_start': int(items_interval['start']),
                'interval_end': int(items_interval['end']),
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
                'value': float_to_money(metrics['raised_funds']['total_raised_funds']),
                'float_value': metrics['raised_funds']['total_raised_funds'],
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

        # valor_aprovado
        approved_funds = {
            'value': float_to_money(0),
            'float_value': 0.0,
            'maximum_expected_funds': float_to_money(0.0),
            'outlier_check': get_outlier_color(False)
        }

        if metrics['approved_funds'] is not None:
            approved_funds = {
                'value': float_to_money(metrics['approved_funds']['total_approved_funds']),
                'float_value': metrics['approved_funds']['total_approved_funds'],
                'maximum_expected_funds': float_to_money(metrics['approved_funds']['maximum_expected_funds']),
                'outlier_check': get_outlier_color(metrics['approved_funds']['is_outlier'])
            }
        
        result['valor_aprovado'] = approved_funds

        # itens_orcamentarios_fora_do_comum
        

        common_items_ratio = {
            'outlier_check': get_outlier_color(False),
            'value': 0.0,
            'float_value': 0.0,
            'mean': 0.0,
            'std': 0.0,
            'uncommon_items': [],
            'common_items_not_in_project': []
        }

        if metrics['common_items_ratio'] is not None:
            common_items_not_in_project_list = []
            uncommon_items_list = []

            for item_id in metrics['common_items_ratio']['common_items_not_in_project']:
                common_items_not_in_project_list.append({
                    'id': item_id,
                    'name': metrics['common_items_ratio']['common_items_not_in_project'][item_id],
                    'link': '#'
                })

            for item_id in metrics['common_items_ratio']['uncommon_items']:
                uncommon_items_list.append({
                    'id': item_id,
                    'name': metrics['common_items_ratio']['uncommon_items'][item_id],
                    'link': '#'
                })

            common_items_ratio = {
                'outlier_check': get_outlier_color(metrics['common_items_ratio']['is_outlier']),
                'value': "{0:.2f}".format(100 - metrics['common_items_ratio']['value'] * 100),
                'float_value': (100 - metrics['common_items_ratio']['value'] * 100),
                'mean': metrics['common_items_ratio']['mean'],
                'std': metrics['common_items_ratio']['std'],
                'uncommon_items': uncommon_items_list,
                'common_items_not_in_project': common_items_not_in_project_list
            }

        result['itens_orcamentarios_fora_do_comum'] = common_items_ratio

        register_project_metric('itens_orcamentarios_fora_do_comum', common_items_ratio['value'], "", financial_complexity_indicator.name, int(pronac))

        # comprovantes_pagamento
        total_receipts = {
            'outlier_check': get_outlier_color(False),
            'total_receipts': 0,
            'maximum_expected_in_segment': 0
        }

        if metrics['total_receipts'] is not None:
            total_receipts = {
                'outlier_check': get_outlier_color(metrics['total_receipts']['is_outlier']),
                'total_receipts': int(metrics['total_receipts']['total_receipts']),
                'maximum_expected_in_segment': int(metrics['total_receipts']['maximum_expected_in_segment'])
            }

        result['comprovantes_pagamento'] = total_receipts

        register_project_metric('comprovantes_pagamento', total_receipts['total_receipts'], str(total_receipts), financial_complexity_indicator.name, int(pronac))

        # novos_fornecedores
        new_providers = {
            'new_providers_list': [],
            'new_providers_quantity': 0,
            'new_providers_percentage': 0,
            'segment_average_percentage': 0,
            'outlier_check': get_outlier_color(False),
            'all_projects_average_percentage': 0
        }

        if metrics['new_providers'] is not None:
            new_providers_list = []

            for provider_cnpj_cpf in metrics['new_providers']['new_providers']:
                items_by_provider = []

                for item_id in metrics['new_providers']['new_providers'][provider_cnpj_cpf]['items']:
                    items_by_provider.append({
                        'item_id': item_id,
                        'item_name': metrics['new_providers']['new_providers'][provider_cnpj_cpf]['items'][item_id],
                        'item_link': '#'
                    })

                new_providers_list.append({
                    'provider_cnpj_cpf': provider_cnpj_cpf,
                    'provider_name': metrics['new_providers']['new_providers'][provider_cnpj_cpf]['name'],
                    'provider_items': items_by_provider
                })

            new_providers = {
                'new_providers_quantity': len(new_providers_list),
                'new_providers_list': new_providers_list,
                'new_providers_percentage': metrics['new_providers']['new_providers_percentage'],
                'segment_average_percentage': metrics['new_providers']['segment_average_percentage'],
                'outlier_check': get_outlier_color(metrics['new_providers']['is_outlier']),
                'all_projects_average_percentage': metrics['new_providers']['all_projects_average_percentage']
            }

        result['novos_fornecedores'] = new_providers

        register_project_metric('novos_fornecedores', new_providers['new_providers_quantity'], "", financial_complexity_indicator.name, int(pronac))

        # projetos_mesmo_proponente
        proponent_projects = {
            'cnpj_cpf': '',
            'submitted_projects': [],
            'analyzed_projects': [],
            'outlier_check': get_outlier_color(False)
        }

        if metrics['proponent_projects'] is not None:
            submitted_projects_list = []
            analyzed_projects_list = []

            all_pronacs = metrics['proponent_projects']['submitted_projects']['pronacs_of_this_proponent']

            projects_information = submitted_projects_info.get_projects_name(all_pronacs)
            for project_pronac in metrics['proponent_projects']['submitted_projects']['pronacs_of_this_proponent']:
                submitted_projects_list.append({
                    'pronac': project_pronac,
                    'name': projects_information[project_pronac],
                    'link': '#'
                })

            for project_pronac in metrics['proponent_projects']['analyzed_projects']['pronacs_of_this_proponent']:
                analyzed_projects_list.append({
                    'pronac': project_pronac,
                    'name': projects_information[project_pronac],
                    'link': '#'
                })

            proponent_projects = {
                'cnpj_cpf': metrics['proponent_projects']['cnpj_cpf'],
                'submitted_projects': submitted_projects_list,
                'analyzed_projects': analyzed_projects_list,
                'outlier_check': get_outlier_color(False)
            }

        result['projetos_mesmo_proponente'] = proponent_projects

        # precos_acima_media
        items_prices = {
            'value': 0,
            'outlier_check': get_outlier_color(False),
            'items': [],
            'total_items': 0,
            'maximum_expected': 0
        }

        if metrics['items_prices'] is not None:
            items_list = []

            for item_id in metrics['items_prices']['outlier_items']:
                items_list.append({
                    'item_id': item_id,
                    'item_name': metrics['items_prices']['outlier_items'][item_id],
                    'link': '#'
                })

            items_prices = {
                'value': int(metrics['items_prices']['number_items_outliers']),
                'outlier_check': get_outlier_color(metrics['items_prices']['is_outlier']),
                'items': items_list,
                'total_items': int(metrics['items_prices']['total_items']),
                'maximum_expected': int(metrics['items_prices']['maximum_expected'])
            }

        result['precos_acima_media'] = items_prices


        project_indicators = [
            {
                'name': 'complexidade_financeira',
                'value': result['easiness']['value'],
                'metrics': [
                    {
                        'name': 'itens_orcamentarios',
                        'value': result['itens_orcamentarios']['total_items'],
                        'reason': 'any reason',
                        'outlier_check': result['itens_orcamentarios']['outlier_check'],
                        'interval_start': result['itens_orcamentarios']['interval_start'],
                        'interval_end': result['itens_orcamentarios']['interval_end'],
                        'bar': set_width_bar(result['itens_orcamentarios']['interval_start'],
                                            result['itens_orcamentarios']['interval_end'],
                                            result['itens_orcamentarios']['total_items'])

                    },
                    {
                        'name': 'itens_orcamentarios_fora_do_comum',
                        'value': result['itens_orcamentarios_fora_do_comum']['value'],
                        'reason': 'any reason',
                        'outlier_check': result['itens_orcamentarios_fora_do_comum']['outlier_check'],
                        'mean': result['itens_orcamentarios_fora_do_comum']['mean'],
                        'std': result['itens_orcamentarios_fora_do_comum']['std'],
                        'expected_itens': result['itens_orcamentarios_fora_do_comum']['uncommon_items'],
                        'missing_itens': result['itens_orcamentarios_fora_do_comum']['common_items_not_in_project']
                    },
                    {
                        'name': 'comprovantes_pagamento',
                        'value': result['comprovantes_pagamento']['total_receipts'],
                        'reason': 'any reason',
                        'outlier_check': result['comprovantes_pagamento']['outlier_check'],
                        'maximum_expected_in_segment': result['comprovantes_pagamento']['maximum_expected_in_segment']
                    },
                    {
                        'name': 'precos_acima_media',
                        'reason': 'any reason',
                        'value': result['precos_acima_media']['value'],
                        'outlier_check': result['precos_acima_media']['outlier_check'],
                        'items': result['precos_acima_media']['items'],
                        'total_items': result['precos_acima_media']['total_items'],
                        'maximum_expected': result['precos_acima_media']['maximum_expected']
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
                        'value': len(result['projetos_mesmo_proponente']['submitted_projects']),
                        'reason': 'any reason',
                        'outlier_check': result['projetos_mesmo_proponente']['outlier_check'],
                        'proponent_projects': result['projetos_mesmo_proponente']['submitted_projects'],
                    },
                    {
                        'name': 'novos_fornecedores',
                        'value': result['novos_fornecedores']['new_providers_quantity'],
                        'reason': 'any reason',
                        'providers': result['novos_fornecedores']['new_providers_list'],
                        'new_providers_percentage': result['novos_fornecedores']['new_providers_percentage'],
                        'segment_average_percentage': result['novos_fornecedores']['segment_average_percentage'],
                        'outlier_check': result['novos_fornecedores']['outlier_check'],
                        'all_projects_average_percentage': result['novos_fornecedores']['all_projects_average_percentage']
                    },
                    {
                        'name': 'valor_aprovado',
                        'value': result['valor_aprovado']['value'],
                        'reason': 'any reason',
                        'outlier_check': result['valor_aprovado']['outlier_check'],
                        'maximum_expected_funds': result['valor_aprovado']['maximum_expected_funds']
                    }
                ]
            },
        ]
        project_feedback_possibilities = ['Muito simples',
                                'Simples', 'Normal', 'Complexo', 'Muito complexo']

        string_pronac = "{:06}".format(int(pronac))

        project_information = {
            'project': {
                'name': project.name,
                'pronac': string_pronac
            },
            'user': {
                'name': user.name,
                'email': user.email
            },
            'project_indicators': project_indicators,
            'project_feedback_possibilities': project_feedback_possibilities,
        }

        return JsonResponse(project_information)

class SendMetricFeedbackView(APIView):
    """
    A view that receives a single metric feedback
    """
    renderer_classes = (JSONRenderer, )
    @csrf_exempt
    def post(self, request, format=None):

        return JsonResponse(request.content)

class SendProjectFeedbackView(APIView):
    """
    A view that receives a single metric feedback
    """
    renderer_classes = (JSONRenderer, )
    @csrf_exempt
    def post(self, request, format=None):

        return JsonResponse(request.content)