#!/usr/bin/env python3

import os
import subprocess
import sys
from argparse import ArgumentParser

from svn_externals import parse_svn_externals, SvnExternalUrlType


def get_argparser():
    parser = ArgumentParser(description="List all svn:externals properties in a SVN project archive.")

    parser.add_argument(
        "-s", "--svnlook-path",
        default="svnlook",
        help="Path to the `svnlook' binary. Default: `%(default)s'."
    )
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


def get_svn_tree(svnlook_path, archive_path, subtree="/", include_files=True, include_dirs=True):
    proc = subprocess.Popen(
        [svnlook_path, "tree", "--full-paths", "--", archive_path, subtree],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = proc.communicate()

    if proc.returncode:
        raise subprocess.CalledProcessError(
            proc.returncode,
            proc.args,
            stderr
        )

    tree = []
    for line in stdout.splitlines():
        if line.endswith("/"):
            if include_dirs:
                tree.append(line)
        elif include_files:
            tree.append(line)

    return tree


def get_svn_property(svnlook_path, archive_path, propname, node):
    proc = subprocess.Popen(
        [svnlook_path, "propget", "--", archive_path, propname, node],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=dict(os.environ, LC_MESSAGES="C")
    )
    stdout, stderr = proc.communicate()

    if proc.returncode:
        if proc.returncode == 1 and "E200017" in stderr:
            # Property not found.
            return None

        # Else it's another error.
        raise subprocess.CalledProcessError(
            proc.returncode,
            proc.args,
            stderr
        )

    return stdout


def main():
    args = get_argparser().parse_args()
    include_types = set([SvnExternalUrlType[x] for x in args.only_type])

    print("Fetching directory tree...", file=sys.stderr)
    dirs = get_svn_tree(args.svnlook_path, args.archive_path, include_files=False)

    for dir in dirs:
        print("Checking directory `%s'..." % dir, file=sys.stderr)

        svn_externals = get_svn_property(args.svnlook_path, args.archive_path, "svn:externals", dir)
        if not svn_externals:
            # No externals set on this directory.
            continue

        parsed_externals = [x for x in parse_svn_externals(svn_externals)
                            if not include_types or x.urltype in include_types]
        if parsed_externals:
            print(dir)

            for parsed_external in parsed_externals:
                print("\t%s -> %s\t%s\t[%s]" % (
                    parsed_external.subdir, parsed_external.url, parsed_external.revopt, parsed_external.urltype.name
                ))


if __name__ == "__main__":
    sys.exit(main())
