# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt


def canonical_tuple_path(tuple_path):
    """Make a Zope path the smallest possible. Unlike canonical_path
    it takes the path as a tuple.
    """
    canonical_path = []
    for item in tuple_path:
        if item == '..':
            if not canonical_path or not canonical_path[-1]:
                raise ValueError("Invalid path")
            canonical_path.pop()
        elif item != '.':
            if item == '' and canonical_path:
                continue
            canonical_path.append(item)
    return canonical_path


def canonical_path(path):
    """Make a Zope path the smallest possible.
    """
    return '/'.join(canonical_tuple_path(path.split('/')))


def relative_tuple_path(path_orig, path_dest):
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

# BBB
relative_path = relative_tuple_path

def is_inside_path(container_path, content_path):
    """Tell you if the given content_path is located inside the
    container path.
    """
    if len(content_path) < len(container_path):
        return False
    return container_path == content_path[:len(container_path)]


def is_inside_container(container, content):
    """Tell you if a given content is inside the container. This is
    done by a comparaison on the object paths.
    """
    if content is None:
        # The reference is broken
        return False
    return is_inside_path(
        container.getPhysicalPath(),
        content.getPhysicalPath())
