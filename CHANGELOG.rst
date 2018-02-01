Changelog
=========

v0.3.2 (2018-02-01)
-------------------

- Fix packaging

v0.3.1 (2018-02-01)
-------------------

- Pylint
- Improve passing of arguments to logger in MySQL backend

v0.3.0 (2018-02-01)
-------------------

- Change API of mapper to pass tenant_name to get_db_name
- Add new Tests section in the documentation
- Rename dbname to db_name for consistency with tenant_name
- Fix bug from v2.0 on signature of get_cache_prefix

The API of the mapper has been modified to speed up parsing
and for consistency:

- ``get_dbname()`` has been renamed to ``get_db_name()``
- ``get_db_name()`` receives ``request`` and a new ``tenant_name`` argument
- ``get_cache_prefix()`` receives ``request`` and new ``tenant_name`` and
  ``db_name`` arguments

v0.2.1 (2017-11-21)
-------------------

- Fixed package name in setup.py

v0.2.0 (2017-11-20)
-------------------

- New PostgreSQL backend
- Improved documentation
- Examples of mappers are provided in the repository
- update_from_env arguments are now optional
- New setup.py based on Human's Ultimate Guide to setup.py
- Remove Python 2.6 support

v0.1.3 (2016-09-10)
-------------------

-  Django 1.10 compatibility
   (`#8 <https://github.com/mik3y/django-db-multitenant/pull/8>`__)

v0.1.2 (2014-05-14)
-------------------

*Note:* This version was not properly tagged/released. The pypi source
distribution corresponds to commit ``96795a5`` with commit ``f1b3320``
cherry-picked into it.

-  Added ``update_from_env`` convenience function.

v0.1.1 (2013-07-24)
-------------------

-  Fixed missing exception during error (issue #1).

v0.1.0 (2013-07-09)
-------------------

-  Initial release.
