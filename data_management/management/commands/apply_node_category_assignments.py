import json
import os

from django.core.management.base import BaseCommand

DECISIONS_PATH = 'data_management/data/node_assignment_decisions.jsonl'
CANDIDATES_PATH = 'data_management/data/node_assignment_candidates.jsonl'
ASSIGNMENTS_PATH = 'data_management/data/canonical_category_assignments.json'


class Command(BaseCommand):
    help = (
        'Reads node_assignment_decisions.jsonl and writes canonical_category_assignments.json. '
        'PathClassifier loads this file automatically on the next update run. '
        'Re-run generate --primary-cats after this to propagate changes to products.'
    )

    def handle(self, *args, **options):
        if not os.path.exists(DECISIONS_PATH):
            self.stderr.write(
                f'Decisions file not found at {DECISIONS_PATH}. '
                'Run assign_node_category first.'
            )
            return

        assignments = {}
        excluded_count = 0
        assigned_count = 0

        with open(DECISIONS_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    slug = rec['canonical_slug']
                    primary = rec.get('primary_category')
                    assignments[slug] = primary
                    if primary is None:
                        excluded_count += 1
                    else:
                        assigned_count += 1
                except (json.JSONDecodeError, KeyError) as e:
                    self.stderr.write(f'Skipping malformed line: {e}')

        undecided = 0
        if os.path.exists(CANDIDATES_PATH):
            with open(CANDIDATES_PATH, 'r', encoding='utf-8') as f:
                undecided = sum(1 for line in f if line.strip())

        self.stdout.write(
            f'{len(assignments)} decisions — {assigned_count} assigned, '
            f'{excluded_count} excluded. '
            f'{undecided} candidates still unclassified.'
        )
        if undecided > 0:
            self.stdout.write(self.style.WARNING(
                f'  {undecided} candidates still pending — run assign_node_category to clear them.'
            ))

        with open(ASSIGNMENTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(assignments, f, indent=2, ensure_ascii=False, sort_keys=True)

        self.stdout.write(self.style.SUCCESS(
            f'Wrote {len(assignments)} canonical slug → primary category mappings to {ASSIGNMENTS_PATH}.'
        ))
        self.stdout.write(
            'Next step: run  python manage.py generate --primary-cats  to propagate to products.'
        )
