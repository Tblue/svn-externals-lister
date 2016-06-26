#!/usr/bin/awk -f
#
# Convert output with indented directory contents to "full paths" (non-indented) style.
#
# Useful if you forgot to specify the `--full-paths' option.

BEGIN {
    FS = "\t"
    current_dir = ""
}

{
    if ($1 == "") {
        sub(/^\t/, "/")
        print current_dir $0
    } else {
        current_dir = $0
    }
}
