# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import tempfile
import subprocess

from five import grok
from zope.component import getUtility, getMultiAdapter
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.traversing.browser import absoluteURL

from silva.core import interfaces
from silva.core.services.utils import walk_silva_tree
from silva.core.references.interfaces import (
    IReferenceService, IReferenceGrapher)


GRAPH_THRESHOLD = 2500


def graphviz_safe_id(string):
    """Create a sensible Graphivz ID.
    """
    if isinstance(string, unicode):
        string = string.encode('utf-8')
    return '"%s"' % string.replace('"', '\\"').replace('\n', '\\n')


def graphviz_type(content):
    """Return a different color for each content type.
    """
    if interfaces.ILinkVersion.providedBy(content):
        return ('salmon2', 'note')
    if interfaces.IImage.providedBy(content):
        return ('deepskyblue', 'oval')
    if interfaces.IAsset.providedBy(content):
        return ('lightskyblue1', 'oval')
    if interfaces.IGhostAware.providedBy(content):
        return ('darkolivegreen3', 'note')
    if interfaces.IIndexer.providedBy(content):
        return ('plum', 'octagon')
    if interfaces.IContainer.providedBy(content):
        return ('silver', 'octagon')
    if interfaces.IPublishable.providedBy(content) or \
            interfaces.IVersion.providedBy(content):
        return ('white', 'note')
    if interfaces.ISilvaObject.providedBy(content):
        return ('white', 'oval')
    return ('white', 'circle')


def graphviz_content_node(content, content_id, request):
    """Return a line describing a content.
    """
    if content is None:
        return ''
    try:
        url = absoluteURL(content, request)
    except:
        url = '#'
    if interfaces.IVersion.providedBy(content):
        zope_id = content.get_content().getId()
    else:
        zope_id = content.getId()
    if interfaces.ISilvaObject.providedBy(content):
        title = content.get_title_or_id()
    else:
        title = content.getId()
    color, shape = graphviz_type(content)
    return '%s [label=%s,URL=%s,tooltip=%s,fillcolor=%s,shape=%s,target=_graphivz];\n' % (
        content_id,
        graphviz_safe_id(zope_id),
        graphviz_safe_id(url),
        graphviz_safe_id(title),
        color, shape)


class Grapher(grok.MultiAdapter):
    grok.adapts(interfaces.ISilvaObject, IBrowserRequest)
    grok.implements(IReferenceGrapher)
    grok.provides(IReferenceGrapher)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def references(self, *kwargs):
        service = getUtility(IReferenceService)
        producer = service.get_references_from
        for content in walk_silva_tree(self.context, version=True):
            for reference in producer(content):
                yield reference

    def dot(self, stream):
        seen = set()
        count = 1
        buffer = 'digraph references {\n'
        buffer += 'node [style=filled,fontsize="9pt",fontname="sans-serif"];\n'
        buffer += '0 [tooltip="references to this element are broken",'
        buffer += 'label="broken",fillcolor=red];\n'


        for reference in self.references():
            source_id = reference.source_id
            if source_id not in seen:
                buffer += graphviz_content_node(
                    reference.source, source_id, self.request)
                seen.add(source_id)
            target_id = reference.target_id
            if target_id not in seen:
                buffer += graphviz_content_node(
                    reference.target, target_id, self.request)
                seen.add(target_id)
            count += 1
            if count > GRAPH_THRESHOLD:
                self.context._p_jar.cacheMinimize()
                stream.write(buffer)
                buffer = ""
                count = 0
        del seen
        buffer += "\n"

        for reference in self.references():
            buffer += "%s->%s [tooltip=%s];\n" % (
                reference.source_id,
                reference.target_id,
                graphviz_safe_id(reference.tags[0]))
            count += 1
            if count > GRAPH_THRESHOLD:
                self.context._p_jar.cacheMinimize()
                stream.write(buffer)
                buffer = ""
                count = 0

        if count:
            stream.write(buffer)
        title = self.context.get_title_or_id()
        stream.write("""
tooltip=%s;
label=%s;
splines=true;
K=0.5;
maxiter=5;
fontsize=10;
}
""" % (graphviz_safe_id("Relations between contents of '%s'" % title),
       graphviz_safe_id(title)))

    def svg(self, stream):
        with tempfile.TemporaryFile() as source:
            self.dot(source)
            source.seek(0)
            fdp = subprocess.Popen(
                ['fdp', '-Tsvg'],
                stdin=source,
                stdout=subprocess.PIPE)

            result = fdp.stdout.read(4096)
            while result:
                stream.write(result)
                result = fdp.stdout.read(4096)


class RootGrapher(Grapher):
    grok.adapts(interfaces.IRoot, IBrowserRequest)

    def references(self):
        service = getUtility(IReferenceService)
        for reference_key in service.references.keys():
            yield service.references[reference_key]


class DotReferenceGraph(grok.View):
    grok.context(interfaces.ISilvaObject)
    grok.name('graph_references.dot')
    grok.require('silva.ReadSilvaContent')

    def render(self):
        self.response.setHeader('Content-Type', 'text/vnd.graphviz')
        grapher = getMultiAdapter(
            (self.context, self.request), IReferenceGrapher)
        grapher.dot(self.response)
        return ''


class SVGReferenceGraph(grok.View):
    grok.context(interfaces.ISilvaObject)
    grok.name('graph_references.svg')
    grok.require('silva.ReadSilvaContent')

    def render(self):
        self.response.setHeader('Content-Type', 'image/svg+xml')
        grapher = getMultiAdapter(
            (self.context, self.request), IReferenceGrapher)
        grapher.svg(self.response)
        return ''
