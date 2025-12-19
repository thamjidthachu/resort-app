from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_200_OK

# Create your views here.



class IndexView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        return Response({'status': 'ok', 'application': 'Azure Horizon', "version": "0.0.1"}, status=HTTP_200_OK)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        return Response({'status': 'ok', 'application': 'Azure Horizon', "version": "0.0.1"}, status=HTTP_200_OK)