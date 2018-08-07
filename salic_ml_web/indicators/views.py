# Remove this import when has a valid complexity value
import random
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Entity, User, ProjectFeedback, MetricFeedback, Metric
from salic_db.utils import test_connection, make_query_from_db


def index(request):
    projects = [
        {"pronac": "1234", "complexity": 25,
            "project_name": "Show do Tiririca", "analist": "Florentina"},
        {"pronac": "4321", "complexity": 75,
            "project_name": "Show do ex Calipso", "analist": "Chimbinha"},
        {"pronac": "1324", "complexity": 95,
            "project_name": "Projeto da Cláudia Leitte", "analist": "Cláudia Leitte"},
        {"pronac": "1243", "complexity": 15,
            "project_name": "Tourada", "analist": "Ferdinando"},
        {"pronac": "2143", "complexity": 5,
            "project_name": "Projeto modelo", "analist": "Modelo"},
    ]
    # projects = projects_to_analyse(request)

    return render(request, 'index.html', {'projects': projects})


def show_metrics(request, pronac):
    project = get_object_or_404(Entity, pronac=int(pronac))
    current_user = None
    metrics = []
    return render(request, 'show_metrics.html', {'project': project, 'user': current_user, 'metrics': metrics})


def db_connection_test(request):
    connection_result = test_connection()
    return HttpResponse(connection_result)


def projects_to_analyse(request):
    query = "SELECT CONCAT(AnoProjeto, Sequencial), NomeProjeto, Analista, \
             Situacao FROM SAC.dbo.Projetos WHERE DtFimExecucao < GETDATE()"
    query_result = make_query_from_db(query)

    end_situations = [
        'A09', 'A13', 'A14', 'A16', 'A17', 'A18', 'A20', 'A23', 'A24', 'A26',
        'A40', 'A41', 'A42', 'C09', 'D18', 'E04', 'E09', 'E36', 'E47', 'E49',
        'E63', 'E64', 'E65', 'G16', 'G25', 'G26', 'G29', 'G30', 'G56', 'K00',
        'K01', 'K02', 'L01', 'L02', 'L03', 'L04', 'L05', 'L06', 'L08', 'L09',
        'L10', 'L11'
    ]

    filtered_data = [
        each for each in query_result if each[3] not in end_situations]

    filtered_data_dict = []

    for each in filtered_data:
        filtered_data_dict.append(
            {
                'pronac': each[0],
                'complexity': random.randint(0, 100),
                'project_name': each[1],
                'analist': each[2]
            }
        )

    return filtered_data_dict


def fetch_user_data(request):
    try:
        user = User.objects.get(email=request.POST['user_email'])
    except:
        user_name = str(request.POST['user_first_name'])

        user_email = str(request.POST['user_email'] + "@gmail.com")

        user = User.objects.create(email=user_email, name=user_name)

    pronac = request.POST['project_pronac']
    project = get_object_or_404(Entity, pronac=int(pronac))

    project_indicators = [
        {
            'name': 'complexidade da prestação de contas',
            'value': '50',
            'metrics': [
                {
                    'name': 'Metrica 01',
                    'value': '12',
                    'reason': 'any reason',
                    'outlier_check': True
                },
                {
                    'name': 'Metrica 02',
                    'value': '13',
                    'reason': 'any reason',
                    'outlier_check': True
                },
                {
                    'name': 'Metrica 03',
                    'value': '60',
                    'reason': 'any reason',
                    'outlier_check': False
                },
                {
                    'name': 'Metrica 04',
                    'value': '70',
                    'reason': 'any reason',
                    'outlier_check': False
                },
            ]
        },
    ]
    project_feedback_list = ['Muito simples', 'Simples', 'Normal', 'Complexo', 'Muito complexo']
    
    return render(request, 'show_metrics.html', {'project': project, 'user': user, 'project_indicators': project_indicators, 'project_feedback_list': project_feedback_list})

def post_metrics_feedback(request):
    entity = Entity.objects.get(pronac=request.POST['project_pronac'])
    user = User.objects.get(email=request.POST['user_email'])

    project_feedback_grade = request.POST['project_feedback_grade']
    #ProjectFeedback.objects.create(user=user, entity=entity, grade=project_feedback_grade)

    return HttpResponse(project_feedback_grade)

