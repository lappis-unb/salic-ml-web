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
from .serializers import TestSerializer
import difflib

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
        
        return Response(content)

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
        
        return Response(content)

class ProjectInfoView(APIView):
    """
    A view that creates or sets an user and returns a single project information (indicators, metrics, feedbacks...)
    """
    renderer_classes = (JSONRenderer, )
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, format=None):
        obj = {
            'test': 123,
            'request': json.loads(request.body)
        }

        return JsonResponse(obj)

class SendMetricFeedbackView(APIView):
    """
    A view that receives a single metric feedback
    """
    renderer_classes = (JSONRenderer, )
    @csrf_exempt
    def post(self, request, format=None):

        return Response(request.content)

class SendProjectFeedbackView(APIView):
    """
    A view that receives a single metric feedback
    """
    renderer_classes = (JSONRenderer, )
    @csrf_exempt
    def post(self, request, format=None):

        return Response(request.content)
