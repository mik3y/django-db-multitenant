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
                # As performance_schema always exists, it's predefined to avoid ImproperlyConfigured exception
                db_name = "performance_schema"
                #raise ImproperlyConfigured('db_name not set at cursor create time')

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
