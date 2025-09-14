from companies.models import Category

class CategoryCycleManager:
    """A class to detect and automatically prune cycles in category hierarchies."""

    def __init__(self, command, company):
        self.command = command
        self.company = company
        self.cycles_repaired = 0

    def prune_cycles(self):
        self.command.stdout.write(self.command.style.SUCCESS(f"Starting automatic cycle pruning for {self.company.name}..."))
        # We need to re-query the categories in each pass, as links are being deleted.
        while self._find_and_prune_a_cycle():
            self.cycles_repaired += 1
        
        if self.cycles_repaired > 0:
            self.command.stdout.write(self.command.style.SUCCESS(f"  - Finished for {self.company.name}. Pruned {self.cycles_repaired} cycle(s)."))
        else:
            self.command.stdout.write(self.command.style.SUCCESS(f"  - No cycles found for {self.company.name}."))

    def _find_and_prune_a_cycle(self):
        """Finds the first cycle and prunes it by re-implementing the working recursive logic."""
        all_company_categories = Category.objects.filter(company=self.company)
        # visited_nodes tracks nodes checked in this entire pass to avoid re-validating clean branches
        visited_nodes = set()
        for category in all_company_categories:
            if category.id not in visited_nodes:
                # path_nodes tracks the current recursion stack for one traversal
                if self._prune_cycle_recursive(category, path_nodes=set(), visited_nodes=visited_nodes):
                    return True # A cycle was found and pruned
        return False # No cycles found in this pass

    def _prune_cycle_recursive(self, current_node, path_nodes, visited_nodes):
        path_nodes.add(current_node)
        visited_nodes.add(current_node)

        for parent in current_node.parents.all():
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
                return True # Signal that a cycle was pruned
            
            if parent.id not in visited_nodes:
                if self._prune_cycle_recursive(parent, path_nodes, visited_nodes):
                    return True # Pass the signal up

        path_nodes.remove(current_node)
        return False # No cycle found in this branch
