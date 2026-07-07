from django.core.cache import cache
from pipeline.models import SystemSetting

CACHE_KEY = 'default_pricing_companies'


def get_default_company_ids() -> list[int]:
    company_ids = cache.get(CACHE_KEY)
    if company_ids is None:
        try:
            setting = SystemSetting.objects.get(key=CACHE_KEY)
            company_ids = setting.value
            cache.set(CACHE_KEY, company_ids, 60 * 60)
        except SystemSetting.DoesNotExist:
            company_ids = []
    return company_ids
