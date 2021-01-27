"""Xiseq file parser (:mod:`pymanip.video.ximea.xiseq`)
=======================================================

.. autoclass:: XiseqFile
   :members:
   :private-members:

"""

from functools import cached_property
from pathlib import Path
import xml.etree.ElementTree as ET


class XiseqFile:
    """Simple parser for Ximea Xiseq file.

    :param filepath: path to file
    :type filepath: :class:`~pathlib.Path` or str

    """

    def __init__(self, filepath):
        """Constructor method
        """
        self.filepath = filepath

    @cached_property
    def tree(self):
        return ET.parse(self.filepath)

    @cached_property
    def metadata_tree(self):
        metadata, = self.tree.findall("imageMetadata")
        return metadata

    @cached_property
    def metadata(self):
        return {child.tag: child.text for child in self.metadata_tree}

    def files(self):
        """Iterate through files in sequence. Yields a dictionnary with keys
        ``timestamp``, ``frame`` and ``filename``.
        """
        for f in self.tree.findall("file"):
            yield {
                "timestamp": f.get("timestamp"),
                "frame": f.get("frame"),
                "filename": f.text,
            }
