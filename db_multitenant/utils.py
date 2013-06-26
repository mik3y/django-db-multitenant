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
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

from db_multitenant.mapper import TenantMapper

_CACHED_MAPPER = None

import os

def update_database_from_env(db_dict):
    from django.db import connection
    dbname = os.environ.get('TENANT_DATABASE_NAME')
    if dbname:
        db_dict['NAME'] = dbname
        connection.get_threadlocal().set_dbname(dbname)

def update_cache_from_env(cache_dict):
    from django.db import connection
    cache_prefix = os.environ.get('TENANT_CACHE_PREFIX')
    if cache_prefix is not None:
        cache_dict['KEY_PREFIX'] = cache_prefix
        connection.get_threadlocal().set_cache_prefix(cache_prefix)

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
        except (ValueError, ImportError, AttributeError), e:
            raise ImportError("Could not import mapper: %s: %s" % (name, e))

        if not issubclass(cls, TenantMapper):
            raise ImproperlyConfigured('%s does not subclass db_multitenant.mapper.TenantMapper', name)

        _CACHED_MAPPER = cls()

    return _CACHED_MAPPER

