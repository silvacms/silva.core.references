# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from OFS.interfaces import IItem
from dolmen.relations.catalog import RelationCatalog
from dolmen.relations.container import RelationsContainer
from five import grok
from zc.relation.interfaces import ICatalog
from zc.relation.queryfactory import TransposingTransitive
from zope import component
from zope.lifecycleevent.interfaces import (
    IObjectCreatedEvent, IObjectCopiedEvent)
import uuid

from silva.core import conf as silvaconf
from silva.core.references.interfaces import (
    IReferenceService, IReferenceValue, IReferenceGrapher)
from silva.core.references.reference import (
    ReferenceValue, get_content_id, relative_path)
from silva.core.services.base import SilvaService
from silva.core.views import views as silvaviews


class ReferenceService(SilvaService):
    """This service track existing references between content
    """
    meta_type = 'Silva Reference Service'
    grok.implements(IReferenceService)
    silvaconf.icon('service.png')

    manage_options = (
        {'label':'Broken references', 'action':'manage_brokenreferences'},
        ) + SilvaService.manage_options

    def __init__(self, id):
        super(ReferenceService, self).__init__(id)
        self.catalog = RelationCatalog()
        self.references = RelationsContainer()

    def __create_reference(self, content_id, name=None, target_id=0,
            tags=None, factory=ReferenceValue):
        """Create and add a new reference
        """
        if not IReferenceValue.implementedBy(factory):
            raise TypeError('Wrong factory %s for reference, '
                'it should implement IReferenceValue' % factory)
        if tags is None:
            tags = []
        if name is not None:
            tags.append(name)
        reference = factory(content_id, target_id, tags=tags)
        reference_id = str(uuid.uuid4())
        self.references[reference_id] = reference
        return reference

    def new_reference(self, content, name=None, factory=ReferenceValue):
        """Create a new reference.
        """
        content_id = get_content_id(content)
        return self.__create_reference(content_id, name=name, factory=factory)

    def get_reference(self, content, name=None, add=False,
            factory=ReferenceValue):
        """Retrieve an existing reference.
        """
        content_id = get_content_id(content)
        references = list(self.catalog.findRelations(
            {'source_id': content_id, 'tag': name}))
        if not len(references):
            if add is True:
                return self.__create_reference(
                    content_id, name=name, factory=factory)
            return None
        return references[0]

    def get_references_to(self, content, name=None, depth=1):
        """Get all references to the given content.
        """
        content_id = get_content_id(content)
        query = {'target_id': content_id}
        options = {}
        if name is not None:
            query['tag'] = name
        if depth:
            options['queryFactory'] = TransposingTransitive(
                'source_id', 'target_id')
            options['maxDepth'] = depth
        return self.catalog.findRelations(query, **options)

    def get_references_from(self, content, name=None, depth=0):
        """Get all references from the given content.
        """
        content_id = get_content_id(content)
        query = {'source_id': content_id}
        options = {}
        if name is not None:
            query['tag'] = name
        if depth:
            options['queryFactory'] = TransposingTransitive(
                'souce_id', 'target_id')
            options['maxDepth'] = depth
        return self.catalog.findRelations(query, **options)

    def get_references_between(self, source, target, name=None):
        query = {'source_id': get_content_id(source),
                 'target_id': get_content_id(target)}
        if name is not None:
            query['tag'] = name
        return self.catalog.findRelations(query)

    def delete_reference(self, content, name=None):
        """Lookup and remove a reference.
        """
        reference = self.get_reference(content, name=name, add=False)
        if reference is not None:
            del self.references[reference.__name__]

    def delete_reference_by_name(self, name):
        del self.references[name]

    def clone_references(
        self, content, clone, copy_source=None, copy_target=None):
        """Clone content reference to clone content unless source and
        target are both in container.
        """
        content_id = get_content_id(content)
        clone_id = get_content_id(clone)
        references = self.catalog.findRelations({'source_id': content_id})
        for reference in references:
            clone_target_id = reference.target_id
            if copy_source is not None and clone_target_id:
                target_path = reference.target.getPhysicalPath()
                copy_source_path = copy_source.getPhysicalPath()
                if (len(target_path) >= len(copy_source_path) and
                    target_path[:len(copy_source_path)] == copy_source_path):
                    # Reference target is in copy_source, so we need to
                    # set target to the corresponding one in
                    # copy_target.
                    assert copy_target is not None
                    relative_target_path = relative_path(
                        copy_source_path, target_path)
                    if relative_target_path != ['.']:
                        clone_target = copy_target.unrestrictedTraverse(
                            relative_target_path)
                    else:
                        clone_target = copy_target
                    clone_target_id =  get_content_id(clone_target)
            self.__create_reference(
                clone_id,
                target_id=clone_target_id,
                tags=list(reference.tags))


class ListBrokenReference(silvaviews.ZMIView):
    grok.name('manage_brokenreferences')

    def update(self):
        self.broken_targets = list(self.context.catalog.findRelations(
                {'target_id': 0}))
        self.broken_sources = list(self.context.catalog.findRelations(
                {'source_id': 0}))


class ReferenceGraph(silvaviews.ZMIView):
    """This view create a graphivz file with all contained references.
    """
    grok.name('graph.svg')

    def render(self, only_in=None):
        root = self.context.get_root()
        if only_in is not None:
            root = root.restrictedTraverse(only_in)

        self.response.setHeader('Content-Type', 'text/vnd.graphviz')
        grapher = component.getMultiAdapter(
            (root, self.request), IReferenceGrapher)
        grapher.dot(self.response)
        return ''


@grok.subscribe(IReferenceService, IObjectCreatedEvent)
def configure_reference_service(service, event):
    """Configure the reference after it have been created. Register
    the relation catalog to the root local site.
    """
    root = service.get_root()
    sm = root.getSiteManager()
    sm.registerUtility(service.catalog, ICatalog)


@grok.subscribe(IItem, IObjectCopiedEvent)
def clone_reference(content, event):
    """Clone object references when the object is cloned.
    """
    service = component.queryUtility(IReferenceService)
    if service is not None:
        # This event is called for all content contained in
        # event.object. We need to find the corresponding original
        # content matching content to call clone_references.
        copy_path = content.getPhysicalPath()[1:]
        original = event.original
        if len(copy_path):
            # basically event.object != content. content is the copy
            # of event.original, so the relative path event.object to
            # content should exists as well from event.original.
            original = original.unrestrictedTraverse(copy_path)
        service.clone_references(
            original, content,
            copy_source=event.original, copy_target=event.object)
