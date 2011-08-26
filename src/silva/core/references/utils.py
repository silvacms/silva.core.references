# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$


def canonical_path(path):
    """Make a Zope path the smallest possible.
    """
    canonical_path = []
    for item in path.split('/'):
        if item == '..':
            if not canonical_path or not canonical_path[-1]:
                raise ValueError("Invalid path")
            canonical_path.pop()
        elif item != '.':
            if item == '' and canonical_path:
                continue
            canonical_path.append(item)
    return '/'.join(canonical_path)


def relative_path(path_orig, path_dest):
    """Takes two path as list of ids and return a new path that is the
    relative path the second against the first.
    """
    path_orig = list(path_orig)
    path_dest = list(path_dest)
    while ((path_orig and path_dest) and
           (path_orig[0] == path_dest[0])):
        path_orig.pop(0)
        path_dest.pop(0)
    result_path = ['..'] * len(path_orig)
    result_path.extend(path_dest)
    if not result_path:
        return ['.']
    return result_path


def is_inside_container(container, content):
    """Tell you if a given content is inside the container. This is
    done by a comparaison on the object paths.
    """
    if content is None:
        # The reference is broken
        return False
    content_path = content.getPhysicalPath()
    container_path = container.getPhysicalPath()
    if len(content_path) < len(container_path):
        return False
    return container_path == content_path[:len(container_path)]
