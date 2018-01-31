django-db-multitenant
=====================

Provides a simple multi-tenancy solution for Django based on the concept
of having a **single tenant per database**.

This application is still experimental, but is being used in production
by the authors. Contributions and discussion are welcome.

`Read the Changelog <CHANGELOG.rst>`__

Background
----------

Multi-tenancy is the ability to support multiple distinct datasets from
the same application server. Each dataset usually maps to a customer
(the tenant) and is partially or fully partitioned from all other tenant
data.

Among the possible approaches are:

-  **Isolated approach**: Separate database per tenant.
-  **Semi-isolated approach**: Shared database, separate namespaces
   (PostgreSQL schemas) or table names/prefix per tenant.
-  **Shared approach**: Single database for all tenants. Each table has
   a column identifying the tenant for that row of data.

This application supports two backends, MySQL and PostgreSQL:

- **With MySQL**, this application implements a variation of the **isolated approach**,
  each tenant has its **own database**, however their **connection details are
  shared** (such as password, database user).

- **For PostgreSQL**, this application implements a **semi-isolated approach**,
  each tenant has its own schema and the connection details are shared via the
  public schema.

django-db-multitenant makes it possible (even easy) to take a Django
application designed for a single tenant and use it with multiple
tenants.

Operation
---------

The main technique is as follows:

#. When a request first arrives, determine desired the tenant from the
   ``request`` object, and save it in thread-local storage.
#. Later in the request, when a database cursor is accquired, issue an
   SQL ``USE <tenant database name>`` for the desired tenant with MySQL
   or ``SET search_patch TO <tenant name>`` with PostgreSQL.

Step 1 is accomplished by implementing a `mapper
class <https://github.com/mik3y/django-db-multitenant/blob/master/db_multitenant/mapper.py>`__.
Your mapper takes a request object and returns a database name or tenant
name, using whatever logic you like (translate hostname, inspect a HTTP
header, etc). The mapper result is saved in thread-local storage for
later use.

Step 2 determines whether the desired database or schema has already
been selected, and is skipped if so. This is implemented using a thin
database backend
wrapper `for MySQL <https://github.com/mik3y/django-db-multitenant/blob/master/db_multitenant/db/backends/mysql/base.py>`__ and
`for PostgreSQL <https://github.com/mik3y/django-db-multitenant/blob/master/db_multitenant/db/backends/postgresql/base.py>`__
which must be set in ``settings.DATABASES`` as the backend.

Usage
-----

1. Install
~~~~~~~~~~

Install ``django-db-multitenant`` (or add it to your setup.py).

::

    $ pip install django-db-multitenant

2. Implement a mapper
~~~~~~~~~~~~~~~~~~~~~

You must implement a subclass of
`db_multitenant.mapper <https://github.com/mik3y/django-db-multitenant/blob/master/db_multitenant/mapper.py>`__
which determines the database name and cache prefix from the request.

To help you to write your mapper, the repository contains examples of mappers which extracts the hostname
of URL to determine the tenant name (eg. in `https://foo.example.com/bar/`, `foo` will be the tenant name):

-  `mapper for MySQL <https://github.com/mik3y/django-db-multitenant/blob/master/mapper_examples/mysql_hostname_tenant_mapper.py>`__,
   which uses a portion of the hostname directly as the database name.

-  `mapper for PostgreSQL <https://github.com/mik3y/django-db-multitenant/blob/master/mapper_examples/postgresql_hostname_tenant_mapper.py>`__,
   which uses a portion of the hostname as search path (schema). PostgreSQL
   allows complex setups with sharing of common tables (public accounts for example),
   see the comment in the mapper for more details.

-  `mapper for Redis <https://github.com/mik3y/django-db-multitenant/blob/master/mapper_examples/redis_hostname_tenant_mapper.py>`__,
   which looks up the tenant using the hostname, throwing a 404 if unrecognized.

Feel free to copy an example mapper in your project then adjust it to your needs.

3. Update settings.py
~~~~~~~~~~~~~~~~~~~~~

Set the multitenant mapper by specifying the full dotted path to your
implementation (in this example, `mapper` is the name of file `mapper.py`):

.. code:: python

    MULTITENANT_MAPPER_CLASS = 'myapp.mapper.TenantMapper'

Install the multitenant middleware as the *first* middleware of the list (prior to Django
1.10, you must use the ``MIDDLEWARE_CLASSES`` setting):

.. code:: python

    MIDDLEWARE = [
        'db_multitenant.middleware.MultiTenantMiddleware',
        ....
    ]

Change your database backend to the multitenant wrapper:

.. code:: python

    DATABASES = {
        'default': {
            'ENGINE': 'db_multitenant.db.backends.mysql',
            'NAME': 'devnull',
        }
    }

*Note*: the ``NAME`` is useless for MySQL but due to a current
limitation, the named database must exist. It may be empty and
read-only.

Or for PostgreSQL:

.. code:: python

    DATABASES = {
        'default': {
            'ENGINE': 'db_multitenant.db.backends.postgresql',
            'NAME': 'mydb',
        }
    }

Optionally, add the multitenant helper ``KEY_FUNCTION`` to your cache
definition, which will cause cache keys to be prefixed with the value of
``mapper.get_cache_prefix``:

.. code:: python

    CACHES = {
      'default' : {
            'LOCATION': '127.0.0.1:11211',
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'KEY_FUNCTION': 'db_multitenant.cache.helper.multitenant_key_func'
        }
    }

4. Tests
~~~~~~~~

If the tenant name of your application is extracted from the URL (as in the provided examples of
`mappers <https://github.com/mik3y/django-db-multitenant/blob/master/mapper_examples>`__), you can add
a host to your ``/etc/hosts`` such as ``foo.example.com`` to redirect to your localhost server.

You should add ``foo.example.com`` to ``ALLOWED_HOSTS`` list in your Django settings and just try
to reach your application from your browser with ``http://foo.example.com:8000``.

The examples of mappers provide information about the way to create a tenant zone.

Management Commands
-------------------

In order to use management commands (like ``migrate``) with the correct tenant,
inject this little hack at the end of your ``settings.py``:

.. code:: python

    from db_multitenant.utils import update_from_env
    update_from_env(database_settings=DATABASES['default'],
        cache_settings=CACHES['default'])

If you didn't set ``CACHES`` in your settings and you don't intend to use a cache system,
you don't have to pass the ``cache_settings`` argument to the function.

You can then export ``TENANT_DATABASE_NAME`` for MySQL or ``TENANT_NAME`` for PostgreSQL
and ``TENANT_CACHE_PREFIX`` on the command line, for example:

.. code:: bash

    $ TENANT_DATABASE_NAME=example.com ./manage.py migrate

Don't forget to create the database (MySQL) or the required schema first (PostgreSQL).

That’s it. Because django-db-multitenant does not define any models,
there’s no need to add it to ``INSTALLED_APPS``.

Advantages and Limitations
--------------------------

There is no one-size-fits-all solution for a data modeling problem such
as multi-tenancy (see ‘Alternatives’).

Advantages
~~~~~~~~~~

-  Compatibility: Your Django application doesn’t need any awareness of
   multi-tenancy. Database-level tools (such as ``mysqldump`` or ``pgdump``)
   just work.
-  Isolation: One tenant, one database means there’s no intermingling of
   tenant data (excepted if you share tables with PostgreSQL).
-  Simplicity: Your application schemas don’t need to be cluttered with
   ‘Tenant’ foreign key relationships.
-  Should work well with Django 1.6 connection persistence and
   connection pooling.

Limitations
~~~~~~~~~~~

-  Unorthodox. Django does not expect this kind of dynamic database
   connection tinkering, and there could be unexpected bugs.
-  Limited isolation. Since the same DB credentials are used for all
   tenants, bugs in the mapper (or anywhere else in the app) could cause
   data corruption.
-  A valid database still needs to be specified in ``settings.DATABASE``
   for use when the connection is first established with MySQL (this should be
   fixed eventually).
-  Overhead: requests may add up to one extra query (the
   ``USE <db_name>`` statement for MySQL or the ``SET search_path TO <tenant_name>`` for PostgreSQL).

Alternatives and Further Reading
--------------------------------

-  `django-tenant-schemas <https://github.com/bcarneiro/django-tenant-schemas>`__
   implements a semi-isolated approach using PostgreSQL schemas (and
   inspired this project, as well as the ‘Overview’ section above).

Credits and License
-------------------

Copyright 2013 mike wakerly (opensource@hoho.com)

Licensed under the Apache License, Version 2.0 (the “License”); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an “AS IS” BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
