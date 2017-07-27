# coding=utf-8

"""
Enables protocol buffer support despite conflicting root package.

Notes
-----
Taken from App Engine Python Google Group. View the `original thread`_.

.. _original thread: https://groups.google.com/forum/
        ?fromgroups=#!topic/google-appengine/25EO1Arklfw

"""

import os
import sys


BASE_PACKAGE = 'google'


def FixImports(*packages):
    topdir = os.path.dirname(__file__)

    def ImportPackage(full_package):
        """Import a fully qualified package."""
        imported_module = __import__(full_package, globals(), locals())

        # Check if the override path already exists for the module; if it does,
        # that means we've already fixed imports.
        original_module = sys.modules[full_package]
        lib_path = os.path.join(topdir, full_package.replace('.', '/'))

        if lib_path not in original_module.__path__:
        # Insert after runtime path, but before anything else
            original_module.__path__.insert(1, lib_path)

    ImportPackage(BASE_PACKAGE)

    for package in packages:
        # For each package, we need to import all of its parent packages.
        dirs = package.split('.')
        full_package = BASE_PACKAGE
        for my_dir in dirs:
            full_package = '%s.%s' % (full_package, my_dir)
            ImportPackage(full_package)
