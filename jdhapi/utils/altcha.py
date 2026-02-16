import datetime
import logging
from altcha import ChallengeOptions, create_challenge, verify_solution
from django.conf import settings

logger = logging.getLogger(__name__)

hmac_key = settings.ALTCHA_HMAC_KEY[0]

def create_captcha_challenge():
    """
    Create a challenge for the captcha.
    
    :return: The created challenge.
    :rtype: Challenge
    """

    logger.info("[create_challenge] Starting create challenge for captcha")

    # Create a new challenge
    options = ChallengeOptions(
        expires=datetime.datetime.now() + datetime.timedelta(hours=1),
        max_number=100000, # The maximum random number
        hmac_key=hmac_key,
    )
    challenge = create_challenge(options)
    logger.info(f"Challenge created:", challenge)

    # Manually convert the Challenge object to a dictionary
    challenge_dict = {
        'algorithm': challenge.algorithm,
        'challenge': challenge.challenge,
        'maxnumber': challenge.max_number,
        'salt': challenge.salt,
        'signature': challenge.signature,
    }

    logger.info("Challenge converted to a dict")

    return challenge_dict

def verify_challenge_solution(payload: dict) -> bool :
    """
    Verify if the payload contains a valid solution for the captcha challenge.
    
    :return: True or false.
    :rtype: Boolean.
    :param payload: The payload to verify, it should contain the following keys: algorithm, challenge, number, salt and signature.

    """

    ok, err = verify_solution(payload, hmac_key, check_expires=True)

    return ok, err