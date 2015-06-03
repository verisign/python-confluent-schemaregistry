
VALID_LEVELS=['NONE','FULL','FORWARD','BACKWARD']

class ClientError(Exception, object):
    """Error thrown by Schema Registry clients"""
    def __init__(self, message, http_code=-1):
        self.message = message
        self.http_code = http_code
        super(ClientError, self).__init__(self.__str__())

    def __repr__(self):
        return "ClientError(error={error})".format(error=self.message)

    def __str__(self):
        return self.message

from MockSchemaRegistryClient import *
from CachedSchemaRegistryClient import *
