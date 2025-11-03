
class AnonymousUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        anonymous_id = request.headers.get('X-Anonymous-ID')
        if anonymous_id:
            request.anonymous_id = anonymous_id
        
        response = self.get_response(request)
        
        return response