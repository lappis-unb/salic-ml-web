from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import generic
from django.http import JsonResponse
import json
import difflib
from indicators.financial_metrics_instance import financial_metrics, submitted_projects_info, fetch_project_complexity
from core.utils.get_project_info_from_pronac import GetProjectInfoFromPronac
from indicators.models import Entity, Indicator, Metric, User, MetricFeedback, ProjectFeedback
from django.shortcuts import get_object_or_404
from indicators.indicators_requests import http_financial_metrics_instance
from salic_db.utils import make_query_from_db

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

    # query = "SELECT TOP 2000 CONCAT(AnoProjeto, Sequencial), NomeProjeto, Analista \
    #          FROM SAC.dbo.Projetos WHERE DtFimExecucao < GETDATE() \
    #          AND Situacao NOT IN ({}) ORDER BY DtFimExecucao DESC".format(end_situations)

    query_result = make_query_from_db(query)

    filtered_data = [{'pronac': each[0],
                      'complexidade': int(fetch_project_complexity(int(each[0]))),
                      'nome': each[1],
                      'responsavel': each[2]}
                      for each in query_result]

    return filtered_data

# TODO Move fetch to correspondent class
def fetch_entity(pronac):
    string_pronac = "{:06}".format(pronac)
    try:
        project = Entity.objects.get(pronac=pronac)
    except:
        project_query = "SELECT CONCAT(AnoProjeto, Sequencial), NomeProjeto \
        FROM SAC.dbo.Projetos WHERE CONCAT(AnoProjeto, Sequencial) = '{0}'".format(string_pronac)
        project_raw_data = make_query_from_db(project_query)
        project_data = {
                'pronac': project_raw_data[0][0],
                'name': project_raw_data[0][1]
        }

        project = Entity.objects.create(pronac=int(project_data['pronac']), name=project_data['name'])

    return project

# TODO Improve float_to_money method name
def float_to_money(value):
    us_value = '{:,.2f}'.format(value)
    v_value = us_value.replace(',','v')
    c_value = v_value.replace('.',',')
    return c_value.replace('v','.')

def verify_outlier(is_outlier):
    if is_outlier:
        return False
    else:
        return True

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

    def paginate_projects(self, full_list, projects_per_page):
        full_list.sort(key=lambda x : x["complexidade"], reverse=True)
        paginated_list = [full_list[i:i+projects_per_page] for i in range(0, len(full_list), projects_per_page)]

        return paginated_list

    def get_page(self, paginated_list, page):
        try:
            required_list = paginated_list[page - 1]
        except:
            required_list = []

        return required_list

    def get_projects_per_page(self, projects_per_page):
        if projects_per_page is None:
            projects_per_page = 15
        else:
            projects_per_page = int(projects_per_page)
        
        return projects_per_page

    def get_next_or_prev_page(self, x, y):
        if prev_page_index < 1:
            prev_page = None
        else:
            prev_page = '/projetos?page={0}'.format(prev_page_index)

    def get_next_and_prev(self, paginated_list, page):
        next_page_index = int(page) + 1

        if next_page_index > paginated_list:
            next_page = None
        else:
            next_page = '/projetos?page={0}'.format(next_page_index)

        prev_page_index = int(page) - 1

        if prev_page_index < 1:
            prev_page = None
        else:
            prev_page = '/projetos?page={0}'.format(prev_page_index)

        return {'next': next_page, 'prev': prev_page }

    @csrf_exempt
    def get(self, request, format=None, **kwargs):

        try:
            projects = projects_to_analyse(request)
        except:
            projects = []

        projects_processed = [
            {
                "pronac": project['pronac'],
                "complexidade": project['complexidade'],
                "nome": project['nome'],
                "analista": project['responsavel']
            } for project in projects
        ]

        keyword = request.GET.get('filter')

        if keyword is not None:
            pronac_matches_list = difflib.get_close_matches(
                keyword,
                [project['pronac'] for project in projects],
                n=len(projects),
                cutoff=1
            )

            result_list = [project for project in projects_processed if project['pronac'] in pronac_matches_list]
        else:
            result_list = projects

        projects_per_page = self.get_projects_per_page(request.GET.get('per_page'))
        paginated_list = self.paginate_projects(result_list, projects_per_page)

        page = request.GET.get('page')

        if page is None: page = "1"
        
        projects_list = self.get_page(paginated_list, int(page))

        pages = self.get_next_and_prev(len(paginated_list), int(page))

        content = {
            'total': len(projects),
            'per_page': projects_per_page,
            'current_page': int(page),
            'last_page': len(paginated_list),
            'next_page_url': pages['next'],
            'prev_page_url': pages['prev'],
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

    def create_metric_template(self):
        template = {
            'value': 0,
            'is_outlier': False,
            'minimum_expected': 0,
            'maximum_expected': 0
        }
        return template

    def create_list_items(self, metrics, name, item_list_name):
        items_list = [] 
        for item_id in metrics[name][item_list_name]:
            items_list.append({
                'id': item_id,
                'name': metrics[name][item_list_name][item_id],
                'link': '#'
            })
        return items_list

    def get_itens_orcamentarios_fora_do_comum(self, metrics, pronac, financial_complexity_indicator_name):
        common_items_ratio = {
            'value': 0,
            'is_outlier': False
        }

        common_items_ratio['uncommon_items'] = []
        common_items_ratio['common_items_not_in_project'] = []
        name = 'common_items_ratio'
        metric_name = 'itens_orcamentarios_fora_do_comum'

        if metrics[name] is not None:
            common_items_not_in_project_list = []
            uncommon_items_list = []

            common_items_not_in_project_list = self.create_list_items(metrics, name, 'common_items_not_in_project')
            uncommon_items_list = self.create_list_items(metrics, name, 'uncommon_items')

            common_items_ratio = {
                'is_outlier': verify_outlier(metrics[name]['is_outlier']),
                'value': (100 - metrics[name]['value'] * 100),
                'uncommon_items': uncommon_items_list,
                'common_items_not_in_project': common_items_not_in_project_list
            }

        itens = register_project_metric(metric_name, common_items_ratio['value'], "", financial_complexity_indicator_name, pronac)
        common_items_ratio['metric_id'] = itens.id

        return common_items_ratio

    def get_novos_fornecedores(self, metrics, pronac, financial_complexity_indicator_name):
        name = 'new_providers'
        new_providers = {
            'value': 0,
            'is_outlier': verify_outlier(False),
            'new_providers_list': [],
        }

        if metrics[name] is not None:
            new_providers_list = []

            for provider_cnpj_cpf in metrics[name]['new_providers']:
                items_by_provider = []

                for item_id in metrics[name]['new_providers'][provider_cnpj_cpf]['items']:
                    items_by_provider.append({
                        'item_id': item_id,
                        'item_name': metrics[name]['new_providers'][provider_cnpj_cpf]['items'][item_id],
                        'item_link': '#'
                    })

                new_providers_list.append({
                    'provider_cnpj_cpf': provider_cnpj_cpf,
                    'provider_name': metrics[name]['new_providers'][provider_cnpj_cpf]['name'],
                    'provider_items': items_by_provider
                })

            new_providers = {
                'value': len(new_providers_list),
                'is_outlier': verify_outlier(metrics[name]['is_outlier']),
                'new_providers_list': new_providers_list,
            }

        novos_fornecedores = register_project_metric('novos_fornecedores', new_providers['value'], "", financial_complexity_indicator_name, pronac)
        new_providers['metric_id'] = novos_fornecedores.id

        return new_providers
 
    def get_projetos_mesmo_proponente(self, metrics, pronac, financial_complexity_indicator_name):
        proponent_projects = {
            'cnpj_cpf': '',
            'value': 0,
            'submitted_projects': [],
            'analyzed_projects': [],
            'is_outlier': verify_outlier(False),
        }

        name = 'proponent_projects'

        if metrics[name] is not None:
            submitted_projects_list = []
            analyzed_projects_list = []

            all_pronacs = metrics[name]['submitted_projects']['pronacs_of_this_proponent']

            projects_information = submitted_projects_info.get_projects_name(all_pronacs)
            for project_pronac in metrics[name]['submitted_projects']['pronacs_of_this_proponent']:
                submitted_projects_list.append({
                    'pronac': project_pronac,
                    'name': projects_information[project_pronac],
                    'link': '#'
                })

            for project_pronac in metrics[name]['analyzed_projects']['pronacs_of_this_proponent']:
                analyzed_projects_list.append({
                    'pronac': project_pronac,
                    'name': projects_information[project_pronac],
                    'link': '#'
                })

            proponent_projects = {
                'cnpj_cpf': metrics[name]['cnpj_cpf'],
                'value': len(submitted_projects_list),
                'submitted_projects': submitted_projects_list,
                'analyzed_projects': analyzed_projects_list,
                'is_outlier': verify_outlier(False),
            }

        projetos_mesmo_proponente = register_project_metric('projetos_mesmo_proponente', len(proponent_projects['submitted_projects']), "", financial_complexity_indicator_name, pronac)
        proponent_projects['metric_id'] = projetos_mesmo_proponente.id

        return proponent_projects


    def get_precos_acima_media(self, metrics, pronac, financial_complexity_indicator_name):
        name = 'items_prices'
        items_prices = {
            'value': 0,
            'is_outlier': verify_outlier(False),
            'items': [],
            'total_items': 0,
            'maximum_expected': 0,
        }

        if metrics[name] is not None:
            items_list = []
            items_list = self.create_list_items(metrics, 'items_prices', 'outlier_items')

            items_prices = {
                'value': int(metrics[name]['number_items_outliers']),
                'is_outlier': verify_outlier(metrics[name]['is_outlier']),
                'items': items_list,
                'total_items': int(metrics[name]['total_items']),
                'maximum_expected': int(metrics[name]['maximum_expected']),
            }

        precos_acima_media = register_project_metric('precos_acima_media', items_prices['value'], "", financial_complexity_indicator_name, pronac)
        items_prices['metric_id'] = precos_acima_media.id

        return items_prices


    def create_metric(self, metric_attributes, metrics, pronac, financial_complexity_indicator_name):
        metric = self.create_metric_template()
        name = metric_attributes['name']
        metric_name = metric_attributes['metric_name']

        if metrics[name] is not None:
            metric['value'] = metrics[name][metric_attributes['value']]
            metric['is_outlier'] = verify_outlier(metrics[name]['is_outlier'])
            metric['maximum_expected'] = metrics[name][metric_attributes['maximum_expected']]

        metric_id = register_project_metric(metric_name, metric['value'], str(metric), financial_complexity_indicator_name, pronac)
        metric['metric_id'] = metric_id.id

        return metric 

    def get(self, request, format=None, **kwargs):
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

        metrics['items'] = http_financial_metrics_instance.number_of_items(pronac="090105")

        result = {
            'pronac': pronac,
            'received_metrics': metrics
        }

        #complexidade_financeira
        financial_complexity_indicator = register_project_indicator(int(pronac), 'complexidade_financeira', 0)

        easiness = {
            'value': 1,
        }

        if metrics['easiness'] is not None:
            complexity = int((1 - metrics['easiness']['easiness']) * 100) # Converts easiness to complexity

            if complexity is 0:
                complexity = 1

            easiness = { 'value': complexity }

        result['easiness'] = easiness

        metric_attributes = [
            {
                'name': 'items',
                'metric_name': 'itens_orcamentarios',
                'value': 'number_of_items',
                'maximum_expected': 'maximum_expected'
            },
            {
                'name': 'total_receipts',
                'metric_name': 'comprovantes_pagamento',
                'value': 'total_receipts',
                'maximum_expected': 'maximum_expected_in_segment'
            },
            {
                'name': 'raised_funds',
                'metric_name': 'valor_captado',
                'value': 'total_raised_funds',
                'maximum_expected': 'maximum_expected_funds'
            },
            {
                'name': 'verified_funds',
                'metric_name': 'valor_comprovado',
                'value': 'total_verified_funds',
                'maximum_expected': 'maximum_expected_funds'
            },
            {
                'name': 'approved_funds',
                'metric_name': 'valor_aprovado',
                'value': 'total_approved_funds',
                'maximum_expected': 'maximum_expected_funds'
            }
        ]

        project_indicators = [
            {
                'name': 'complexidade_financeira',
                'value': result['easiness']['value'],
                'metrics': [
                    self.create_metric(metric_attributes[0], metrics, int(pronac), financial_complexity_indicator.name),
                    self.create_metric(metric_attributes[1], metrics, int(pronac), financial_complexity_indicator.name),
                    self.create_metric(metric_attributes[2], metrics, int(pronac), financial_complexity_indicator.name),
                    self.create_metric(metric_attributes[3], metrics, int(pronac), financial_complexity_indicator.name),
                    self.create_metric(metric_attributes[4], metrics, int(pronac), financial_complexity_indicator.name),
                    self.get_itens_orcamentarios_fora_do_comum(metrics, int(pronac), financial_complexity_indicator.name),
                    self.get_novos_fornecedores(metrics, int(pronac), financial_complexity_indicator.name),
                    self.get_projetos_mesmo_proponente(metrics, int(pronac), financial_complexity_indicator.name),
                    self.get_precos_acima_media(metrics, int(pronac), financial_complexity_indicator.name),
                ]
            }
        ]

        string_pronac = "{:06}".format(int(pronac))

        if(project is not None):
            project_information = {
                'name': project.name,
                'pronac': string_pronac,
                'indicators': project_indicators
            }
        else: project_information = {}

        return JsonResponse(project_information)

# class SendMetricFeedbackView(APIView):
#     """
#     A view that receives a single metric feedback
#     """
#     renderer_classes = (JSONRenderer, )
#     @method_decorator(csrf_exempt)
#     def dispatch(self, request, *args, **kwargs):
#         return generic.View.dispatch(self, request, *args, **kwargs)
# 
#     @csrf_exempt
#     def post(self, request, format=None):
#         request_data = json.loads(request.body)
# 
#         user_email = "{0}@cultura.gov.br".format(request_data['user_email'])
# 
#         user = get_object_or_404(User, email=user_email)
#         metric = get_object_or_404(Metric, id=int(request_data['metric_id']))
#         metric_feedback_rating = int(request_data['metric_feedback_rating'])
#         metric_feedback_text = request_data['metric_feedback_text']
# 
#         metric_query = MetricFeedback.objects.filter(
#             user=user,
#             metric=metric
#         )
# 
#         if len(metric_query) is 0:
#             # Creates metric
#             saved_metric_feedback = MetricFeedback.objects.create(
#                 user=user,
#                 metric=metric,
#                 grade=metric_feedback_rating,
#                 reason=metric_feedback_text
#             )
#         else:
#             # Updates metric
#             saved_metric_feedback = metric_query[0]
#             saved_metric_feedback.grade = metric_feedback_rating
#             saved_metric_feedback.reason = metric_feedback_text
#             saved_metric_feedback.save()
# 
#         request_response = {
#             'feedback_id': saved_metric_feedback.id,
#             'feedback_grade': saved_metric_feedback.grade,
#             'feedback_reason': saved_metric_feedback.reason
#         }
# 
#         return JsonResponse(request_response)
# 
# class SendProjectFeedbackView(APIView):
#     """
#     A view that receives a single metric feedback
#     """
#     renderer_classes = (JSONRenderer, )
#     @method_decorator(csrf_exempt)
#     def dispatch(self, request, *args, **kwargs):
#         return generic.View.dispatch(self, request, *args, **kwargs)
# 
#     @csrf_exempt
#     def post(self, request, format=None):
#         request_data = json.loads(request.body)
# 
#         user_email = "{0}@cultura.gov.br".format(request_data['user_email'])
# 
#         user = get_object_or_404(User, email=user_email)
#         entity = get_object_or_404(Entity, pronac=int(request_data['pronac']))
#         project_feedback_grade = int(request_data['project_feedback_grade'])
# 
#         project_query = ProjectFeedback.objects.filter(
#             user=user,
#             entity=entity
#         )
# 
#         if len(project_query) is 0:
#             # Creates
#             saved_project_feedback = ProjectFeedback.objects.create(
#                 user=user,
#                 entity=entity,
#                 grade=project_feedback_grade
#             )
#         else:
#             # Updates
#             saved_project_feedback = project_query[0]
#             saved_project_feedback.grade = project_feedback_grade
#             saved_project_feedback.save()
# 
# 
#         request_response = {
#             'feedback_id': saved_project_feedback.id,
#             'feedback_grade': saved_project_feedback.grade,
#         }
# 
#         return JsonResponse(request_response)
# 
# class CreateSingleUserView(APIView):
#     """
#     A view that creates a single user if not created
#     """
#     renderer_classes = (JSONRenderer, )
#     @method_decorator(csrf_exempt)
#     def dispatch(self, request, *args, **kwargs):
#         return generic.View.dispatch(self, request, *args, **kwargs)
# 
#     @csrf_exempt
#     def post(self, request, format=None):
#         user_data = json.loads(request.body)
# 
#         user_email = '{0}@cultura.gov.br'.format(user_data['email'])
# 
#         user_query = User.objects.filter(email=user_email)
# 
#         if len(user_query) is 0:
#             user_name = user_data['name']
# 
#             user = User.objects.create(email=user_email, name=user_name)
#         else:
#             user = user_query[0]
# 
#         user_response = {
#             'id': user.id,
#             'name': user.name,
#             'email': user.email
#         }
# 
#         return JsonResponse(user_response)
