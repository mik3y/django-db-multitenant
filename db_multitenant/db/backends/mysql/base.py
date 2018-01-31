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

from importlib import import_module
import logging
import time

from django.core.exceptions import ImproperlyConfigured

from db_multitenant.threadlocal import MultiTenantThreadlocal
from db_multitenant.utils import update_database_from_env

WRAPPED_BACKEND = import_module('django.db.backends.mysql.base')

LOGGER = logging.getLogger('db_multitenant')

class DatabaseWrapper(WRAPPED_BACKEND.DatabaseWrapper):
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.threadlocal = MultiTenantThreadlocal()

    def get_threadlocal(self):
        return self.threadlocal

    def _cursor(self):
        """Supplies a cursor, executing the `USE` statement if required.

        Ideally we'd override a get_new_connection DatabaseWrapper function,
        but _cursor() is as close as it gets.
        """
        cursor = super(DatabaseWrapper, self)._cursor()

        db_name = self.threadlocal.get_db_name()
        if not db_name:
            # Django loads the settings after it tries to connect to mysql, when
            # running management commands If that's the case, update database
            # name manually
            update_database_from_env(super(DatabaseWrapper, self).get_connection_params())
            db_name = self.threadlocal.get_db_name()
            if not db_name:
                raise ImproperlyConfigured('db_name not set at cursor create time')

        # Cache the applied db_name as "mt_db_name" on the connection, avoiding
        # an extra execute() if already set.  Importantly, we assume no other
        # code in the app is executing `USE`.
        connection = cursor.cursor.connection
        connection_db_name = getattr(connection, 'mt_db_name', None)

        if connection_db_name != db_name:
            start_time = time.time()
            cursor.execute('USE `%s`;' % db_name)
            time_ms = int((time.time() - start_time) * 1000)
            LOGGER.debug('Applied db_name `%s` in %s ms', db_name, time_ms)
            connection.mt_db_name = db_name

        return cursor
