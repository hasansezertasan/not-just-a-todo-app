# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Custom syrupy snapshot extensions."""

from syrupy.extensions.single_file import SingleFileSnapshotExtension


class PNGImageExtension(SingleFileSnapshotExtension):
    _file_extension = "png"


class HTMLExtension(SingleFileSnapshotExtension):
    _file_extension = "html"
