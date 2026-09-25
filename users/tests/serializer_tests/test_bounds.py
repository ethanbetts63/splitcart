"""The mirrored field-bounds table, pinned.

`users/serializers/bounds.py` is a hand-copy of
`freetheplatform.security.bounds` because splitcart installs neither the
`freetheplatform` package nor `@freetheplatform/web-security`, so FORMS-8's
cross-repo comparison -- a test in that package's own suite -- cannot run here.

What can be held locally is held here: every kind and every value written out
literally, so a bound cannot be widened in passing, and the mirror on the other
side of the wire (`frontend/src/lib/fieldMax.ts`) has the same table to answer
to. What no test in this repository can see is the *shared* table changing;
that is the part recorded as `n/a` in the conformance ledger rather than as a
pass, and it closes the day splitcart depends on the package.
"""

import pytest

from users.serializers.bounds import FIELD_MAX, char, email, max_length, password

#: Copied from `freetheplatform/src/freetheplatform/security/bounds.py` and
#: `freetheplatform/frontend/web-security/src/bounds.ts`, which agree by a test
#: in that package. Changing a number here without changing it there is the
#: drift this pin exists to catch.
SHARED_TABLE = {
    'name': 120,
    'business_name': 180,
    'email': 150,
    'phone': 40,
    'password': 128,
    'slug': 120,
    'reference': 64,
    'token': 32,
    'postcode': 16,
    'line': 255,
    'url': 200,
    'note': 2000,
    'long_text': 20_000,
    'html': 200_000,
}


def test_the_mirror_declares_exactly_the_shared_kinds():
    assert dict(FIELD_MAX) == SHARED_TABLE


def test_the_table_cannot_be_loosened_at_runtime():
    """A plain dict would let any caller widen every bound in the process."""
    with pytest.raises(TypeError):
        FIELD_MAX['password'] = 10_000_000


def test_an_unknown_kind_fails_loudly():
    """A typo must not quietly produce an unbounded field that looks bounded."""
    with pytest.raises(KeyError) as raised:
        max_length('passwrod')
    assert 'passwrod' in str(raised.value)
    assert 'password' in str(raised.value)


def test_the_builders_carry_the_kind_they_name():
    assert char('line').max_length == FIELD_MAX['line']
    assert email().max_length == FIELD_MAX['email']
    assert password().max_length == FIELD_MAX['password']
    assert password().write_only is True


def test_the_frontend_mirror_declares_the_same_table():
    """The other end of the wire, read as text.

    `frontend/src/lib/fieldMax.ts` is the Zod side of the same bounds. It is a
    TypeScript file with no Python importer, so this reads the literals out of
    it -- crude, but it is the only thing standing between the two mirrors
    until splitcart shares a package with the table.
    """
    import re
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[3] / 'frontend' / 'src' / 'lib' / 'fieldMax.ts'
    ).read_text(encoding='utf-8')
    body = source[source.index('FIELD_MAX = {') : source.index('} as const;')]
    declared = {
        kind: int(value.replace('_', ''))
        for kind, value in re.findall(r'^\s*(\w+):\s*([\d_]+),', body, re.MULTILINE)
    }
    assert declared == SHARED_TABLE
