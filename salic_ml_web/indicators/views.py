from django.shortcuts import render
from django.http import HttpResponse
from salic_db.utils import testConnection

def index(request):
    a = [1,2,3,4]
    return render(request, 'index.html', {'a': a})

def dbConnectionTest(request):
    connection_result = testConnection()
    return HttpResponse(connection_result)
