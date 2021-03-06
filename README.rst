=================
librarian-content
=================

A meta-component that provides an API for accessing the content library.

Installation
------------

The component has the following dependencies:

- outernet_metadata_
- librarian-core_
- fsal_

To enable this component, add it to the list of components in librarian_'s
`config.ini` file, e.g.::

    [app]
    +components =
        librarian_content

Configuration
-------------

``library.refresh_rate``
    The interval of performing checks for new content, specified in seconds.
    Example::

        [library]
        refresh_rate = 60

``library.contentdir``
    A filesystem path pointing to a location where content files are to be
    found. Example::

        [library]
        contentdir = /mnt/data/downloads

``fsal.socket``
    Path to the socket that is created by fsal. Example::

        [fsal]
        socket = /var/run/fsal.ctrl

.. _librarian: https://github.com/Outernet-Project/librarian
.. _librarian-core: https://github.com/Outernet-Project/librarian-core
.. _outernet_metadata: https://github.com/Outernet-Project/outernet_metadata
.. _fsal: https://github.com/Outernet-Project/fsal
