from companies.models import Category

class CategoryCycleManager:
    """A class to detect and automatically prune cycles in category hierarchies."""

    def __init__(self, command, company):
        self.command = command
        self.company = company
        self.cycles_repaired = 0

    def prune_cycles(self):
        self.command.stdout.write(self.command.style.SUCCESS(f"Starting automatic cycle pruning for {self.company.name}..."))
        
        # Load all categories for the company into memory once, prefetching parents
        all_company_categories_cache = list(Category.objects.filter(company=self.company).prefetch_related('parents'))
        
        visited_nodes = set()
        for category in all_company_categories_cache:
            if category.id not in visited_nodes:
                # path_nodes tracks the current recursion stack for one traversal
                self._prune_cycles_recursive(category, path_nodes=set(), visited_nodes=visited_nodes)
        
        if self.cycles_repaired > 0:
            self.command.stdout.write(self.command.style.SUCCESS(f"  - Finished for {self.company.name}. Pruned {self.cycles_repaired} cycle(s)."))
        else:
            self.command.stdout.write(self.command.style.SUCCESS(f"  - No cycles found for {self.company.name}."))

    def _prune_cycles_recursive(self, current_node, path_nodes, visited_nodes):
        path_nodes.add(current_node)
        visited_nodes.add(current_node.id) # Use ID for consistency in the set

        # Iterate over a copy of the parents list to allow safe removal during the loop
        for parent in list(current_node.parents.all()):
            if parent in path_nodes:
                # CYCLE DETECTED!
                self.command.stdout.write(self.command.style.ERROR("\n--- Cycle Detected! ---"))
                self.command.stdout.write(
                    f"  - Path: ... -> '{current_node.name}' -> '{parent.name}' (which is already in the path)"
                )
                self.command.stdout.write(
                    self.command.style.WARNING(f"  - Pruning Link: Removing parent '{parent.name}' from child '{current_node.name}'.")
                )
                current_node.parents.remove(parent)
                self.cycles_repaired += 1
                # Do not return; continue checking other parents for more complex cycles
            
            if parent.id not in visited_nodes:
                self._prune_cycles_recursive(parent, path_nodes, visited_nodes)

        path_nodes.remove(current_node)
