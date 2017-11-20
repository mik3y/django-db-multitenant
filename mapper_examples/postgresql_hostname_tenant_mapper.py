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
"""
import re
from db_multitenant import mapper

host_regex = re.compile(r'(\w+)[\.|$]')


class TenantMapper(mapper.TenantMapper):
    def get_tenant_name(self, request):
        """Takes the first part of the hostname as the tenant"""
        hostname = request.get_host()
        match = host_regex.search(hostname)
        tenant_name = match.groups()[0].lower() if match else None

        # Compare against a whitelist or fallback to 'public'?
        if not tenant_name:
            raise ValueError('Unable to find the tenant name from `%s`.' % hostname)

        return tenant_name

    def get_dbname(self, request):
        # Still use the DB name of settings
        return None

    def get_cache_prefix(self, request):
        return 'tenant-%s' % self.get_tenant_name(request)
