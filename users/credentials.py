"""Turning the login form's fields into what the token serializer reads.

`USERNAME_FIELD` is `email` here, so simplejwt's `TokenObtainPairSerializer`
declares an `email` field rather than a `username` one, while the package's
`LoginView` looks the account up through `username`. The shared resolvers return
only `username`, which is the right shape for every sibling and a missing
required field for this one. So this returns the identifier under both names.

The address is resolved to the account's stored spelling, ignoring case, the
way allauth matched it before. A miss falls through unchanged, so an unknown
address fails in the same place and the same way as a wrong password. Nothing
here decides whether the credentials are correct; the serializer does.
"""

from django.contrib.auth import get_user_model


def email_credentials(data):
    email = (data.get("email") or data.get("username") or "").strip()
    matched = get_user_model().objects.filter(email__iexact=email).first() if email else None
    if matched is not None:
        email = matched.email
    return {"username": email, "email": email, "password": data.get("password") or ""}
