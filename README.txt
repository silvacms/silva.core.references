=====================
silva.core.references
=====================

``silva.core.references`` defines directed references between a source
and target. However you still have the possibility with the help of a
central catalog to query the references in both direction: who is the
target if I am the source, and who is the source if I am the target.

References are tagged can be tagged with different names, and can be
lookup by using one of those names.

By default you don't have the right to remove a content if it is the
target of a existing reference. However by applying a special
interface on your reference, you can trigger the deletion of the
source at the same time that the target is deleted.

Limitation: Don't try to break the rule explained above if you just
created the reference in the same request that you are trying to break
it.

