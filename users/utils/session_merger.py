from users.models import Cart, SelectedStoreList
from .name_generator import generate_unique_name

def merge_anonymous_session(user, anonymous_id):
    """
    Merges an anonymous user's session into an authenticated user's account by 
    creating a new cart and store list.

    Args:
        user: The authenticated user instance.
        anonymous_id: The UUID of the anonymous session.
    """
    if not user or not anonymous_id:
        return

    try:
        # Get the anonymous user's active cart
        anon_cart = Cart.objects.get(anonymous_id=anonymous_id, is_active=True)
        anon_list = anon_cart.selected_store_list

        # Deactivate user's other carts
        Cart.objects.filter(user=user, is_active=True).update(is_active=False)

        # Create a new store list for the user
        new_list_name = "My Store List"
        if anon_list and anon_list.name != 'Default List':
            new_list_name = anon_list.name
        
        unique_list_name = generate_unique_name(SelectedStoreList, {'user': user}, new_list_name)
        new_list = SelectedStoreList.objects.create(user=user, name=unique_list_name)
        if anon_list:
            new_list.stores.set(anon_list.stores.all())

        # Create a new cart for the user, linked to the new list
        new_cart_name = "Cart"
        if anon_cart.name != 'Anonymous Cart':
            new_cart_name = anon_cart.name

        unique_cart_name = generate_unique_name(Cart, {'user': user}, new_cart_name)
        new_cart = Cart.objects.create(
            user=user, 
            name=unique_cart_name, 
            is_active=True, 
            selected_store_list=new_list
        )

        # Move items from the anonymous cart to the new cart
        anon_cart.items.update(cart=new_cart)

        # Delete the old anonymous cart and list
        anon_cart.delete()
        if anon_list:
            anon_list.delete()

    except Cart.DoesNotExist:
        # No anonymous cart to import, do nothing
        pass
