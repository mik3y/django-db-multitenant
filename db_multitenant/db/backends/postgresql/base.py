# Copyright (c) 2013, mike wakerly <opensource@hoho.com>
# Copyright (c) 2017, Stéphane Raimbault <https://github.com/stephane>
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

from django.db.utils import load_backend
from django.core.exceptions import ImproperlyConfigured

from db_multitenant.threadlocal import MultiTenantThreadlocal

WRAPPED_BACKEND = load_backend('django.db.backends.postgresql_psycopg2')


class DatabaseWrapper(WRAPPED_BACKEND.DatabaseWrapper):
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.threadlocal = MultiTenantThreadlocal()
        self.search_path_set = False

    def close(self):
        self.search_path_set = False
        super(DatabaseWrapper, self).close()

    def rollback(self):
        super(DatabaseWrapper, self).rollback()
        # Django's rollback clears the search path so we have to set it again the next time.
        self.search_path_set = False

    def get_threadlocal(self):
        return self.threadlocal

    def _cursor(self, name=None):
        """Supplies a cursor, selecting the schema if required.

        Ideally we'd override a get_new_connection DatabaseWrapper function,
        but _cursor() is as close as it gets.
        """
        if name:
            cursor = super(DatabaseWrapper, self)._cursor(name=name)
        else:
            cursor = super(DatabaseWrapper, self)._cursor()

        tenant_name = self.threadlocal.get_tenant_name()
        if not tenant_name:
            raise ImproperlyConfigured('Tenant name not set at cursor create time.')

        # Cache the applied search_path.  Importantly, we assume no other
        # code in the app is executing `SET search_path`.
        if not self.search_path_set:
            # Named cursor can only be used once
            cursor_for_search_path = self.connection.cursor() if name else cursor
            # Nothing prevent tenant_name to be 'foo, public' to provide sharing of tables
            # (eg. to provide a common table of users).
            cursor_for_search_path.execute('SET search_path TO %s' % tenant_name)

            if name:
                cursor_for_search_path.close()

            self.search_path_set = True

        return cursor
