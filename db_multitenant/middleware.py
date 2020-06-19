from django.conf import settings
from django.db import connection
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Not required for Django <= 1.9, see:
    # https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    MiddlewareMixin = object

from db_multitenant import utils


class MultiTenantMiddleware(MiddlewareMixin):
    """Should be placed first in your middlewares.

    This middleware sets up the database and cache prefix from the request."""
    def process_request(self, request):
        mapper = utils.get_mapper()

        threadlocal = connection.get_threadlocal()
        tenant_name = mapper.get_tenant_name(request)
        threadlocal.set_tenant_name(tenant_name)
        db_name = mapper.get_db_name(request, tenant_name)
        # Fixes ValueError when trying to inject SQL, setting empty string as default
        try:
            threadlocal.set_db_name(db_name)
        except ValueError as ve:
            threadlocal.set_db_name('')
        threadlocal.set_cache_prefix(mapper.get_cache_prefix(request, tenant_name, db_name))

        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            # Clear the sites framework cache.
            from django.contrib.sites.models import Site
            Site.objects.clear_cache()

    def process_response(self, request, response):
        """Clears the database name and cache prefix on response.

        This is a precaution against the connection being reused without
        first calling set_db_name or set_tenant_name.
        """
        connection.get_threadlocal().reset()
        return response
