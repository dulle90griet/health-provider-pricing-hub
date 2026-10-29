"""Define custom serialization rules for our APIGatewayHttpResolver"""

from decimal import Decimal
from datetime import datetime
import json


class CustomJSONEncoder(json.JSONEncoder):
    """
    Supplements the default JSONEncoder to support stringification
    of Decimals and datetimes.
    """

    def default(self, o):
        if isinstance(o, (Decimal, datetime)):
            return str(o)
        return super().default(o)


def custom_serializer(o):
    """
    Function passed to the APIGatewayHttpResolver to instruct use
    of CustomJSONEncoder.
    """

    return json.dumps(o, separators=(",", ":"), cls=CustomJSONEncoder)
