# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = "pymanip"
copyright = "2019, Julien Salort"
author = "Julien Salort"

# The full version, including alpha/beta/rc tags
release = "0.3"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",  # include documentation from docstrings
    "sphinxarg.ext",  # sphinx-argparse generate doc from argparse
    "sphinx.ext.intersphinx",  # link to fluidlab documentation on readthedocs
    "sphinx.ext.viewcode",  # show source code of documented classes and functions
    "sphinx.ext.autosummary",  # generate autodoc summaries
    "sphinx.ext.todo",
]

intersphinx_mapping = {
    "fluidlab": ("https://fluidlab.readthedocs.io/en/latest/", None),
    "cv2": ("https://opencv-python.readthedocs.io/en/latest/", None),
    "numpy": ("https://numpy.readthedocs.io/en/latest/", None),
    "stdlib": ("https://docs.python.org/3/", None),
}

autodoc_mock_imports = [
    "AndorNeo",
    "pymba",
    "win32event",
    "nidaqmx",
    "niScope",
    "PyDAQmx",
    "pyueye",
    "ximea",
    "pyvcam",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

master_doc = "index"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = "alabaster"
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
