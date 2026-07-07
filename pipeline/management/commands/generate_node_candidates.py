import json
import os
from collections import defaultdict

from django.core.management.base import BaseCommand
from products.models import Product
from pipeline.utils.path_classifier import _normalize_node

CANDIDATES_PATH = 'pipeline/data/node_assignment_candidates.jsonl'
DECISIONS_PATH = 'pipeline/data/node_assignment_decisions.jsonl'


def _load_decided_slugs(path):
    slugs = set()
    if not os.path.exists(path):
        return slugs
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                slugs.add(rec['canonical_slug'])
            except (json.JSONDecodeError, KeyError):
                pass
    return slugs


class Command(BaseCommand):
    help = (
        'Generates node_assignment_candidates.jsonl from product category_paths. '
        'Each entry is a unique canonical node slug that needs a primary_category assignment. '
        'Already-decided slugs (in node_assignment_decisions.jsonl) are skipped. '
        'Sorted by evidence_count descending.'
    )

    def handle(self, *args, **options):
        self.stdout.write('Loading product category paths...')
        products = list(
            Product.objects.exclude(category_paths=[]).only('id', 'category_paths')
        )
        self.stdout.write(f'  {len(products)} products with category_paths.')

        decided_slugs = _load_decided_slugs(DECISIONS_PATH)
        self.stdout.write(f'  {len(decided_slugs)} canonical slugs already decided (skipping).')

        # canonical_slug → aggregated data
        nodes = defaultdict(lambda: {
            'evidence_count': 0,
            'raw_names': {},   # (company, name) → True, used as ordered set
            'companies': set(),
            'path_types': set(),
            'sample_paths': [],
        })

        for product in products:
            for entry in product.category_paths:
                company = entry.get('company', '')
                path = entry.get('path', [])
                path_type = entry.get('path_type', 'unknown')
                evidence = entry.get('evidence_count', 1)

                if not company or not path:
                    continue

                depth_count = len(path)
                for i, node_name in enumerate(path):
                    depth_from_leaf = depth_count - 1 - i
                    canonical = _normalize_node(company, node_name, depth_from_leaf)

                    rec = nodes[canonical]
                    rec['evidence_count'] += evidence
                    rec['raw_names'][(company, node_name)] = True
                    rec['companies'].add(company)
                    rec['path_types'].add(path_type)
                    if len(rec['sample_paths']) < 3:
                        path_str = ' > '.join(path) + f' ({company})'
                        if path_str not in rec['sample_paths']:
                            rec['sample_paths'].append(path_str)

        # Filter out already-decided slugs and serialize sets
        candidates = []
        for canonical_slug, data in nodes.items():
            if canonical_slug in decided_slugs:
                continue
            candidates.append({
                'canonical_slug': canonical_slug,
                'evidence_count': data['evidence_count'],
                'companies': sorted(data['companies']),
                'raw_names': [
                    {'company': c, 'name': n}
                    for (c, n) in data['raw_names']
                ],
                'path_types': sorted(data['path_types']),
                'sample_paths': data['sample_paths'],
            })

        candidates.sort(key=lambda r: -r['evidence_count'])

        os.makedirs(os.path.dirname(CANDIDATES_PATH), exist_ok=True)
        with open(CANDIDATES_PATH, 'w', encoding='utf-8') as f:
            for rec in candidates:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')

        self.stdout.write(self.style.SUCCESS(
            f'Wrote {len(candidates)} undecided node candidates to {CANDIDATES_PATH}.'
        ))
