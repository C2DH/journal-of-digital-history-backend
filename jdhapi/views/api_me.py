from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import  IsAdminUser
from rest_framework.decorators import permission_classes

# staff only access
@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_me(request):
    return Response({
        'username': request.user.username,
        'first_name': request.user.first_name,
    })