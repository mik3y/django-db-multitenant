"""
https://gist.github.com/mik3y/5959282
Maps a request to a tenant using Redis.
Redis should store a map of hostname -> tenant name.  The tenant name
is then used to form the database and cache names.
"""

from db_multitenant import mapper
from django.http import Http404
import redis

REDIS_POOL = redis.ConnectionPool(host='localhost', port=6379, db=0)

class RedisTenantMapper(mapper.TenantMapper):
    def get_tenant_name(self, request):
        """Assumes Redis maps hostname -> tenant name."""
        hostname = request.get_host().split(':')[0].lower()
        r = redis.Redis(connection_pool=REDIS_POOL)
        name = r.get(hostname)
        if not name:
            raise Http404('Unknown tenant for hostname: "%s"' % hostname)
        return name

    def get_db_name(self, request, tenant_name):
        """Returns tenant-<tenant_name>, using tenant name from Redis."""
        return 'tenant-%s' % tenant_name

    def get_cache_prefix(self, request, tenant_name, db_name):
        """The arguments db_name and tenant_name are provided by the methods of this TenantMapper.
           Returns tenant-<tenant_name>, using tenant name from Redis."""
        return 'tenant-%s' % tenant_name
