from hmac import HMAC, compare_digest
from hashlib import sha256
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from rest_framework import status


def verify_signature(req):
     received_sign = req.headers.get('X-Hub-Signature-256').split('sha256=')[-1].strip()
     secret = str(settings.JDHTASKS_WEBHOOK_SECRET).encode()
     expected_sign = HMAC(key=secret, msg=req.body, digestmod=sha256).hexdigest()
     return compare_digest(received_sign, expected_sign)


@api_view([
   'POST'])
@permission_classes([AllowAny])
def webhook(request, username, repo):
    """ Webook echo default """
    # Extract signature header
    # See https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads
    # test with curl:
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature or not signature.startswith("sha256="):
      return Response({
        'error': 'X-Hub-Signature required, or not valid.'
      }, status=status.HTTP_400_BAD_REQUEST)

    if not verify_signature(request):
      return Response({
        'error': 'X-Hub-Signature is definitely not valid.'
      }, status=status.HTTP_400_BAD_REQUEST)

    # The signature is fine, let's parse the data
    data = request.get_json()

    # We are only interested in push events from the a certain repo
    return Response({'message': 'Hello!', 'username': username, 'repo': repo, 'data': data})