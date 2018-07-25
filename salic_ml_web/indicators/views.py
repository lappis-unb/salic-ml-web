from django.shortcuts import render
from django.http import HttpResponse
from salic_db.utils import testConnection

def index(request):
    return HttpResponse("This is index")

def dbConnectionTest(request):
    connection_result = testConnection()
    return HttpResponse(connection_result)
