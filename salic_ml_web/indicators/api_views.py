from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from indicators.views import projects_to_analyse

class AllProjectsView(APIView):
    """
    A view that returns a list containing all the projects
    """
    renderer_classes = (JSONRenderer, )

    def get(self, request, format=None):
        
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

        json_dict = projects
        content = {'projects': projects}
        
        return Response(content)