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

import logging
from threading import local

LOGGER = logging.getLogger('db_multitenant')

class MultiTenantThreadlocal(local):
    """Thread-local state.  An instance of this should be attached to a
    database connection.

    The first time a request is processed, the tenant name is looked up and
    set in this class.  When a cursor is accquired on that connection,
    the database wrapper will apply the tenant name.
    """
    def __init__(self):
        self.tenant_name = None
        self.dbname = None
        self.cache_prefix = None

    def get_tenant_name(self):
        return self.tenant_name

    def set_tenant_name(self, tenant_name):
        self.tenant_name = tenant_name

    def get_dbname(self):
        return self.dbname

    def set_dbname(self, dbname):
        # Sanity check; this is highly simplistic; mappers should sanitize.
        if ';' in dbname:
            raise ValueError('Illegal database name: %s' % dbname)
        self.dbname = dbname

    def set_cache_prefix(self, prefix):
        self.cache_prefix = prefix

    def get_cache_prefix(self):
        return self.cache_prefix

    def reset(self):
        self.dbname = None
        self.cache_prefix = None

