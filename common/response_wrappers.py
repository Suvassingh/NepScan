 
from rest_framework.response import Response

class APIResponse(Response):
 
    def __init__(self, data=None, status=200, message='Success', **kwargs):
        if data is None:
            data = {}
        super().__init__(
            {
                'status': status,
                'message': message,
                'data': data,
            },
            status=status,
            **kwargs
        )