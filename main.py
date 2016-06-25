#!/usr/bin/env python2

import sys
from argparse import ArgumentParser

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

    return [entry for entry, _ in
            svn_client.list(
                archive_path,
                dirent_fields=dirent_fields | pysvn.SVN_DIRENT_KIND,
                recurse=True
            )
            if entry.kind in allowed_kinds]


def main():
    args = get_argparser().parse_args()
    include_types = set([SvnExternalUrlType[x] for x in args.only_type])
    svn_client = pysvn.Client()

    print >> sys.stderr, "Fetching directory tree..."
    dirs = get_svn_tree(
        svn_client,
        args.archive_path,
        include_files=False,
        dirent_fields=pysvn.SVN_DIRENT_HAS_PROPS
    )

    for dir in dirs:
        print >> sys.stderr, "Checking directory `%s'..." % dir.repos_path

        if not dir.has_props:
            continue

        svn_externals = svn_client.propget(
            "svn:externals",
            args.archive_path + "/" + dir.repos_path
        )
        if not svn_externals:
            # No externals set on this directory.
            continue

        parsed_externals = [x for x in parse_svn_externals(svn_externals.popitem()[1])
                            if not include_types or x.urltype in include_types]
        if parsed_externals:
            print dir.repos_path

            for parsed_external in parsed_externals:
                print "\t%s -> %s\t%s\t[%s]" % (
                    parsed_external.subdir, parsed_external.url, parsed_external.revopt, parsed_external.urltype.name
                )


if __name__ == "__main__":
    sys.exit(main())
