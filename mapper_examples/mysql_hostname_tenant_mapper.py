"""
https://gist.github.com/mik3y/5959322
Maps a request to a tenant using the first part of the hostname.
For example:
  foo.example.com:8000 -> foo
  bar.baz.example.com -> bar
This is a simple example; you should probably verify tenant names
are valid before returning them, since the returned tenant name will
be issued in a `USE` SQL query.
"""

from db_multitenant import mapper

class SimpleTenantMapper(mapper.TenantMapper):
    def get_tenant_name(self, request):
        """Takes the first part of the hostname as the tenant"""
        hostname = request.get_host().split(':')[0].lower()
        return hostname.split('.')[0]

    def get_db_name(self, request, tenant_name):
        return 'tenant-%s' % tenant_name

    def get_cache_prefix(self, request, tenant_name, db_name):
        """The arguments db_name and tenant_name are provided by the methods of this TenantMapper"""
        return 'tenant-%s' % tenant_name
