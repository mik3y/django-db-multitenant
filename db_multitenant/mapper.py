"""Mapper interface."""

class TenantMapper:
    """Interface for mapping django bits to a tenant, based on a request.

    You must provide an implementation of this class, and set
    settings.MULTITENANT_MAPPER_CLASS to its full class name.
    """
    def get_tenant_name(self, request):
        """Returns an opaque identifier for the current tenant."""
        raise NotImplementedError

    def get_db_name(self, request, tenant_name):
        """Returns the database name which should be used for this tenant."""
        raise NotImplementedError

    def get_cache_prefix(self, request, tenant_name, db_name):
        """Returns the cache prefixed to be used for this tenant."""
        raise NotImplementedError
