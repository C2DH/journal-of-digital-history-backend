from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from jdhapi.utils.altcha import create_captcha_challenge

from .logger import logger as get_logger

logger=get_logger()

@api_view(["GET"])
def get_captcha_challenge(request):

    """
    GET /api/captcha

    Endpoint to send a captcha challenge.
    """

    try:
        challenge = create_captcha_challenge()
        logger.info(f"GET /api/captcha Captcha send")
        return Response(challenge, status=status.HTTP_200_OK)


    except Exception as e :
        logger.error(f"Unexpected error when sending captcha challenge:{e}")
        return Response(
            {
                "error": "InternalError",
                "message": "An unexpected error occurred. Please try again later.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) 



