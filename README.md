# django-db-multitenant

Provides a simple multi-tenancy solution for Django based on the concept
of having a **single tenant per database**.

This application is still experimental, but is being used in
production by the author. Contributions and discussion are welcome.

**Latest Version:** v0.1.3, September 10, 2016 ([changelog](CHANGELOG.md))

## Background

Multi-tenancy is the ability to support multiple distinct datasets from
the same application server.  Each dataset usually maps to a customer
(the tenant) and is partially or fully partitioned from all other tenant
data.

Among the possible approaches are:

* **Isolated approach**: Separate database per tenant.
* **Semi-isolated approach**: Shared database, separate namespaces (postgres schemas)
  or table names/prefix per tenant.
* **Shared approach**: Single database for all tenants.  Each table has a column
  identifying the tenant for that row of data.

This application implements a variation of the **isolated approach**:

* Each tenant has its **own database**, however
* Other **connection details are shared** (such as password, database user).

django-db-multitenant makes it possible (even easy) to take a Django application
designed for a single tenant and use it with multiple tenants.

## Operation

The main technique is as follows:

1. When a request first arrives, determine desired the tenant from the ``request`` object,
   and save it in thread-local storage.
2. Later in the request, when a database cursor is accquired, issue an SQL
   ``USE <tenant database name>`` for the desired tenant with MySQL or
   ``SET search_patch TO <tenant name>``` with PostgreSQL.

Step 1 is accomplished by implementing a [mapper
class](https://github.com/mik3y/django-db-multitenant/blob/master/db_multitenant/mapper.py).
Your mapper takes a request object and returns a database name or tenant name,
using whatever logic you like (translate hostname, inspect a HTTP header, etc).
The mapper result is saved in thread-local storage for later use.

Step 2 determines whether the desired database or schema has already been
selected, and is skipped if so. This is implemented using a [thin database
backend
wrapper](https://github.com/mik3y/django-db-multitenant/blob/master/db_multitenant/db/backends/mysql/base.py),
which must be set in ``settings.DATABASES`` as the backend.

## Usage

### 1. Install

Install ``django-db-multitenant`` (or add it to your setup.py).

```
$ pip install django-db-multitenant
```

### 2. Implement a mapper

You must implement a sublcass of [db_multitenant.mapper](https://github.com/mik3y/django-db-multitenant/blob/master/db_multitenant/mapper.py)
which determines the database name and cache prefix from the request.

Some examples:

* A [simple mapper for MySQL](https://gist.github.com/mik3y/5959322), which uses a portion of the hostname
  directly as the database name.
* A [simple mapper for PostgreSQL](https://gist.github.com/stephane/08b649ea818bd9dce2ff33903ba94aba)
* A [Redis-backed mapper](https://gist.github.com/mik3y/5959282), which looks up the tenant
  using the hostname, throwing a 404 if unrecognized.

### 3. Update settings.py

Set the multitenant mapper by specifying the full dotted path to your implementation:

```python
MULTITENANT_MAPPER_CLASS = 'myapp.mapper.TenantMapper'
```

Install the multitenant middleware as the *first* middleware.

```python
MIDDLEWARE_CLASSES = (
    'db_multitenant.middleware.MultiTenantMiddleware',
    ) + MIDDLEWARE_CLASSES
```

Change your database backend to the multitenant wrapper:

```python
DATABASES = {
    'default': {
        'ENGINE': 'db_multitenant.db.backends.mysql',
        'NAME': 'devnull',
    }
```

*Note*: the `NAME` is useless for MySQL but due to a current limitation, the named database must exist.  It may
be empty and read-only.

Optionally, add the multitenant helper ``KEY_FUNCTION`` to your cache definition,
which will cause cache keys to be prefixed with the value of
``mapper.get_cache_prefix``:

```python
CACHES = {
  'default' : {
    'LOCATION': '127.0.0.1:11211',
    'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    'KEY_FUNCTION': 'db_multitenant.cache.helper.multitenant_key_func'
    }
}
```

**South Support**

If you use South, add the following to settings:

```python
SOUTH_DATABASE_ADAPTERS = {
    'default': 'south.db.mysql'
}
```

**Management Commands**: In order to use management commands (like syncdb)
with the correct tenant, inject this little hack in your settings:

```python
from db_multitenant.utils import update_from_env
update_from_env(database_settings=DATABASES['default'],
    cache_settings=CACHES['default'])
```

You can then export ``TENANT_DATABASE_NAME``, ``TENANT_NAME`` and
``TENANT_CACHE_PREFIX`` on the command line:

```
$ TENANT_DATABASE_NAME=example.com ./manage.py syncdb
```

That's it.  Because django-db-multitenant does not define any models, there's
no need to add it to ``INSTALLED_APPS``.

## Advantages and Limitations

There is no one-size-fits-all solution for a data modeling problem such
as multi-tenancy (see 'Alternatives').

#### Advantages

* Compatibility: Your Django application doesn't need any awareness of
  multi-tenancy.  Database-level tools (such as ``mysqldump``) just work.
* Isolation: One tenant, one database means there's no intermingling of
  tenant data.
* Simplicity: Your application schemas don't need to be cluttered with
  'Tenant' foreign key relationships.
* Should work well with Django 1.6 connection persistence and connection
  pooling.

#### Limitations

* Unorthodox.  Django does not expect this kind of dynamic database
  connection tinkering, and there could be unexpected bugs.
* Limited isolation.  Since the same DB credentials are used for all
  tenants, bugs in the mapper (or anywhere else in the app) could
  cause data corruption.
* A valid database still needs to be specified in ``settings.DATABASE``
  for use when the connection is first established (this should be fixed
  eventually).
* MySQL-only (this should be fixed eventually).
* Overhead: requests may add up to one extra query (the ``USE <dbname>`` statement).

## Alternatives and Further Reading

* [django-tenant-schemas](https://github.com/bcarneiro/django-tenant-schemas) implements a semi-isolated approach using postgres schemas (and inspired this project, as well as the 'Overview' section above).

## Credits and License

Copyright 2013 mike wakerly (opensource@hoho.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
