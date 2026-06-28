"""
PathClassifier: assigns path_type, canonical_key, and primary_category_slug
to a company-specific category path.

path_type values:
  canonical_taxonomy  — a real grocery browse hierarchy
  dietary             — a dietary/lifestyle filter (Vegan, Gluten Free, Halal, etc.)
  promotion           — a promotional/deals overlay (Down Down, Bonus Credit, etc.)
  seasonal            — time-limited seasonal overlay (Christmas, Limited Time Only, etc.)
  brand_collection    — a named-brand section (Heinz, Nescafe, etc.)
  merchandising       — cross-cutting merchandising facets (Lunch Box, Easy Meals, etc.)
  unknown             — unrecognized root

canonical_key: a normalized path slug for cross-company grouping.
  Format: "slug/slug/slug". Nodes are normalized via category_node_equivalences.json
  when that file exists (produced by apply_category_decisions). Without the file,
  falls back to slugifying raw node names (company-specific).

primary_category_slug: slug of the PrimaryCategory to assign.
  Derived by scanning path nodes (leaf → root) through CATEGORY_MAPPINGS.
  Empty string means the path is excluded or unmappable.
"""

import json
import os
from django.utils.text import slugify
from data_management.data.category_mappings import CATEGORY_MAPPINGS

_EQUIVALENCES_PATH = 'data_management/data/category_node_equivalences.json'
_ASSIGNMENTS_PATH = 'data_management/data/canonical_category_assignments.json'
_equivalences: dict | None = None
_assignments: dict | None = None


def _load_equivalences() -> dict:
    global _equivalences
    if _equivalences is not None:
        return _equivalences
    if os.path.exists(_EQUIVALENCES_PATH):
        with open(_EQUIVALENCES_PATH, 'r', encoding='utf-8') as f:
            _equivalences = json.load(f)
    else:
        _equivalences = {}
    return _equivalences


def _load_assignments() -> dict:
    global _assignments
    if _assignments is not None:
        return _assignments
    if os.path.exists(_ASSIGNMENTS_PATH):
        with open(_ASSIGNMENTS_PATH, 'r', encoding='utf-8') as f:
            _assignments = json.load(f)
    else:
        _assignments = {}
    return _assignments


def _normalize_node(company_name: str, node: str, depth_from_leaf: int) -> str:
    """
    Return the canonical slug for a node, using confirmed equivalences if available.
    Falls back to slugify(node).
    """
    eq = _load_equivalences()
    company_eq = eq.get(company_name, {})
    node_eq = company_eq.get(node, {})
    canon = node_eq.get(str(depth_from_leaf))
    return canon if canon else slugify(node)

_SEASONAL_ROOTS = frozenset({
    'christmas',
    'seasonal',
    'limited time only',
    'special buys',
    'weekly specials',
    'easter',
    'halloween',
    'chinese new year',
})

_PROMOTIONAL_ROOTS = frozenset({
    'down down',
    'bonus credit products',
    'everyday market',
    'big night in',
    'front of store',
    'everyday rewards',
    'specials',
})

_DIETARY_ROOTS = frozenset({
    'dietary & world foods',
    'vegan & vegetarian',
    'gluten free',
    'halal',
    'kosher',
    'organic',
    'free from',
    'dietary needs',
    'plant based',
    'low carb & low sugar',
    'sugar free',
    'fat free',
    'peanut free',
    'soy free',
    'egg free',
    'nut free',
    'fodmap friendly',
    'health foods',
    'health & wellness',
})

_BRAND_ROOTS = frozenset({
    'nescafe',
    'heinz',
    'barilla',
    'jacobs creek',
    'grant burge',
    'cadbury',
    'kinder',
    'lindt',
    "m&m's",
    'mars',
    'milky way',
    'oreo',
    'pringles',
    'doritos',
    'shapes',
    'sakata',
    'jatz',
    'kettle',
    'cc\'s',
    'smith\'s',
    'twisties',
    'skittles',
    'connoisseur',
    'peters',
    'darrell lea',
    'the natural confectionery co.',
    'life savers',
    "reese's",
    "jack link's",
    'pepsi',
    'fanta',
    'sprite',
    'coca-cola zero sugar',
    'mount franklin lightly sparkling',
})

_MERCHANDISING_ROOTS = frozenset({
    'lunch box',
    'dinner',
    'breakfast',
    'breakfast & spreads',
    'easy meals',
    'meal kits',
    'meal kits & ingredients',
    'meal occasions',
    'lunch, dinner & entertaining',
    'back to school',
    'school breakfast',
    'school lunches',
    'air fry guy',
    'air fryer ready',
    'entertaining',
    'bbq ready',
    'brands we love',
    'kids snacks & lunch',
    'healthier lunch box',
    'microwave ready',
})

# Normalize company name to CATEGORY_MAPPINGS key
_COMPANY_KEY_MAP = {
    'coles': 'Coles',
    'woolworths': 'Woolworths',
    'aldi': 'Aldi',
}


def _classify_path_type(path: list) -> str:
    if not path:
        return 'unknown'
    root = path[0].lower().strip()
    if root in _SEASONAL_ROOTS:
        return 'seasonal'
    if root in _PROMOTIONAL_ROOTS:
        return 'promotion'
    if root in _DIETARY_ROOTS:
        return 'dietary'
    if root in _BRAND_ROOTS:
        return 'brand_collection'
    if root in _MERCHANDISING_ROOTS:
        return 'merchandising'
    return 'canonical_taxonomy'


def _find_primary_category_slug(company_name: str, path: list) -> str:
    """
    Walk the path from leaf to root, returning the first matching primary category slug.

    Checks canonical_category_assignments.json first (AI-assigned, canonical slugs).
    A null value in the assignments file means explicitly excluded — stop and return ''.
    Falls back to CATEGORY_MAPPINGS for nodes not yet in the assignments file.
    """
    assignments = _load_assignments()

    if assignments:
        depth_count = len(path)
        for i, node in enumerate(reversed(path)):
            depth_from_leaf = i
            canonical = _normalize_node(company_name, node, depth_from_leaf)
            if canonical in assignments:
                return assignments[canonical] or ''  # null → explicitly excluded

    # Fallback: CATEGORY_MAPPINGS (legacy per-company mappings)
    company_key = _COMPANY_KEY_MAP.get(company_name.lower(), '')
    mappings = CATEGORY_MAPPINGS.get(company_key, {})
    for node in reversed(path):
        mapped = mappings.get(node)
        if mapped is not None:
            return slugify(mapped)

    return ''


def classify_path(company_name: str, path: list) -> dict:
    """
    Returns a dict with path_type, canonical_key, and primary_category_slug
    for the given company and path.
    """
    path_type = _classify_path_type(path)

    # Build canonical_key using confirmed node equivalences (depth from leaf).
    # This makes canonical_key cross-company comparable once equivalences exist.
    if path:
        depth_count = len(path)
        canonical_parts = [
            _normalize_node(company_name, node, depth_count - 1 - i)
            for i, node in enumerate(path)
        ]
        canonical_key = '/'.join(canonical_parts)
    else:
        canonical_key = ''

    primary_category_slug = _find_primary_category_slug(company_name, path)

    return {
        'path_type': path_type,
        'canonical_key': canonical_key,
        'primary_category_slug': primary_category_slug,
    }
