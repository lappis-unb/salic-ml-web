from django.shortcuts import render
import random
from django.http import HttpResponse
from salic_db.utils import test_connection, make_query_from_db

def index(request):
    return HttpResponse("This is index")

def db_connection_test(request):
    connection_result = test_connection()
    return HttpResponse(connection_result)

def projects_to_analyse(request):
    query = "SELECT CONCAT(AnoProjeto, Sequencial), NomeProjeto, Analista, Situacao FROM SAC.dbo.Projetos WHERE DtFimExecucao < GETDATE()"
    query_result = make_query_from_db(query)

    end_situations = [
        'A09', 'A13', 'A14', 'A16', 'A17', 'A18', 'A20', 'A23', 'A24', 'A26', 'A40', 'A41',
        'A42', 'C09', 'D18', 'E04', 'E09', 'E36', 'E47', 'E49', 'E63', 'E64', 'E65', 'G16', 'G25',
        'G26', 'G29', 'G30', 'G56', 'K00', 'K01', 'K02', 'L01', 'L02', 'L03', 'L04', 'L05', 
        'L06', 'L08', 'L09', 'L10', 'L11'
    ]

    filtered_data = [each for each in query_result if each[3] not in end_situations]

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

    return HttpResponse(filtered_data_dict)