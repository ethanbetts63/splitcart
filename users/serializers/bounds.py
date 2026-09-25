"""Maximum lengths, declared per field *kind* rather than per field.

Every string a client can send needs a ceiling at the boundary that first
parses it. Without one, a public endpoint is a free write of arbitrary size
into the database, and a hashing endpoint is worse than that: a password field
with no maximum lets a caller hand the site ten megabytes to run PBKDF2 over.

The reason these are *kinds* and not fields is that a table of two hundred
per-field numbers is one nobody consults. A new form asks "what kind of thing
is this" and inherits the answer, so the bound arrives by default instead of
being remembered.

Why this table is here rather than imported
-------------------------------------------
The canonical table is ``freetheplatform.security.bounds``, and
``forms-standard.md`` FORMS-8 holds it equal to the TypeScript one in
``@freetheplatform/web-security`` with a literal comparison in the package's
own suite. splitcart is in neither: it declares no ``freetheplatform`` entry in
``requirements.txt`` and no ``@freetheplatform/*`` entry in
``frontend/package.json``, and ``AGENTS.md`` says adding one is a decision that
applies ``strategy.md``'s tests first -- a larger question than bounding three
forms.

So this is a *mirror*, copied kind for kind and value for value, and
``frontend/src/lib/fieldMax.ts`` is the same mirror on the other side of the
wire. The rule this satisfies is FORMS-6 and FORMS-7: every client string has a
ceiling, and the ceiling is the right kind. The rule it cannot satisfy is
FORMS-8, whose enforcement is a test in a package splitcart does not install --
recorded as ``n/a`` in the conformance ledger with that reason, not as a pass.

``users/tests/serializer_tests/test_bounds.py`` pins every value literally, so
this file cannot drift on its own; what no test here can see is the shared
table changing. When splitcart onboards the ``freetheplatform`` package, delete
this module and import ``freetheplatform.security.bounds`` instead -- the names
are deliberately identical so that is the whole change.

These are ceilings, not product rules. A field whose real limit is tighter
says so locally. What a kind guarantees is that nothing is unbounded.
"""

from types import MappingProxyType

from rest_framework import serializers

#: Kind -> maximum length in characters. Mirrors
#: ``freetheplatform.security.bounds.FIELD_MAX``.
FIELD_MAX = {
    # Identity and contact.
    "name": 120,
    "business_name": 180,
    # 150, not the 254 that SMTP allows, because an address here becomes an
    # account and Django's ``auth.User.username`` column is 150 characters.
    # Two addresses agreeing on their first 150 characters would collide on a
    # unique constraint and the second person would be told they already have
    # an account, with no way forward.
    "email": 150,
    "phone": 40,
    # Django stores its hashes in a 128-character column and its own forms
    # bound the input the same way. The bound is not about password strength;
    # it is about how much data the hasher is asked to chew through.
    "password": 128,
    # Short structured strings.
    "slug": 120,
    # An identifier minted somewhere else: a plate, a VIN, an order reference.
    "reference": 64,
    # A short machine-shaped string whose meaning its own validation supplies:
    # a price or a time typed into a form, a year, an id chosen from a select.
    "token": 32,
    "postcode": 16,
    # Free text, by how much of it a human is expected to write.
    #: One line: an address line, a subject, a label, a cart's name.
    "line": 255,
    # Django's ``URLField`` is 200 characters unless told otherwise. A
    # serializer bound wider than its own column is not a looser rule, it is a
    # 500: validation passes and the write fails.
    "url": 200,
    #: A paragraph typed by a customer into a public form.
    "note": 2000,
    #: Body copy written by staff: a product description, an article.
    "long_text": 20_000,
    #: A stored rich-text document.
    "html": 200_000,
}

#: Read-only, so nothing can loosen every bound in the process at runtime. The
#: TypeScript table is `as const` for the same reason.
FIELD_MAX = MappingProxyType(FIELD_MAX)


def max_length(kind: str) -> int:
    """The ceiling for ``kind``, or a clear failure at import time.

    Raising rather than returning a default is the point: a typo in a kind name
    would otherwise produce an unbounded field that looks bounded.
    """
    try:
        return FIELD_MAX[kind]
    except KeyError:
        raise KeyError(
            f"Unknown field kind {kind!r}. Known kinds: {', '.join(sorted(FIELD_MAX))}. "
            "Add a kind rather than passing a number, and add it to the frontend "
            "table in frontend/src/lib/fieldMax.ts in the same change."
        ) from None


def char(kind: str, **kwargs) -> serializers.CharField:
    """A ``CharField`` bounded by ``kind``."""
    return serializers.CharField(max_length=max_length(kind), **kwargs)


def email(**kwargs) -> serializers.EmailField:
    """An ``EmailField``, which DRF leaves unbounded unless told otherwise."""
    return serializers.EmailField(max_length=max_length("email"), **kwargs)


def password(**kwargs) -> serializers.CharField:
    """A write-only password field with the hashing ceiling applied."""
    kwargs.setdefault("write_only", True)
    kwargs.setdefault("style", {"input_type": "password"})
    return serializers.CharField(max_length=max_length("password"), **kwargs)
