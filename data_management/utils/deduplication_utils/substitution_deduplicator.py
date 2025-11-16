def deduplicate_substitutions(subs_data: list) -> list:
    """
    De-duplicates a list of substitution dictionaries.

    This function removes both direct duplicates and symmetrical duplicates,
    where (product_a, product_b) is considered the same as (product_b, product_a).

    Args:
        subs_data: A list of substitution dictionaries, where each dict
                   is expected to have 'product_a' and 'product_b' keys.

    Returns:
        A new list containing only the unique substitutions.
    """
    seen_keys = set()
    deduplicated_subs = []
    for sub in subs_data:
        try:
            # Create a sorted tuple to handle symmetrical duplicates
            key = tuple(sorted((sub['product_a'], sub['product_b'])))
            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated_subs.append(sub)
        except (KeyError, TypeError):
            # Skip any malformed substitution entries gracefully
            continue
    return deduplicated_subs
