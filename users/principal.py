"""What the API says about whoever is signed in.

`freetheplatform.auth` calls this on login and on `GET /api/me/`. splitcart has
no portal and nothing behind a role, so `role` is always `"shopper"` for an
account and staff are not told apart: `is_staff` never crosses the wire, and
nothing on the frontend has a reason to branch on it.
"""


def principal(user):
    return {
        "id": user.pk,
        "email": user.email,
        "full_name": user.full_name,
        "role": "shopper",
    }
