# In file: stores/utils/recommend_category_links.py

"""
Generates recommendations for linking equivalent categories across stores.

This is a semi-automated data curation tool. It finds categories from different
stores with similar names and hierarchy levels, creating a list of potential
matches for an administrator to review and approve manually.

Args:
    category_ids (list[int], optional): A list of specific, newly created
        Category IDs to generate recommendations for. If None, it can be
        configured to run on all un-linked categories.

Returns:
    dict: A dictionary where keys are the primary keys of the source categories
        and values are a list of recommended equivalent category IDs,
        potentially with a confidence score. This data can then be used to
        render a confirmation page in the Django admin.

Logic Flow:
    1.  For each target category, identify a pool of potential matches from
        other stores.
    2.  Filter this pool to include only categories at a similar hierarchy depth.
    3.  Use fuzzy string matching on the category names to get a similarity score.
    4.  (Advanced) Boost the score if the parents of the two categories are
        already linked as equivalents.
    5.  Return a list of recommendations that exceed a confidence threshold.
"""