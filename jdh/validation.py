import os
import json
import logging

from django.conf import settings
from jsonschema import validate as jsonschemaValidate

logger = logging.getLogger(__name__)


class JSONSchema:
    def __init__(self, filepath):
        abs_filepath = os.path.join(settings.JDH_SCHEMA_ROOT, filepath)
        logger.info(
            f"JSON schema init on file:{filepath}"
            f" - JDH_SCHEMA_ROOT: {settings.JDH_SCHEMA_ROOT}"
        )
        with open(abs_filepath, "r") as schema:
            try:
                self.schema = json.load(schema)
                self.filepath = filepath
                logger.info(f"JSON schema loaded from {filepath}")
            except Exception as e:
                logger.exception(f"Unable to load JSON from {abs_filepath}")
                raise e

    def set_schema_root(self, schema_root):
        abs_filepath = os.path.join(schema_root, self.filepath)
        logger.info(
            f"JSON schema init on file:{self.filepath}"
            f" - *SCHEMA_ROOT: {schema_root}"
        )
        with open(abs_filepath, "r") as schema:
            try:
                self.schema = json.load(schema)
            except Exception as e:
                logger.error(f"Unable to load JSON from {abs_filepath}")
                raise e

    def validate(self, instance):
        # logger.info(f'validate() using json filepath: {self.filepath}')
        jsonschemaValidate(instance=instance, schema=self.schema)
