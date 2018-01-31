# Copyright (c) 2013, mike wakerly <opensource@hoho.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.  Redistributions in binary
# form must reproduce the above copyright notice, this list of conditions and
# the following disclaimer in the documentation and/or other materials provided
# with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
        threadlocal.set_db_name(db_name)
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
