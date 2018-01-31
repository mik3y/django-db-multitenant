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
import os
from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from db_multitenant.mapper import TenantMapper

_CACHED_MAPPER = None

def update_from_env(database_settings=None, cache_settings=None):
    update_database_from_env(database_settings)
    update_cache_from_env(cache_settings)
    update_tenant_name_from_env()

def update_database_from_env(database_settings):
    from django.db import connection
    db_name = os.environ.get('TENANT_DATABASE_NAME')
    if db_name and database_settings is not None:
        database_settings['NAME'] = db_name
        connection.get_threadlocal().set_db_name(db_name)

def update_cache_from_env(cache_settings):
    from django.db import connection
    cache_prefix = os.environ.get('TENANT_CACHE_PREFIX')
    if cache_prefix is not None and cache_settings is not None:
        cache_settings['KEY_PREFIX'] = cache_prefix
        connection.get_threadlocal().set_cache_prefix(cache_prefix)

def update_tenant_name_from_env():
    from django.db import connection
    tenant_name = os.environ.get('TENANT_NAME')
    if tenant_name:
        connection.get_threadlocal().set_tenant_name(tenant_name)

def get_mapper():
    """Returns the mapper."""
    global _CACHED_MAPPER
    if not _CACHED_MAPPER:
        name = getattr(settings, 'MULTITENANT_MAPPER_CLASS', None)
        if not name:
            raise ImproperlyConfigured("You must specify MULTITENANT_MAPPER_CLASS in settings.")

        try:
            module_path, member_name = name.rsplit(".", 1)
            module = import_module(module_path)
            cls = getattr(module, member_name)
        except (ValueError, ImportError, AttributeError) as error:
            raise ImportError("Could not import mapper: %s: %s" % (name, error))

        if not issubclass(cls, TenantMapper):
            raise ImproperlyConfigured(
                '%s does not subclass db_multitenant.mapper.TenantMapper', name)

        _CACHED_MAPPER = cls()

    return _CACHED_MAPPER
