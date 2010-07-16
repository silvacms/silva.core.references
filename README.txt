=====================
silva.core.references
=====================

``silva.core.references`` defines directed references between a source
and target. With the help of a central catalog, you have the
possibility to query the references in both direction: who is the
target if I am the source, and who is the source if I am the target.

References are tagged with different names, and can be
found by searching on one of those names.

Unless you use weak references, you can't remove an content which is a
target of a reference, you will get an error. If you used a weak
reference, the source will be removed.

This extension provides you with a set of fields and widgets that can
be used in forms.
