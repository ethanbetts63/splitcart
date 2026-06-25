import json
import os
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.utils.text import slugify

DECISIONS_PATH = 'data_management/data/category_decisions.jsonl'
SUSPECTS_PATH = 'data_management/data/category_suspects.jsonl'
EQUIVALENCES_PATH = 'data_management/data/category_node_equivalences.json'


def _canonical_name(node_a, node_b):
    a, b = node_a.strip(), node_b.strip()
    return slugify(a) if len(a) <= len(b) else slugify(b)


class Command(BaseCommand):
    help = (
        'Reads confirmed matches from category_decisions.jsonl and writes '
        'category_node_equivalences.json for PathClassifier to use when '
        'normalizing node names into canonical_key.'
    )

    def handle(self, *args, **options):
        if not os.path.exists(DECISIONS_PATH):
            self.stderr.write(f'Decisions file not found at {DECISIONS_PATH}. Run classify_suspect first.')
            return

        matches = []
        counts = defaultdict(int)
        with open(DECISIONS_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                counts[rec.get('decision')] += 1
                if rec.get('decision') == 'match':
                    matches.append(rec)

        # Also count undecided suspects still in the queue
        undecided = 0
        if os.path.exists(SUSPECTS_PATH):
            with open(SUSPECTS_PATH, 'r', encoding='utf-8') as f:
                undecided = sum(1 for line in f if line.strip())

        total_decided = sum(counts.values())
        self.stdout.write(
            f'{total_decided} decided — {counts["match"]} match, '
            f'{counts["not_match"]} not_match, {counts["unsure"]} unsure. '
            f'{undecided} still undecided in suspects file.'
        )

        if undecided > 0:
            self.stdout.write(self.style.WARNING(
                f'  {undecided} suspects still undecided — run classify_suspect to clear them.'
            ))

        # Build equivalences: company → node_name → depth → canonical_slug
        equivalences: dict = defaultdict(lambda: defaultdict(dict))
        for rec in matches:
            canon = _canonical_name(rec['node_a'], rec['node_b'])
            depth = str(rec['depth_from_leaf'])
            equivalences[rec['company_a']][rec['node_a']][depth] = canon
            equivalences[rec['company_b']][rec['node_b']][depth] = canon

        output = {
            company: dict(nodes)
            for company, nodes in equivalences.items()
        }

        with open(EQUIVALENCES_PATH, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        total_mappings = sum(
            len(depths) for nodes in output.values() for depths in nodes.values()
        )
        self.stdout.write(self.style.SUCCESS(
            f'Wrote {total_mappings} node→canonical mappings across '
            f'{len(output)} companies to {EQUIVALENCES_PATH}.'
        ))
