from django.db.models import Q
from products.models import Product
from products.models.substitution import ProductSubstitution
from products.utils.get_pricing_stores import get_pricing_stores_map
from users.models.cart_item import CartItem
from users.models.cart_substitution import CartSubstitution

class SubstituteManager:
    """
    Manages finding potential product substitutes and creating CartSubstitution instances.
    """
    def __init__(self, product_id: int, store_ids: list[int]):
        if not isinstance(product_id, int):
            raise TypeError("product_id must be an integer.")
        if not isinstance(store_ids, list) or not all(isinstance(sid, int) for sid in store_ids):
            raise TypeError("store_ids must be a list of integers.")
        if not store_ids:
            raise ValueError("store_ids cannot be an empty list.")

        self.product_id = product_id
        self.store_ids = store_ids
        self._original_product = None
        self._potential_product_substitutions = None

    def _get_original_product(self) -> Product | None:
        if self._original_product is None:
            try:
                self._original_product = Product.objects.get(id=self.product_id)
            except Product.DoesNotExist:
                self._original_product = None
        return self._original_product

    def find_potential_product_substitutions(self, limit: int = 5) -> list[ProductSubstitution]:
        """
        Finds potential ProductSubstitution objects for the initialized product and stores.

        Args:
            limit: The maximum number of ProductSubstitution objects to return.

        Returns:
            A list of ProductSubstitution objects. Returns an empty list if the original product
            is not found or if no substitutes are found matching the criteria.
        """
        if self._potential_product_substitutions is not None:
            return self._potential_product_substitutions

        # Resolve member store IDs to their anchor store IDs, since Price rows only
        # exist on anchors (member prices are deleted after group confirmation).
        pricing_map = get_pricing_stores_map(self.store_ids)
        pricing_store_ids = list(set(pricing_map.values()))

        print(f"[SubstituteManager] find_potential_product_substitutions: product_id={self.product_id}, store_ids={self.store_ids}, pricing_store_ids={pricing_store_ids}")

        original_product = self._get_original_product()
        if not original_product:
            print(f"[SubstituteManager] original product not found for id={self.product_id}")
            return []

        substitutions_queryset = ProductSubstitution.objects.filter(
            Q(product_a=original_product) | Q(product_b=original_product)
        ).order_by('level', '-score')

        unfiltered_count = substitutions_queryset.count()
        print(f"[SubstituteManager] ProductSubstitutions before store filter: {unfiltered_count}")

        # Filter by anchor store IDs (the stores that actually hold Price rows)
        substitutions_queryset = substitutions_queryset.filter(
            Q(product_a=original_product, product_b__prices__store__id__in=pricing_store_ids) |
            Q(product_b=original_product, product_a__prices__store__id__in=pricing_store_ids)
        ).distinct()

        self._potential_product_substitutions = list(substitutions_queryset[:limit])
        print(f"[SubstituteManager] after store filter: {len(self._potential_product_substitutions)} substitutions found")
        return self._potential_product_substitutions

    def create_cart_substitutions(self, original_cart_item: CartItem) -> list[CartSubstitution]:
        """
        Creates CartSubstitution instances for the found potential product substitutes,
        linked to the given original CartItem.

        Args:
            original_cart_item: The CartItem for which to create substitutions.

        Returns:
            A list of created CartSubstitution objects.
        """
        if not isinstance(original_cart_item, CartItem):
            raise TypeError("original_cart_item must be an instance of CartItem.")

        found_product_substitutions = self.find_potential_product_substitutions()
        created_cart_substitutions = []

        for ps in found_product_substitutions:
            substitute_product = ps.product_a if ps.product_b.id == self.product_id else ps.product_b
            
            if not CartSubstitution.objects.filter(
                original_cart_item=original_cart_item,
                substituted_product=substitute_product
            ).exists():
                cart_sub = CartSubstitution.objects.create(
                    original_cart_item=original_cart_item,
                    substituted_product=substitute_product,
                    quantity=1,
                    is_approved=False
                )
                created_cart_substitutions.append(cart_sub)

        
        return created_cart_substitutions

    def update_cart_substitution(self, substitution_id: str, is_approved: bool = None, quantity: int = None) -> CartSubstitution | None:
        """
        Updates an existing CartSubstitution instance.

        Args:
            substitution_id: The ID of the CartSubstitution to update.
            is_approved: Optional boolean to set the approval status.
            quantity: Optional integer to set the quantity.

        Returns:
            The updated CartSubstitution object, or None if not found or removed.
        """
        try:
            cart_sub = CartSubstitution.objects.get(id=substitution_id)
            if is_approved is not None:
                cart_sub.is_approved = is_approved
            if quantity is not None:
                cart_sub.quantity = quantity
            cart_sub.save()
            return cart_sub
        except CartSubstitution.DoesNotExist:
            return None

    def remove_cart_substitution(self, substitution_id: str) -> bool:
        """
        Removes a CartSubstitution instance.

        Args:
            substitution_id: The ID of the CartSubstitution to remove.

        Returns:
            True if the substitution was removed, False otherwise.
        """
        try:
            cart_sub = CartSubstitution.objects.get(id=substitution_id)
            cart_sub.delete()
            return True
        except CartSubstitution.DoesNotExist:
            return False
