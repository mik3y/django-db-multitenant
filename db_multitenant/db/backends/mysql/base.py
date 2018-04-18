import logging
import time

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from importlib import import_module

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

        dbname = self.threadlocal.get_dbname()
        if not dbname:
            # Django loads the settings after it tries to connect to mysql, when running management commands
            # If that's the case, update database name manually
            update_database_from_env(super(DatabaseWrapper, self).get_connection_params())
            dbname = self.threadlocal.get_dbname()
            if not dbname:
                #raise ImproperlyConfigured('dbname not set at cursor create time')
                dbname = settings.DATABASES['default']['NAME']
                LOGGER.debug('dbname not set at cursor create time, using default database name: "{}".'.format(dbname))
        # Cache the applied dbname as "mt_dbname" on the connection, avoiding
        # an extra execute() if already set.  Importantly, we assume no other
        # code in the app is executing `USE`.
        connection = cursor.cursor.connection
        connection_dbname = getattr(connection, 'mt_dbname', None)

        if connection_dbname != dbname:
            start_time = time.time()
            cursor.execute('USE `%s`;' % dbname)
            time_ms = int((time.time() - start_time) * 1000)
            LOGGER.debug('Applied dbname `%s` in %s ms' % (dbname, time_ms))
            connection.mt_dbname = dbname

        return cursor