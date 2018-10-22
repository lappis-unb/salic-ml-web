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
from indicators.models import Entity, Indicator, Metric, User, MetricFeedback, ProjectFeedback
from django.shortcuts import get_object_or_404
from indicators.indicators_requests import http_financial_metrics_instance

def fetch_entity(pronac):
    string_pronac = "{:06}".format(pronac)
    # project = get_object_or_404(Entity, pronac=pronac)
    try:
        project = Entity.objects.get(pronac=pronac)
    except:
        # project_query = "SELECT CONCAT(AnoProjeto, Sequencial), NomeProjeto \
        # FROM SAC.dbo.Projetos WHERE CONCAT(AnoProjeto, Sequencial) = '{0}'".format(string_pronac)
        # project_raw_data = make_query_from_db(project_query)
        # project_data = {
        #         'pronac': project_raw_data[0][0],
        #         'name': project_raw_data[0][1]
        # }
        """
        project_data = {
            'pronac': pronac,
            'name': 'Mock'
        }

        info = submitted_projects_info.get_projects_name([string_pronac])

        project_data = {
            'pronac': pronac,
            'name': info[string_pronac]
        }
        """
        #project = Entity.objects.create(pronac=int(project_data['pronac']), name=project_data['name'])
        project = None

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
        'interval_start': min_interval, 
        'interval_end': max_interval,
        'interval': (max_interval-min_interval)
    }

def calculate_search_cutoff(keyword_len):
    if keyword_len >= 6:
        cutoff = 0.3
    else:
        cutoff = keyword_len * 0.05
    
    return cutoff

def paginate_projects(full_list, projects_per_page):

    full_list.sort(key=lambda x : x["complexity"], reverse=True)
    paginated_list = [full_list[i:i+projects_per_page] for i in range(0, len(full_list), projects_per_page)]
    
    return paginated_list

def get_page(paginated_list, page):
    try:
        required_list = paginated_list[page - 1]
    except:
        required_list = []

    return required_list

def reason_text_formatter(value, expected_max_value, prefix="", descriptor="", to_show_value=None, to_show_expected_max_value=None):
    # "O valor de {0}{1}{2} está abaixo/acima do valor médio de {3}{4} {5}"
    if to_show_value is None:
        to_show_value = value
    
    if to_show_expected_max_value is None:
        to_show_expected_max_value = expected_max_value

    if value > expected_max_value:
        reason_text = "O valor de {0}{1}{2} está acima do valor máximo esperado de {3}{4}{5}".format(
            prefix, 
            to_show_value, 
            descriptor, 
            prefix, 
            to_show_expected_max_value, 
            descriptor
            )
    elif value < expected_max_value:
        reason_text = "O valor de {0}{1}{2} está abaixo do valor máximo esperado de {3}{4}{5}".format(
            prefix, 
            to_show_value, 
            descriptor, 
            prefix, 
            to_show_expected_max_value, 
            descriptor
            )
    else:
        reason_text = "O valor de {0}{1}{2} está correspondente ao valor máximo esperado de {3}{4}{5}".format(
            prefix, 
            to_show_value, 
            descriptor, 
            prefix, 
            to_show_expected_max_value, 
            descriptor
            )

    return reason_text

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
                "name": "Indie 2009 - Mostra de Cinema Mundial", "analist": "Florentina"},
            {"pronac": "153833", "complexity": 75,
                "name": "TRES SOMBREROS DE COPA", "analist": "Chimbinha"},
            {"pronac": "160443", "complexity": 95,
                "name": "SERGIO REIS – CORAÇÃO ESTRADEIRO", "analist": "Cláudia Leitte"},
            {"pronac": "118593", "complexity": 15,
                "name": "ÁGUIA  CARNAVAL 2012: TROPICÁLIA! O MOVIMENTO QUE NÃO TERMINOU", "analist": "Ferdinando"},
            {"pronac": "161533", "complexity": 5,
                "name": "“Livro sobre Serafim Derenzi” (título provisório)", "analist": "Modelo"},
            {"pronac": "171372", "complexity": 5,
                "name": "“Paisagismo Brasileiro, Roberto Burle Marx e Haruyoshi Ono – 60 anos de história”.", "analist": "Modelo"},
            {"pronac": "92739", "complexity": 5,
                "name": "Circulação de oficinas e shows - Claudia Cimbleris", "analist": "Modelo"},
            {"pronac": "90021", "complexity": 25,
                "name": "Indie 2009 - Mostra de Cinema Mundial", "analist": "Florentina"},
            {"pronac": "153833", "complexity": 75,
                "name": "TRES SOMBREROS DE COPA", "analist": "Chimbinha"},
            {"pronac": "160443", "complexity": 95,
                "name": "SERGIO REIS – CORAÇÃO ESTRADEIRO", "analist": "Cláudia Leitte"},
            {"pronac": "118593", "complexity": 15,
                "name": "ÁGUIA  CARNAVAL 2012: TROPICÁLIA! O MOVIMENTO QUE NÃO TERMINOU", "analist": "Ferdinando"},
            {"pronac": "161533", "complexity": 5,
                "name": "“Livro sobre Serafim Derenzi” (título provisório)", "analist": "Modelo"},
            {"pronac": "171372", "complexity": 5,
                "name": "“Paisagismo Brasileiro, Roberto Burle Marx e Haruyoshi Ono – 60 anos de história”.", "analist": "Modelo"},
            {"pronac": "92739", "complexity": 5,
                "name": "Circulação de oficinas e shows - Claudia Cimbleris", "analist": "Modelo"},
            ]

        projects_bk = projects
        
        for i in range(100):
            projects = projects + projects_bk

        paginated_list = paginate_projects(projects, request.GET.get('per_page'))

        page = request.GET.get('page')
        
        projects_list = get_page(paginated_list, int(page))

        # content = {'projects': projects_list, 'last_page':len(paginated_list)}
        
        next_page_index = int(page) + 1

        if next_page_index > len(paginated_list):
            next_page = None
        else:
            next_page = '/indicators/projects/{0}'.format(next_page_index)

        prev_page_index = int(kwargs['page']) - 1

        if prev_page_index < 1:
            prev_page = None
        else:
            prev_page = '/indicators/projects/{0}'.format(prev_page_index)

        content = {
            'total': len(projects),
            'per_page': 10,
            'current_page': int(page),
            'last_page': len(paginated_list),
            'next_page_url': next_page,
            'prev_page_url': prev_page,
            'from': 1,
            'to': len(paginated_list),
            'data': projects_list
        }

        return JsonResponse(content)

class SearchProjectView(APIView):
    """
    Busca todos os projetos. Como retorno tem se como resultado uma lista paginada com todos os projetos ordenados de forma decrescente à complexidade do projeto.

    Abaixo acompanha respectivamente um exemplo de como obter uma lista de projetos contida em uma determinada página, como limitar a quantidade de projetos por página e como filtrar a lista de projetos pelo PRONAC.
    ```
        https://salicml.lappis.rocks/projetos?page=3
        https://salicml.lappis.rocks/projetos?per_page=2
        https://salicml.lappis.rocks/projetos?filter=000001

    ```
    """
    renderer_classes = (JSONRenderer, )
    @csrf_exempt
    def get(self, request, format=None, **kwargs):
        
        try:
            projects = projects_to_analyse(request)
        except:
            projects = [
            {"pronac": "90021", "complexity": 25,
                "name": "Indie 2009 - Mostra de Cinema Mundial", "analist": ""},
            {"pronac": "153833", "complexity": 75,
                "name": "TRES SOMBREROS DE COPA", "analist": ""},
            {"pronac": "160443", "complexity": 95,
                "name": "SERGIO REIS – CORAÇÃO ESTRADEIRO", "analist": ""},
            {"pronac": "118593", "complexity": 15,
                "name": "ÁGUIA  CARNAVAL 2012: TROPICÁLIA! O MOVIMENTO QUE NÃO TERMINOU", "analist": ""},
            {"pronac": "161533", "complexity": 5,
                "name": "“Livro sobre Serafim Derenzi” (título provisório)", "analist": ""},
            {"pronac": "171372", "complexity": 5,
                "name": "“Paisagismo Brasileiro, Roberto Burle Marx e Haruyoshi Ono – 60 anos de história”.", "analist": ""},
            {"pronac": "92739", "complexity": 5,
                "name": "Circulação de oficinas e shows - Claudia Cimbleris", "analist": ""},
            {"pronac": "90021", "complexity": 25,
                "name": "Indie 2009 - Mostra de Cinema Mundial", "analist": ""},
            {"pronac": "153833", "complexity": 75,
                "name": "TRES SOMBREROS DE COPA", "analist": ""},
            {"pronac": "160443", "complexity": 95,
                "name": "SERGIO REIS – CORAÇÃO ESTRADEIRO", "analist": ""},
            {"pronac": "118593", "complexity": 15,
                "name": "ÁGUIA  CARNAVAL 2012: TROPICÁLIA! O MOVIMENTO QUE NÃO TERMINOU", "analist": ""},
            {"pronac": "161533", "complexity": 5,
                "name": "“Livro sobre Serafim Derenzi” (título provisório)", "analist": ""},
            {"pronac": "171372", "complexity": 5,
                "name": "“Paisagismo Brasileiro, Roberto Burle Marx e Haruyoshi Ono – 60 anos de história”.", "analist": ""},
            {"pronac": "92739", "complexity": 5,
                "name": "Circulação de oficinas e shows - Claudia Cimbleris", "analist": ""},
            ]

        projects_processed = [{
            "pronac": project['pronac'], 
            "complexity": project['complexity'],
            "name": project['name'],
            "analist": project['analist']
        } for project in projects]

        keyword = request.GET.get('filter')

        if keyword is not None:
            # NAME_CUTOFF = calculate_search_cutoff(len(keyword))

            # name_matches_list = difflib.get_close_matches(
            #     keyword.lower(), 
            #     [project['name_lowered'] for project in projects_processed], 
            #     n=len(projects), 
            #     cutoff=NAME_CUTOFF
            # )

            pronac_matches_list = difflib.get_close_matches(
                keyword, 
                [project['pronac'] for project in projects], 
                n=len(projects), 
                cutoff=1
            )

            result_list = [project for project in projects_processed if project['pronac'] in pronac_matches_list]
        else:
            result_list = projects

        projects_per_page = request.GET.get('per_page')
        
        if projects_per_page is None:
            projects_per_page = 15
        else: 
            projects_per_page = int(projects_per_page)

        paginated_list = paginate_projects(result_list, projects_per_page)

        page = request.GET.get('page')

        if page is None:
            page = "1"

        projects_list = get_page(paginated_list, int(page))
        
        # content = {'projects': projects_list, 'last_page': len(paginated_list)}

        """next_page_index = int(page) + 1

        if next_page_index > len(paginated_list):
            next_page = None
        else:
            next_page = '/indicators/projects/search/any/{0}'.format(next_page_index)

        prev_page_index = int(kwargs['page']) - 1

        if prev_page_index < 1:
            prev_page = None
        else:
            prev_page = '/indicators/projects/search/any/{0}'.format(prev_page_index)
        """

        content = {
            'total': len(projects),
            'per_page': projects_per_page,
            'current_page': int(page),
            #'last_page': len(paginated_list),
            #'next_page_url': next_page,
            #'prev_page_url': prev_page,
            'begin_page': 1,
            'end_page': len(paginated_list),
            'data': projects_list
        }
        
        return JsonResponse(content)

class ProjectInfoView(APIView):
    """
    Busca informações de determinado projeto por meio do seu PRONAC
    """
    renderer_classes = (JSONRenderer, )
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    # def post(self, request, format=None, **kwargs):
    def get(self, request, format=None, **kwargs):
        # user_data = json.loads(request.body)

        # user_email = user_data['email'] + '@cultura.gov.br'
        # try:
        #     user = User.objects.get(email=user_email)
        # except:
        #     user_name = user_data['name']

        #     user = User.objects.create(email=user_email, name=user_name)

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

        # total_metrics = 

        total_metrics = financial_metrics.get_metrics("{:06}".format(int(pronac)))

        for metric_name in metrics_list:
            try:
                metrics[metric_name] = total_metrics[metric_name]
            except:
                if metric_name is '':
                    metrics[metric_name] = total_metrics[metric_name]
                else:
                    metrics[metric_name] = None

        # metrics['items'] = http_financial_metrics_instance.number_of_items(pronac="090105")

        result = {
            'pronac': pronac,
            'received_metrics': metrics
        }

        # return HttpResponse(str(result))
        #complexidade_financeira
        # financial_complexity_indicator = register_project_indicator(int(pronac), 'complexidade_financeira', 0)

        easiness = {
            'value': 1,
        }

        if metrics['easiness'] is not None:
            complexity = int((1 - metrics['easiness']['easiness']) * 100) # Converts easiness to complexity
            
            if complexity is 0:
                complexity = 1

            easiness = {
                'value': complexity
            }

        result['easiness'] = easiness
        # return HttpResponse(str(result))

        """
        # itens_orcamentarios
        items = {
                'total_items': 0,
                'interval_start': 0,
                'interval_end': 0,
                'reason': "Não há registros desta métrica para este projeto",
                'outlier_check': get_outlier_color(False)
        }

        if metrics['items'] is not None:
            # items_interval = get_items_interval(metrics['items']['mean'], metrics['items']['std'])
            items = {
                'total_items': int(metrics['items']['number_of_items']),
                'interval_start': int(metrics['items']['minimum_expected']),
                'interval_end': int(metrics['items']['maximum_expected']),
                'reason': reason_text_formatter(int(metrics['items']['number_of_items']), int(metrics['items']['maximum_expected']), descriptor=" item(ns)"),
                'outlier_check': get_outlier_color(metrics['items']['is_outlier'])
            }

        itens_orcamentarios = register_project_metric('itens_orcamentarios', items['total_items'], str(items), financial_complexity_indicator.name, int(pronac))
        items['metric_id'] = itens_orcamentarios.id

        result['itens_orcamentarios'] = items

        # valor_captado
        raised_funds = {
            'value': float_to_money(0.0),
            'float_value': 0.0,
            'reason': "Não há registros desta métrica para este projeto",
            'maximum_expected_value': float_to_money(0.0),
            'outlier_check': get_outlier_color(False)
        }

        if metrics['raised_funds'] is not None:
            raised_funds = {
                'value': float_to_money(metrics['raised_funds']['total_raised_funds']),
                'float_value': metrics['raised_funds']['total_raised_funds'],
                'reason': reason_text_formatter(
                    metrics['raised_funds']['total_raised_funds'], 
                    metrics['raised_funds']['maximum_expected_funds'], 
                    to_show_value=float_to_money(metrics['raised_funds']['total_raised_funds']),
                    to_show_expected_max_value=float_to_money(metrics['raised_funds']['maximum_expected_funds'])
                    ),
                'maximum_expected_value': float_to_money(metrics['raised_funds']['maximum_expected_funds']),
                'outlier_check': get_outlier_color(metrics['raised_funds']['is_outlier'])
            }

        valor_captado = register_project_metric('valor_captado', raised_funds['float_value'], str(raised_funds), financial_complexity_indicator.name, int(pronac))        
        raised_funds['metric_id'] = valor_captado.id

        result['valor_captado'] = raised_funds

        # valor_comprovado
        verified_funds = {
            'value': float_to_money(0.0),
            'float_value': 0.0,
            'maximum_expected_value': float_to_money(0.0),
            'outlier_check': get_outlier_color(False),
            'reason': "Não há registros desta métrica para este projeto"
        }

        if metrics['verified_funds'] is not None:
            verified_funds = {
                'value': float_to_money(metrics['verified_funds']['total_verified_funds']),
                'float_value': metrics['verified_funds']['total_verified_funds'],
                'maximum_expected_value': float_to_money(metrics['verified_funds']['maximum_expected_funds']),
                'outlier_check': get_outlier_color(metrics['verified_funds']['is_outlier']),
                'reason': reason_text_formatter(
                    metrics['verified_funds']['total_verified_funds'], 
                    metrics['verified_funds']['maximum_expected_funds'], 
                    to_show_value=float_to_money(metrics['verified_funds']['total_verified_funds']),
                    to_show_expected_max_value=float_to_money(metrics['verified_funds']['maximum_expected_funds'])
                    ),
            }

        valor_comprovado = register_project_metric('valor_comprovado', verified_funds['float_value'], str(verified_funds), financial_complexity_indicator.name, int(pronac))
        verified_funds['metric_id'] = valor_comprovado.id

        result['valor_comprovado'] = verified_funds

        # valor_aprovado
        approved_funds = {
            'value': float_to_money(0),
            'float_value': 0.0,
            'maximum_expected_funds': float_to_money(0.0),
            'outlier_check': get_outlier_color(False),
            'reason': "Não há registros desta métrica para este projeto"
        }

        if metrics['approved_funds'] is not None:
            approved_funds = {
                'value': float_to_money(metrics['approved_funds']['total_approved_funds']),
                'float_value': metrics['approved_funds']['total_approved_funds'],
                'maximum_expected_funds': float_to_money(metrics['approved_funds']['maximum_expected_funds']),
                'outlier_check': get_outlier_color(metrics['approved_funds']['is_outlier']),
                'reason': reason_text_formatter(
                    metrics['approved_funds']['total_approved_funds'],
                    metrics['approved_funds']['maximum_expected_funds'], 
                    to_show_value=float_to_money(metrics['approved_funds']['total_approved_funds']),
                    to_show_expected_max_value=float_to_money(metrics['approved_funds']['maximum_expected_funds'])
                    ),
            }
        
        valor_aprovado = register_project_metric('valor_aprovado', approved_funds['float_value'], str(approved_funds), financial_complexity_indicator.name, int(pronac))
        approved_funds['metric_id'] = valor_aprovado.id

        result['valor_aprovado'] = approved_funds

        # itens_orcamentarios_fora_do_comum
        common_items_ratio = {
            'outlier_check': get_outlier_color(False),
            'value': '0.0%',
            'float_value': 0.0,
            'mean': 0.0,
            'std': 0.0,
            'uncommon_items': [],
            'common_items_not_in_project': [],
            'reason': "Não há registros desta métrica para este projeto"
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
                'value': "{0:.2f}%".format(100 - metrics['common_items_ratio']['value'] * 100),
                'float_value': (100 - metrics['common_items_ratio']['value'] * 100),
                'mean': metrics['common_items_ratio']['mean'],
                'std': metrics['common_items_ratio']['std'],
                'uncommon_items': uncommon_items_list,
                'reason': reason_text_formatter(
                    (100 - metrics['common_items_ratio']['value'] * 100), 
                    metrics['common_items_ratio']['mean'] * 100, 
                    to_show_value="{0:.2f}%".format(100 - metrics['common_items_ratio']['value'] * 100),
                    to_show_expected_max_value="{0:.2f}%".format(100 - metrics['common_items_ratio']['mean'] * 100)
                    ),
                'common_items_not_in_project': common_items_not_in_project_list
            }

        itens_orcamentarios_fora_do_comum = register_project_metric('itens_orcamentarios_fora_do_comum', common_items_ratio['float_value'], "", financial_complexity_indicator.name, int(pronac))
        common_items_ratio['metric_id'] = itens_orcamentarios_fora_do_comum.id

        result['itens_orcamentarios_fora_do_comum'] = common_items_ratio

        # comprovantes_pagamento
        total_receipts = {
            'outlier_check': get_outlier_color(False),
            'total_receipts': 0,
            'maximum_expected_in_segment': 0,
            'reason': "Não há registros desta métrica para este projeto"
        }

        if metrics['total_receipts'] is not None:
            total_receipts = {
                'outlier_check': get_outlier_color(metrics['total_receipts']['is_outlier']),
                'total_receipts': int(metrics['total_receipts']['total_receipts']),
                'maximum_expected_in_segment': int(metrics['total_receipts']['maximum_expected_in_segment']),
                'reason': reason_text_formatter(int(metrics['total_receipts']['total_receipts']), int(metrics['total_receipts']['maximum_expected_in_segment']), descriptor=" item(ns)")
            }

        comprovantes_pagamento = register_project_metric('comprovantes_pagamento', total_receipts['total_receipts'], str(total_receipts), financial_complexity_indicator.name, int(pronac))
        total_receipts['metric_id'] = comprovantes_pagamento.id

        result['comprovantes_pagamento'] = total_receipts

        # novos_fornecedores
        new_providers = {
            'new_providers_list': [],
            'new_providers_quantity': 0,
            'new_providers_percentage': "0.0%",
            'segment_average_percentage': 0,
            'outlier_check': get_outlier_color(False),
            'all_projects_average_percentage': 0,
            'reason': "Não há registros desta métrica para este projeto"
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
                'new_providers_percentage': "{0:.2f}%".format(metrics['new_providers']['new_providers_percentage']),
                'segment_average_percentage': metrics['new_providers']['segment_average_percentage'],
                'outlier_check': get_outlier_color(metrics['new_providers']['is_outlier']),
                'all_projects_average_percentage': metrics['new_providers']['all_projects_average_percentage'],
                'reason': reason_text_formatter(
                    metrics['new_providers']['new_providers_percentage'], 
                    metrics['new_providers']['all_projects_average_percentage'], 
                    to_show_value="{0:.2f}%".format(metrics['new_providers']['new_providers_percentage'] * 100),
                    to_show_expected_max_value="{0:.2f}%".format(metrics['new_providers']['all_projects_average_percentage'] * 100)
                    )
            }

        novos_fornecedores = register_project_metric('novos_fornecedores', new_providers['new_providers_quantity'], "", financial_complexity_indicator.name, int(pronac))
        new_providers['metric_id'] = novos_fornecedores.id

        result['novos_fornecedores'] = new_providers

        # projetos_mesmo_proponente
        proponent_projects = {
            'cnpj_cpf': '',
            'submitted_projects': [],
            'analyzed_projects': [],
            'outlier_check': get_outlier_color(False),
            'reason': "Não há registros desta métrica para este projeto"
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
                'outlier_check': get_outlier_color(False),
                'reason': ""
            }

        projetos_mesmo_proponente = register_project_metric('projetos_mesmo_proponente', len(proponent_projects['submitted_projects']), "", financial_complexity_indicator.name, int(pronac))
        proponent_projects['metric_id'] = projetos_mesmo_proponente.id

        result['projetos_mesmo_proponente'] = proponent_projects

        # precos_acima_media
        items_prices = {
            'value': 0,
            'outlier_check': get_outlier_color(False),
            'items': [],
            'total_items': 0,
            'maximum_expected': 0,
            'reason': "Não há registros desta métrica para este projeto"
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
                'maximum_expected': int(metrics['items_prices']['maximum_expected']),
                'reason': reason_text_formatter(int(metrics['items_prices']['number_items_outliers']), int(metrics['items_prices']['maximum_expected']), descriptor=" item(ns)")
            }

        precos_acima_media = register_project_metric('precos_acima_media', items_prices['value'], "", financial_complexity_indicator.name, int(pronac))
        items_prices['metric_id'] = precos_acima_media.id

        result['precos_acima_media'] = items_prices
        """
        """
        project_indicators = [
            {
                'name': 'complexidade_financeira',
                'value': result['easiness']['value'],
                'metrics': [
                    {
                        'name': 'itens_orcamentarios',
                        'name_title': 'Itens orçamentários',
                        'type': 'bar',
                        'helper_text':'Compara a quantidade de itens deste projeto com a quantidade mais comum de itens em projetos do mesmo segmento',
                        'metric_id': result['itens_orcamentarios']['metric_id'],
                        'value': result['itens_orcamentarios']['total_items'],
                        'reason': result['itens_orcamentarios']['reason'],
                        'outlier_check': result['itens_orcamentarios']['outlier_check'],
                        'interval_start': result['itens_orcamentarios']['interval_start'],
                        'interval_end': result['itens_orcamentarios']['interval_end'],
                        'bar': set_width_bar(result['itens_orcamentarios']['interval_start'],
                                            result['itens_orcamentarios']['interval_end'],
                                            result['itens_orcamentarios']['total_items'])

                    },
                    {
                        'name': 'itens_orcamentarios_fora_do_comum',
                        'name_title': 'Itens orçamentários fora do comum',
                        'type': 'items-list',
                        'helper_text':'Indica os itens orçamentários deste projeto que não estão entre os mais comuns do segmento. \
                        Também lista os itens que aparecem frequentemente em projetos do segmento, mas que não aparecem neste projeto',
                        'metric_id': result['itens_orcamentarios_fora_do_comum']['metric_id'],
                        'value': result['itens_orcamentarios_fora_do_comum']['value'],
                        'reason': result['itens_orcamentarios_fora_do_comum']['reason'],
                        'outlier_check': result['itens_orcamentarios_fora_do_comum']['outlier_check'],
                        'mean': result['itens_orcamentarios_fora_do_comum']['mean'],
                        'std': result['itens_orcamentarios_fora_do_comum']['std'],
                        'uncommon_items': result['itens_orcamentarios_fora_do_comum']['uncommon_items'],
                        'common_items_not_in_project': result['itens_orcamentarios_fora_do_comum']['common_items_not_in_project']
                    },
                    {
                        'name': 'comprovantes_pagamento',
                        'name_title': 'Comprovantes de pagamento',
                        'type': 'bar',
                        'helper_text':'Compara a quantidade de comprovantes deste projeto com a quantidade mais comum de comprovantes em projetos do mesmo segmento',
                        'metric_id': result['comprovantes_pagamento']['metric_id'],
                        'value': result['comprovantes_pagamento']['total_receipts'],
                        'reason': result['comprovantes_pagamento']['reason'],
                        'outlier_check': result['comprovantes_pagamento']['outlier_check'],
                        'maximum_expected_in_segment': result['comprovantes_pagamento']['maximum_expected_in_segment']
                    },
                    {
                        'name': 'precos_acima_media',
                        'name_title': 'Preços acima da média',
                        'type': 'bar',
                        'helper_text':'Verifica a porcentagem de itens com valor acima da mediana histórica neste projeto \
                        e compara com a porcentagem mais frequente de itens acima da mediana em projetos do mesmo segmento',
                        'metric_id': result['precos_acima_media']['metric_id'],
                        'reason': result['precos_acima_media']['reason'],
                        'value': result['precos_acima_media']['value'],
                        'outlier_check': result['precos_acima_media']['outlier_check'],
                        'items': result['precos_acima_media']['items'],
                        'total_items': result['precos_acima_media']['total_items'],
                        'maximum_expected': result['precos_acima_media']['maximum_expected']
                    },
                    {
                        'name': 'valor_comprovado',
                        'name_title': 'Valor comprovado',
                        'type': 'bar',
                        'helper_text':'Compara o valor comprovado neste projeto com o valor mais frequentemente comprovado em projetos do mesmo segmento',
                        'metric_id': result['valor_comprovado']['metric_id'],
                        'value': result['valor_comprovado']['value'],
                        'reason': result['valor_comprovado']['reason'],
                        'outlier_check': result['valor_comprovado']['outlier_check']
                    },
                    {
                        'name': 'valor_captado',
                        'name_title': 'Valor captado',
                        'type': 'bar',
                        'helper_text':'Compara o valor captado neste projeto com o valor mais frequentemente captado em projetos do mesmo segmento',
                        'metric_id': result['valor_captado']['metric_id'],
                        'value': result['valor_captado']['value'],
                        'reason': result['valor_captado']['reason'],
                        'outlier_check': result['valor_captado']['outlier_check']
                    },
                    # {
                    #     'name': 'mudancas_planilha_orcamentaria',
                    #     'value': '70',
                    #     'reason': 'any reason',
                    #     'outlier_check': '',
                    #     'document_version': 14,
                    # },
                    {
                        'name': 'projetos_mesmo_proponente',
                        'name_title': 'Projetos do mesmo proponente',
                        'type': 'proponents-list',
                        'helper_text':'Indica os projetos que o proponente já executou no passado.',
                        'metric_id': result['projetos_mesmo_proponente']['metric_id'],
                        'value': len(result['projetos_mesmo_proponente']['submitted_projects']),
                        'reason': result['projetos_mesmo_proponente']['reason'],
                        'outlier_check': result['projetos_mesmo_proponente']['outlier_check'],
                        'proponent_projects': result['projetos_mesmo_proponente']['submitted_projects'],
                    },
                    {
                        'name': 'novos_fornecedores',
                        'name_title': 'Novos fornecedores',
                        'type': 'providers-list',
                        'helper_text':' Indica a proporção de fornecedores que nunca participaram de projetos de incentivo antes em \
                        relação ao total de fornecedores envolvidos com o projeto.Também lista os itens orçamentários dos novos fornecedores.',
                        'metric_id': result['novos_fornecedores']['metric_id'],
                        'value': result['novos_fornecedores']['new_providers_quantity'],
                        'reason': result['novos_fornecedores']['reason'],
                        'providers': result['novos_fornecedores']['new_providers_list'],
                        'new_providers_percentage': result['novos_fornecedores']['new_providers_percentage'],
                        'segment_average_percentage': result['novos_fornecedores']['segment_average_percentage'],
                        'outlier_check': result['novos_fornecedores']['outlier_check'],
                        'all_projects_average_percentage': result['novos_fornecedores']['all_projects_average_percentage']
                    },
                    {
                        'name': 'valor_aprovado',
                        'name_title': 'Valor aprovado',
                        'type': 'bar',
                        'helper_text':'Compara o valor aprovado para este projeto com o valor mais frequentemente aprovado em projetos do mesmo segmento',
                        'metric_id': result['valor_aprovado']['metric_id'],
                        'value': result['valor_aprovado']['value'],
                        'reason': result['valor_aprovado']['reason'],
                        'outlier_check': result['valor_aprovado']['outlier_check'],
                        'maximum_expected_funds': result['valor_aprovado']['maximum_expected_funds']
                    }
                ]
            },
        ]
       """ 

        indicators = [
            {
                'name': 'complexidade_financeira',
                'complexity': result['easiness']['value'],
            }
        ]

        string_pronac = "{:06}".format(int(pronac))

        if(project is not None):
            project_information = {
                'name': project.name,
                'pronac': string_pronac,
                'indicators': indicators,
            }
        else: project_information = {} 

        return JsonResponse(project_information)

class SendMetricFeedbackView(APIView):
    """
    A view that receives a single metric feedback
    """
    renderer_classes = (JSONRenderer, )
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, format=None):
        request_data = json.loads(request.body)

        user_email = "{0}@cultura.gov.br".format(request_data['user_email'])

        user = get_object_or_404(User, email=user_email)
        metric = get_object_or_404(Metric, id=int(request_data['metric_id']))
        metric_feedback_rating = int(request_data['metric_feedback_rating'])
        metric_feedback_text = request_data['metric_feedback_text']

        metric_query = MetricFeedback.objects.filter(
            user=user,
            metric=metric
        )

        if len(metric_query) is 0:
            # Creates metric
            saved_metric_feedback = MetricFeedback.objects.create(
                user=user,
                metric=metric,
                grade=metric_feedback_rating,
                reason=metric_feedback_text
            )
        else:
            # Updates metric
            saved_metric_feedback = metric_query[0]
            saved_metric_feedback.grade = metric_feedback_rating
            saved_metric_feedback.reason = metric_feedback_text
            saved_metric_feedback.save()

        request_response = {
            'feedback_id': saved_metric_feedback.id,
            'feedback_grade': saved_metric_feedback.grade,
            'feedback_reason': saved_metric_feedback.reason
        }       

        return JsonResponse(request_response)

class SendProjectFeedbackView(APIView):
    """
    A view that receives a single metric feedback
    """
    renderer_classes = (JSONRenderer, )
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, format=None):
        request_data = json.loads(request.body)

        user_email = "{0}@cultura.gov.br".format(request_data['user_email'])

        user = get_object_or_404(User, email=user_email)
        entity = get_object_or_404(Entity, pronac=int(request_data['pronac']))
        project_feedback_grade = int(request_data['project_feedback_grade'])

        project_query = ProjectFeedback.objects.filter(
            user=user, 
            entity=entity
        )

        if len(project_query) is 0:
            # Creates
            saved_project_feedback = ProjectFeedback.objects.create(
                user=user, 
                entity=entity,
                grade=project_feedback_grade
            )
        else:
            # Updates
            saved_project_feedback = project_query[0]
            saved_project_feedback.grade = project_feedback_grade
            saved_project_feedback.save()
        

        request_response = {
            'feedback_id': saved_project_feedback.id,
            'feedback_grade': saved_project_feedback.grade,
        }    

        return JsonResponse(request_response)

class CreateSingleUserView(APIView):
    """
    A view that creates a single user if not created
    """
    renderer_classes = (JSONRenderer, )
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, format=None):
        user_data = json.loads(request.body)

        user_email =  '{0}@cultura.gov.br'.format(user_data['email'])

        user_query = User.objects.filter(email=user_email)

        if len(user_query) is 0:
            user_name = user_data['name']

            user = User.objects.create(email=user_email, name=user_name)
        else:
            user = user_query[0]

        user_response = {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }

        return JsonResponse(user_response)
