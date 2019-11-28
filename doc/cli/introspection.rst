Session introspection and management
====================================

The sessions created by pymanip use standard formats for storage:

- the synchronous sessions use both HDF5_ and raw ascii files. For a session named `toto`, three files are created: `toto.dat`, `toto.hdf5` and `toto.log`;

- the asynchronous sessions use a SQLite3_ database. For a session name `toto`, one file `toto.db` is created.

The rationale for having three files in the first case is that HDF5 is not designed for repeated access, and it happens sometimes that the file gets corrupted, for example if the program is interrupted while the program was writting to the disk. The ascii files however are opened in `append` mode, so that no data can ever be lost.

We switched to a database format for the newer asynchronous session, because such a format is designed for multiple concurrent access, and each transaction is atomic and can be safely rolled back if an unexpected error occurs. The risk of corruption is much less, and we thought it was no longer necessary to keep the ascii files.

Because all those file formats are simple and documented, it is possible to read and inspect them with standard tools, such as `h5dump` for the synchronous session files, or the `sqlite3` command line tool, but it is impractical to use these tools to quickly check the content of some session file. That is why a simple command line tool is provided.


The main command for introspecting saved session is

.. code-block:: bash

    $ python -m pymanip info session_name

It can read :ref:`asynchronous sessions<AsyncSession>`, as well as synchronous sessions and old-style
OctMI sessions. It is not necessary to happen the filename extensions, e.g. `.db` for asynchronous
sessions.
The command will output the start and end dates of the session, as well as a list of saved
variables.

Two other commands are provided, but they are specific to synchronous sessions which are stored
in HDF5_ file format:

- the `check_hdf` sub-command checks that the ascii and HDF5_ files are identical;

- the `rebuild_hdf` sub-command rebuilds the hdf file from the ascii file. This is useful if the HDF5_ file has been corrupted.

.. _HDF5: https://www.hdfgroup.org/solutions/hdf5

.. _SQLite3: https://www.sqlite.org/version3.html
