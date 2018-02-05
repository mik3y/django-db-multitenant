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
