# Parse an SVN externals definition (or multiple definitions; one per line).
#
# Supports old-style externals definitions (SVN 1.4 or older) and new-style
# definitions (SVN 1.5 or newer).
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

import shlex
from collections import namedtuple
from urlparse import urlsplit

# Available from PyPI as "enum34".
from enum import Enum


SvnExternal = namedtuple("SvnExternal", "subdir revopt url urltype")


class SvnExternalUrlType(Enum):
    ABSOLUTE = 0
    RELATIVE_DIR = 1
    RELATIVE_REPO_ROOT = 2
    RELATIVE_SCHEME = 3
    RELATIVE_SRV_ROOT = 4
    RELATIVE_SIBLING_REPO = 5


def _get_url_type(url):
    parsed_url = urlsplit(url)

    if parsed_url.scheme:
        # svn://foo.bar/baz etc. (everything with an URL scheme)
        return SvnExternalUrlType.ABSOLUTE
    elif parsed_url.netloc:
        # //foo.bar/baz
        return SvnExternalUrlType.RELATIVE_SCHEME
    elif parsed_url.path.startswith("/"):
        return SvnExternalUrlType.RELATIVE_SRV_ROOT
    elif parsed_url.path.startswith("^/../"):
        return SvnExternalUrlType.RELATIVE_SIBLING_REPO
    elif parsed_url.path.startswith("^/"):
        return SvnExternalUrlType.RELATIVE_REPO_ROOT
    else:
        return SvnExternalUrlType.RELATIVE_DIR


def parse_svn_externals(externals_str):
    externals = []

    for line in externals_str.splitlines():
        parts = shlex.split(line)

        if len(parts) == 0:
            # Empty line, ignore.
            continue
        elif parts[0].startswith("#"):
            # Skip comments
            continue
        elif len(parts) == 2:
            # SVN < 1.5:    <subdir> <abs_url>
            # SVN >= 1.5:   <abs_or_rel_url> <subdir>
            part1_url_type = _get_url_type(parts[1])
            if part1_url_type == SvnExternalUrlType.ABSOLUTE:
                # SVN < 1.5
                externals.append(
                    SvnExternal(parts[0], "", parts[1], part1_url_type)
                )
            else:
                # Otherwise this is an SVN >= 1.5 externals definition.
                externals.append(
                    SvnExternal(parts[1], "", parts[0], _get_url_type(parts[0]))
                )
        elif len(parts) == 3:
            # SVN < 1.5:    <subdir> <revopt> <abs_url>
            # SVN >= 1.5:   <revopt> <abs_or_rel_url> <subdir>
            part2_url_type = _get_url_type(parts[2])
            if part2_url_type == SvnExternalUrlType.ABSOLUTE:
                # SVN < 1.5
                externals.append(
                    SvnExternal(parts[0], parts[1], parts[2], part2_url_type)
                )
            else:
                # Else it is an SVN >= 1.5 externals definition
                externals.append(
                    SvnExternal(parts[2], parts[0], parts[1], _get_url_type(parts[1]))
                )
        else:
            # Invalid line.
            raise ValueError("Expected 2 or 3 fields in SVN externals definition '%s'" % line)

    return externals
