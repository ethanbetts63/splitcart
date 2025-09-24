from django.core.management.base import BaseCommand
from companies.models import Company, Category

class Command(BaseCommand):
    help = 'Finds and reports cycles in category parent-child relationships for a specific company.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-name',
            type=str,
            required=True,
            help='The name of the company to diagnose (e.g., "woolworths").'
        )

    def handle(self, *args, **options):
        company_name = options['company_name']
        self.stdout.write(f"Starting cycle detection for company: {company_name}")

        try:
            company = Company.objects.get(name__iexact=company_name)
        except Company.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Company '{company_name}' not found."))
            return

        all_company_categories = Category.objects.filter(company=company)
        
        # Keep track of nodes visited in the overall graph to avoid re-checking branches
        # path_nodes: nodes in the current traversal path (for cycle detection)
        # visited_nodes: all nodes visited so far in the entire process (for efficiency)
        path_nodes = set()
        visited_nodes = set()
        cycles_found = 0

        for category in all_company_categories:
            if category.id not in visited_nodes:
                cycle = self._find_cycle_recursive(category, path_nodes, visited_nodes)
                if cycle:
                    cycles_found += 1
                    self.stdout.write(self.style.ERROR("\n--- Cycle Detected! ---"))
                    self.stdout.write("The following categories form a loop:")
                    # Format the cycle path for readability
                    path_str = " -> ".join([f'{c.name} (ID: {c.id})' for c in cycle])
                    self.stdout.write(path_str)

        if cycles_found == 0:
            self.stdout.write(self.style.SUCCESS("No cycles found for this company."))
        else:
            self.stdout.write(self.style.WARNING(f"\nFound {cycles_found} distinct cycle(s)."))

    def _find_cycle_recursive(self, current_node, path_nodes, visited_nodes):
        # Add current node to the path for this traversal
        path_nodes.add(current_node.id)
        visited_nodes.add(current_node.id)

        for parent in current_node.parents.all():
            if parent.id in path_nodes:
                # Cycle detected! We found a node that is already in our current path.
                # We need to return the path that shows the cycle.
                # This is a simplified representation; full path reconstruction is more complex.
                # For diagnosis, just knowing the participants is often enough.
                # A simple approach is to just return the participants we know about.
                # A more complex implementation would pass the path list down.
                return [current_node, parent]
            
            if parent.id not in visited_nodes:
                result = self._find_cycle_recursive(parent, path_nodes, visited_nodes)
                if result:
                    # If a cycle is found in a deeper call, append current node and pass it up.
                    if current_node not in result:
                         result.append(current_node)
                    return result

        # No cycle found from this node, remove it from the current path before backtracking
        path_nodes.remove(current_node.id)
        return None
