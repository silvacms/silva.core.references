# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from silva.core import conf as silvaconf

silvaconf.extension_name('silva.core.references')
silvaconf.extension_title('Silva Core References')
silvaconf.extension_system()

# Use our own KeyReference implementation.
CLASS_CHANGES = {
    'five.intid.keyreference KeyReferenceToPersistent':
        'silva.core.references.keyreference KeyReferenceToIItem',
    }
