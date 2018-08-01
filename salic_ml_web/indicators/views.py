from django.shortcuts import render
from django.http import HttpResponse
from salic_db.utils import testConnection

def index(request):
    projects = [
        {"pronac": "1234", "complexity": 25, "title": "Show do Tiririca", "responsible": "Florentina"},
        {"pronac": "4321", "complexity": 75, "title": "Show do ex Calipso", "responsible": "Chimbinha"},
        {"pronac": "1324", "complexity": 95, "title": "Projeto da Cláudia Leitte", "responsible": "Cláudia Leitte"},
        {"pronac": "1243", "complexity": 15, "title": "Tourada", "responsible": "Ferdinando"},
        {"pronac": "2143", "complexity": 5, "title": "Projeto modelo", "responsible": "Modelo"},
    ]
    return render(request, 'index.html', {'projects': projects})

def show_metrics(request):
    return render(request, 'show_metrics.html', {})

def dbConnectionTest(request):
    connection_result = testConnection()
    return HttpResponse(connection_result)
