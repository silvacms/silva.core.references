# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from silva.core.services.base import SilvaService

from BTree import IOBTree


class IntegrityService(SilvaService):
    """This service track existing references between content.
    """

    def __init__(self):
        self.__backward_references = IOBTree()
        self.__forward_references = IOBTree()
        self.__brokens = []

    def is_deletable(self, content):
        return False

    def track_reference(self, source_id, target_id):
        pass

    def untrack_reference(self, source_id, target_id):
        pass



