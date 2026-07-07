import json
import os

from django.core.management.base import BaseCommand, CommandError

SUSPECTS_PATH = 'pipeline/data/category_suspects.jsonl'
DECISIONS_PATH = 'pipeline/data/category_decisions.jsonl'
VALID_DECISIONS = {'match', 'not_match', 'unsure'}


class Command(BaseCommand):
    help = (
        'Records a classification decision for a category suspect entry. '
        'Removes the entry from category_suspects.jsonl and appends it to '
        'category_decisions.jsonl. The agent will not see this entry again.\n\n'
        'Usage: python manage.py classify_suspect <id> <match|not_match|unsure> [--note "..."]'
    )

    def add_arguments(self, parser):
        parser.add_argument('suspect_id', type=str)
        parser.add_argument('decision', type=str, choices=list(VALID_DECISIONS))
        parser.add_argument('--note', type=str, default=None)

    def handle(self, *args, **options):
        suspect_id = options['suspect_id']
        decision = options['decision']
        note = options['note']

        if not os.path.exists(SUSPECTS_PATH):
            raise CommandError(
                f'Suspects file not found at {SUSPECTS_PATH}. Run generate_category_suspects first.'
            )

        # Read suspects file, pull out the target entry
        remaining = []
        target = None
        with open(SUSPECTS_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec['id'] == suspect_id:
                    target = rec
                else:
                    remaining.append(rec)

        if target is None:
            raise CommandError(
                f"No undecided suspect found with id '{suspect_id}'. "
                f"It may have already been decided — check {DECISIONS_PATH}."
            )

        # Apply decision
        target['decision'] = decision
        target['note'] = note

        # Write remaining suspects back (entry removed)
        with open(SUSPECTS_PATH, 'w', encoding='utf-8') as f:
            for rec in remaining:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')

        # Append decided entry to decisions archive
        os.makedirs(os.path.dirname(DECISIONS_PATH), exist_ok=True)
        with open(DECISIONS_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(target, ensure_ascii=False) + '\n')

        self.stdout.write(self.style.SUCCESS(
            f"[{decision.upper()}] {target['company_a']}:{target['node_a']} "
            f"↔ {target['company_b']}:{target['node_b']} "
            f"(depth {target['depth_from_leaf']}, evidence {target['evidence_count']})"
        ))
        self.stdout.write(f"  {len(remaining)} suspects remaining.")
