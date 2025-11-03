from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control

@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(cache_control(max_age=3600), name='dispatch')
class ReactAppView(TemplateView):
    template_name = 'index.html'
