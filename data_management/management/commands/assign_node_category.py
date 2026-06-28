import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from data_management.data.category_mappings import CATEGORY_MAPPINGS, PRIMARY_CATEGORY_HIERARCHY

CANDIDATES_PATH = 'data_management/data/node_assignment_candidates.jsonl'
DECISIONS_PATH = 'data_management/data/node_assignment_decisions.jsonl'


def _valid_primary_category_slugs():
    slugs = set()
    for store_mappings in CATEGORY_MAPPINGS.values():
        for v in store_mappings.values():
            if v is not None:
                slugs.add(slugify(v))
    for parent, children in PRIMARY_CATEGORY_HIERARCHY.items():
        slugs.add(slugify(parent))
        for child in children:
            slugs.add(slugify(child))
    return slugs


class Command(BaseCommand):
    help = (
        'Records a primary category assignment for a canonical node slug. '
        'Removes the entry from node_assignment_candidates.jsonl and appends it to '
        'node_assignment_decisions.jsonl. Run apply_node_category_assignments to rebuild '
        'canonical_category_assignments.json.\n\n'
        'Usage: python manage.py assign_node_category <canonical_slug> <primary_category_slug|none> [--note "..."]'
    )

    def add_arguments(self, parser):
        parser.add_argument('canonical_slug', type=str)
        parser.add_argument(
            'primary_category',
            type=str,
            help='Primary category slug (e.g. "yogurt", "milk") or "none" to explicitly exclude.',
        )
        parser.add_argument('--note', type=str, default=None)

    def handle(self, *args, **options):
        canonical_slug = options['canonical_slug']
        primary_category_raw = options['primary_category'].strip().lower()
        note = options['note']

        if primary_category_raw == 'none':
            primary_category = None
        else:
            valid = _valid_primary_category_slugs()
            if primary_category_raw not in valid:
                raise CommandError(
                    f"'{primary_category_raw}' is not a recognised primary category slug.\n"
                    f"Valid slugs: {', '.join(sorted(valid))}"
                )
            primary_category = primary_category_raw

        if not os.path.exists(CANDIDATES_PATH):
            raise CommandError(
                f'Candidates file not found at {CANDIDATES_PATH}. '
                'Run generate_node_candidates first.'
            )

        remaining = []
        target = None
        with open(CANDIDATES_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec['canonical_slug'] == canonical_slug:
                    target = rec
                else:
                    remaining.append(rec)

        if target is None:
            raise CommandError(
                f"No candidate found with canonical_slug '{canonical_slug}'. "
                f"It may have already been decided — check {DECISIONS_PATH}."
            )

        decision = {
            'canonical_slug': canonical_slug,
            'primary_category': primary_category,
            'note': note,
            'evidence_count': target.get('evidence_count', 0),
            'companies': target.get('companies', []),
        }

        with open(CANDIDATES_PATH, 'w', encoding='utf-8') as f:
            for rec in remaining:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')

        os.makedirs(os.path.dirname(DECISIONS_PATH), exist_ok=True)
        with open(DECISIONS_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(decision, ensure_ascii=False) + '\n')

        label = primary_category if primary_category else 'EXCLUDED'
        self.stdout.write(self.style.SUCCESS(
            f'[{label}] {canonical_slug} (evidence {target.get("evidence_count", 0)})'
        ))
        self.stdout.write(f'  {len(remaining)} candidates remaining.')
