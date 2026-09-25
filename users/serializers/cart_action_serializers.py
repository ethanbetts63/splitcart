"""Request serializers for `CartViewSet`'s custom actions.

Every one of these actions used to read `request.data.get(...)` straight into a
model field or a bulk write. `rename` in particular assigned `cart.name` with no
validation at all, so an oversized name was either a truncated row (MySQL in
non-strict mode) or a 500, and a malformed `cart_id` was a 500 either way.

Bounds here are the model column where one exists, and otherwise a ceiling on
how much work one request may ask for.
"""

from rest_framework import serializers

from users.models import Cart

# Cart.name's column width. Stated rather than inherited so a bound wider than
# the column -- which is a failed INSERT, not a looser rule -- cannot drift in.
CART_NAME_MAX_LENGTH = Cart._meta.get_field("name").max_length

# A shopping list, not a bulk import. Each newly created item also runs a
# substitute search, so the list length is a CPU bound as much as a row count.
MAX_SYNC_ITEMS = 300
# Substitutes offered for one item.
MAX_SYNC_SUBSTITUTIONS = 50
# Nobody buys a thousand of anything through this interface.
MAX_ITEM_QUANTITY = 999
# The optimiser solves one LP per entry.
MAX_OPTIMIZE_OPTIONS = 10
MAX_COMPANIES_PER_OPTION = 20


class CartRenameSerializer(serializers.Serializer):
    """`POST /api/carts/rename/`."""

    cart_id = serializers.UUIDField()
    new_name = serializers.CharField(max_length=CART_NAME_MAX_LENGTH, trim_whitespace=True)


class CartSwitchActiveSerializer(serializers.Serializer):
    """`POST /api/carts/switch-active/`."""

    cart_id = serializers.UUIDField()


class CartSyncSubstitutionSerializer(serializers.Serializer):
    """One substitute's approval state, as sent back by the client."""

    id = serializers.UUIDField()
    is_approved = serializers.BooleanField(required=False)
    quantity = serializers.IntegerField(required=False, min_value=1, max_value=MAX_ITEM_QUANTITY)


class CartSyncItemSerializer(serializers.Serializer):
    """One line of the client's cart."""

    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_ITEM_QUANTITY)
    substitutions = serializers.ListField(
        child=CartSyncSubstitutionSerializer(),
        required=False,
        allow_empty=True,
        max_length=MAX_SYNC_SUBSTITUTIONS,
    )


class CartSyncSerializer(serializers.Serializer):
    """`POST /api/carts/sync/` -- the client's whole cart state in one body."""

    cart_id = serializers.UUIDField()
    items = serializers.ListField(
        child=CartSyncItemSerializer(),
        allow_empty=True,
        max_length=MAX_SYNC_ITEMS,
    )


class CartOptimizeSerializer(serializers.Serializer):
    """`POST /api/carts/<pk>/optimize/`."""

    max_companies_options = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=MAX_COMPANIES_PER_OPTION),
        required=False,
        allow_empty=False,
        max_length=MAX_OPTIMIZE_OPTIONS,
        # A callable, so the default list cannot be mutated between requests.
        default=lambda: [2, 3, 4],
    )
