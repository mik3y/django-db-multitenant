"""
https://gist.github.com/stephane/08b649ea818bd9dce2ff33903ba94aba
Maps a request to a tenant using the first part of the hostname.

For example:
  foo.example.com:8000 -> foo
  bar.baz.example.com -> bar

This is a simple example; you should probably verify tenant names
are valid against a whitelist before returning them, since the returned
tenant name will be issued in a `SET search_path TO` SQL query.

Take care to create the corresponding schema first, with ``psql``:

  db=# CREATE SCHEMA foo;

You can set the tenant in command line with:

  TENANT_NAME=foo ./manage.my migrate

With PostgreSQL, it's possible to have complex setups where
some tables are public so you can set the schema to:

  SET search_path TO foo,public;

To have an access to public and foo tables at the same time.

https://www.postgresql.org/docs/current/static/ddl-schemas.html
"""
import re
from db_multitenant import mapper

HOST_REGEX = re.compile(r'(\w+)[\.|$]')


class TenantMapper(mapper.TenantMapper):
    def get_tenant_name(self, request):
        """Takes the first part of the hostname as the tenant"""
        hostname = request.get_host()
        match = HOST_REGEX.search(hostname)
        tenant_name = match.groups()[0].lower() if match else None

        # Compare against a whitelist or fallback to 'public'?
        if not tenant_name:
            raise ValueError('Unable to find the tenant name from `%s`.' % hostname)

        return tenant_name

    def get_db_name(self, request, tenant_name):
        # Still use the DB name of settings
        return None

    def get_cache_prefix(self, request, tenant_name, db_name):
        """The arguments db_name and tenant_name are provided by the methods of this TenantMapper"""
        return 'tenant-%s' % tenant_name
