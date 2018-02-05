from django.db import connection
from django.core.exceptions import ImproperlyConfigured

def multitenant_key_func(key, key_prefix, version):
    tenant_prefix = connection.get_threadlocal().get_cache_prefix()
    if tenant_prefix is None:
        raise ImproperlyConfigured('Multi-tenant cache prefix not available')
    return '%s:%s:%s:%s' % (tenant_prefix, key_prefix, version, key)
