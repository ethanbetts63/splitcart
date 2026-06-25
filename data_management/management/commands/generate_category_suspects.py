import hashlib
import json
import os
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations

from django.core.management.base import BaseCommand
from products.models import Product

SUSPECTS_PATH = 'data_management/data/category_suspects.jsonl'
DECISIONS_PATH = 'data_management/data/category_decisions.jsonl'


def _make_id(company_a, node_a, company_b, node_b, depth_from_leaf):
    raw = f"{company_a}|{node_a}|{company_b}|{node_b}|{depth_from_leaf}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _name_similarity(a, b):
    return round(SequenceMatcher(None, a.lower(), b.lower()).ratio(), 3)


def _align_from_leaf(path_a, path_b):
    """
    Yield (node_a, node_b, depth_from_leaf) pairs aligned from the leaf end.
    Stops at the shorter path. Unmatched nodes in the longer path are skipped.
    """
    for i, (na, nb) in enumerate(zip(reversed(path_a), reversed(path_b))):
        yield na, nb, i


def _load_ids_from_jsonl(path):
    ids = set()
    if not os.path.exists(path):
        return ids
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ids.add(rec['id'])
            except (json.JSONDecodeError, KeyError):
                pass
    return ids


class Command(BaseCommand):
    help = (
        'Generates category_suspects.jsonl from product category_paths. '
        'Pairs aligned from the leaf; sorted by evidence descending. '
        'Already-decided entries (in category_decisions.jsonl) are never re-added. '
        'Existing undecided entries in the suspects file are preserved and updated with fresh evidence counts.'
    )

    def handle(self, *args, **options):
        self.stdout.write('Loading product category paths...')
        products = list(
            Product.objects.exclude(category_paths=[]).only('id', 'category_paths')
        )
        self.stdout.write(f'  {len(products)} products with category_paths.')

        # --- Build full evidence map from DB ---
        evidence = defaultdict(lambda: {'evidence_count': 0, 'example_product_ids': []})

        for product in products:
            paths_by_company = defaultdict(list)
            for entry in product.category_paths:
                company = entry.get('company', '')
                path = entry.get('path', [])
                if company and len(path) >= 1:
                    paths_by_company[company].append(path)

            if len(paths_by_company) < 2:
                continue

            for (company_a, paths_a), (company_b, paths_b) in combinations(paths_by_company.items(), 2):
                for path_a in paths_a:
                    for path_b in paths_b:
                        for node_a, node_b, depth in _align_from_leaf(path_a, path_b):
                            pair_id = _make_id(company_a, node_a, company_b, node_b, depth)
                            rec = evidence[pair_id]
                            rec['evidence_count'] += 1
                            if len(rec['example_product_ids']) < 5:
                                if product.id not in rec['example_product_ids']:
                                    rec['example_product_ids'].append(product.id)
                            if 'company_a' not in rec:
                                rec.update({
                                    'id': pair_id,
                                    'company_a': company_a,
                                    'node_a': node_a,
                                    'company_b': company_b,
                                    'node_b': node_b,
                                    'depth_from_leaf': depth,
                                    'name_similarity': _name_similarity(node_a, node_b),
                                })

        self.stdout.write(f'  {len(evidence)} unique node pairs found in DB.')

        # --- Load already-decided IDs — never re-add these ---
        decided_ids = _load_ids_from_jsonl(DECISIONS_PATH)
        self.stdout.write(f'  {len(decided_ids)} pairs already decided (skipping).')

        # --- Load existing undecided suspects — preserve them ---
        existing_undecided = {}
        if os.path.exists(SUSPECTS_PATH):
            with open(SUSPECTS_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        existing_undecided[rec['id']] = rec
                    except (json.JSONDecodeError, KeyError):
                        pass

        # --- Merge: update evidence counts on existing, add genuinely new pairs ---
        final = {}
        new_count = 0
        for pair_id, rec in evidence.items():
            if pair_id in decided_ids:
                continue
            if pair_id in existing_undecided:
                # Update evidence count in case more products have been scraped
                existing_undecided[pair_id]['evidence_count'] = rec['evidence_count']
                existing_undecided[pair_id]['example_product_ids'] = rec['example_product_ids']
                final[pair_id] = existing_undecided[pair_id]
            else:
                final[pair_id] = rec
                new_count += 1

        # Sort: evidence desc, then name_similarity desc (exact matches surface first)
        sorted_pairs = sorted(
            final.values(),
            key=lambda r: (-r['evidence_count'], -r['name_similarity']),
        )

        os.makedirs(os.path.dirname(SUSPECTS_PATH), exist_ok=True)
        with open(SUSPECTS_PATH, 'w', encoding='utf-8') as f:
            for rec in sorted_pairs:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')

        self.stdout.write(self.style.SUCCESS(
            f'Wrote {len(sorted_pairs)} undecided suspects to {SUSPECTS_PATH} '
            f'({new_count} new this run, {len(sorted_pairs) - new_count} carried over).'
        ))
