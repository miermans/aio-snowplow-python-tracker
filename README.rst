======================================================
asyncio Python Analytics for Snowplow
======================================================
.. image:: https://github.com/miermans/aio-snowplow-python-tracker/actions/workflows/ci.yml/badge.svg
    :alt: Build Status
    :target: https://github.com/miermans/aio-snowplow-python-tracker/actions
.. image:: https://coveralls.io/repos/github/miermans/aio-snowplow-python-tracker/badge.svg?branch=main
    :alt: Test Coverage
    :target: https://coveralls.io/github/miermans/aio-snowplow-python-tracker?branch=main
.. image:: http://img.shields.io/badge/license-Apache--2-blue.svg?style=flat
    :target: http://www.apache.org/licenses/LICENSE-2.0

|

.. image:: https://img.shields.io/pypi/v/aio-snowplow-tracker
    :alt: Pypi Snowplow Tracker
    :target: https://pypi.org/project/aio-snowplow-tracker/
.. image:: https://img.shields.io/pypi/pyversions/aio-snowplow-tracker
    :alt: Python Versions
    :target: https://pypi.org/project/aio-snowplow-tracker/
.. image:: https://img.shields.io/pypi/dm/aio-snowplow-tracker
    :alt: Monthly Downloads
    :target: https://pypi.org/project/aio-snowplow-tracker/


Overview
########

This is a fork of to the official `Snowplow Python Tracker`_ that leverages asyncio_ for high-performance event tracking.

.. _`Snowplow Python Tracker`: https://github.com/snowplow/snowplow-python-tracker
.. _asyncio: https://realpython.com/async-io-python/

With this tracker you can collect event data from your Python-based applications, games or Python web servers/frameworks.

Example
#############

.. code-block:: python

    from aio_snowplow_tracker import Tracker, Emitter, Subject
    import asyncio

    async def main():
        e = Emitter('d3rkrsqld9gmqf.cloudfront.net')
        s = Subject().set_user_id('5432')
        t = Tracker(e, subject=s, app_id='example-app')
        await t.track_page_view('http://example.com', 'Title')

    asyncio.run(main())


Installation
#############
To install the Snowplow Python Tracker locally, assuming you already have Pip installed:

.. code-block:: shell

    $ pip install snowplow-tracker --upgrade

To install the Snowplow Tracker with extras:

.. code-block:: shell

    # Redis extra
    $ pip install snowplow-tracker[redis]
    # Celery extra
    $ pip install snowplow-tracker[celery]


Find out more
#############
The official Snowplow Python Tracker documentation is applicable to this library as well, with some minor changes:

1. :code:`import aio_snowplow_tracker` instead of :code:`import snowplow_tracker`.

2. :code:`await` Tracker calls.

+---------------------------------+-----------------------------------+
| Technical Docs                  | Contributing                      |
+=================================+===================================+
| |techdocs|_                     | |contributing|                    |
+---------------------------------+-----------------------------------+
| `Technical Docs`_               | `Contributing`_                   |
+---------------------------------+-----------------------------------+

.. |techdocs| image:: https://d3i6fms1cm1j0i.cloudfront.net/github/images/techdocs.png
.. |setup| image:: https://d3i6fms1cm1j0i.cloudfront.net/github/images/setup.png
.. |contributing| image:: https://d3i6fms1cm1j0i.cloudfront.net/github/images/contributing.png

.. _techdocs: https://docs.snowplowanalytics.com/docs/collecting-data/collecting-from-own-applications/python-tracker/

.. _`Technical Docs`: https://docs.snowplowanalytics.com/docs/collecting-data/collecting-from-own-applications/python-tracker/
.. _`Contributing`: https://github.com/miermans/aio-snowplow-python-tracker/blob/master/CONTRIBUTING.md

Maintainer Quickstart
#######################

Assuming pyenv_ is installed

::

   host$ git clone git@github.com:snowplow/snowplow-python-tracker.git
   host$ cd snowplow-python-tracker
   host$ pyenv install 3.7.11 && pyenv install 3.8.11 && pyenv install 3.9.6
   host$ ./run-tests.sh deploy
   host$ ./run-tests.sh test

.. _pyenv: https://github.com/pyenv/pyenv

Copyright and license
#####################

The Snowplow Python Tracker is copyright 2013-2021 Snowplow Analytics Ltd.

Licensed under the `Apache License, Version 2.0`_ (the "License");
you may not use this software except in compliance with the License.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


.. _Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0
