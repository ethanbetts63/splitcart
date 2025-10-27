def generate_unique_name(model_class, owner_filter, base_name):
    """
    Generates a unique name for a model instance by appending an incrementing number.

    Args:
        model_class: The model class to check against (e.g., Cart, SelectedStoreList).
        owner_filter: A Q object or dictionary for filtering by owner (user or anonymous_id).
        base_name: The desired base name for the object.

    Returns:
        A unique name string.
    """
    # First, check if the base name itself is available
    if not model_class.objects.filter(owner_filter, name=base_name).exists():
        return base_name

    # If not, start appending numbers
    i = 1
    while True:
        name = f"{base_name} #{i}"
        if not model_class.objects.filter(owner_filter, name=name).exists():
            return name
        i += 1
