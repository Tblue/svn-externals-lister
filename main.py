#!/usr/bin/env python2
#
# List all svn:externals definitions in a Subversion repository.
# Intended to be used on a Subversion project archive, not a working copy.
#
#
# This file is part of svn-externals-lister (see
# https://github.com/Tblue/svn-externals-lister).
#
# Copyright (c) 2016, Tilman Blumenbach <tilman (at) ax86 (dot) net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list
#    of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this
#    list of conditions and the following disclaimer in the documentation and/or
#    other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

import os.path
import sys
from argparse import ArgumentParser
from urlparse import urlsplit

import pysvn

from svn_externals import parse_svn_externals, SvnExternalUrlType


def get_argparser():
    parser = ArgumentParser(description="List all svn:externals properties in a SVN project archive.")

    parser.add_argument(
        "-t", "--only-type",
        action="append",
        choices=list(SvnExternalUrlType.__members__.keys()),
        default=[],
        help="Only show externals with the given type. Can be specified more than once. Default: Show all types."
    )
    parser.add_argument(
        "-F", "--full-paths",
        action="store_true",
        help="Print full directory paths instead of indenting the contents of a directory."
    )

    parser.add_argument(
        "archive_path",
        help="Path to SVN project archive to operate on."
    )

    return parser


def get_svn_tree(svn_client, archive_path, include_files=True, include_dirs=True, dirent_fields=pysvn.SVN_DIRENT_ALL):
    allowed_kinds = set()

    if include_files:
        allowed_kinds.add(pysvn.node_kind.file)
    if include_dirs:
        allowed_kinds.add(pysvn.node_kind.dir)

    dirs = [(archive_path, True)]
    while dirs:
        dir_path, yield_itself = dirs.pop(0)
        dir_contents = svn_client.list(
            dir_path,
            dirent_fields=dirent_fields | pysvn.SVN_DIRENT_KIND,
            recurse=False
        )

        # Special case: If we are listing the topmost directory, then we need to yield
        # its own SVN node to the caller -- because otherwise, we would never yield it
        # to the caller at all since below, we are only looking at the directory *contents*
        # (and not the topmost directory itself).
        if yield_itself:
            yield dir_contents[0][0]

        # Skip the listed directory itself (index 0). It gets included in its own listing
        # for some reason...
        for node, _ in dir_contents[1:]:
            if node.kind == pysvn.node_kind.dir:
                dirs.append((archive_path + node.repos_path, False))

            if node.kind in allowed_kinds:
                yield node


def main():
    args = get_argparser().parse_args()
    include_types = set([SvnExternalUrlType[x] for x in args.only_type])
    svn_client = pysvn.Client()

    if not urlsplit(args.archive_path).scheme:
        args.archive_path = "file://%s" % os.path.abspath(args.archive_path)

    for node in get_svn_tree(
            svn_client,
            args.archive_path,
            include_files=False,
            dirent_fields=pysvn.SVN_DIRENT_HAS_PROPS
    ):
        print >> sys.stderr, "Checking directory `%s'..." % node.repos_path

        if not node.has_props:
            continue

        svn_externals = svn_client.propget(
            "svn:externals",
            args.archive_path + "/" + node.repos_path
        )
        if not svn_externals:
            # No externals set on this directory.
            continue

        parsed_externals = [x for x in parse_svn_externals(svn_externals.popitem()[1])
                            if not include_types or x.urltype in include_types]
        if parsed_externals:
            if not args.full_paths:
                print node.repos_path

            for parsed_external in parsed_externals:
                if not args.full_paths:
                    subdir = "\t" + parsed_external.subdir
                else:
                    subdir = node.repos_path + "/" + parsed_external.subdir

                print "%s -> %s\t%s\t[%s]" % (
                    subdir, parsed_external.url, parsed_external.revopt, parsed_external.urltype.name
                )


if __name__ == "__main__":
    sys.exit(main())
