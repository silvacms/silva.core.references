# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import interface


class BrokenReferenceError(ValueError):
    """Exception used to identify broken reference.
    """


class NotSetReferenceError(BrokenReferenceError):
    """Exception used to identify a unset reference.
    """


class IReference(interface.Interface):
    """This object represent a reference to an other object.
    """

    def get():
        """Return the value of the reference or raise
        BrokenReferenceError.
        """

    def query():
        """Return the value of the reference or None.
        """

    def set(value):
        """Set the value of the reference to the given one.
        """

    def url(request):
        """Return the URL of the reference for the given request.
        """
