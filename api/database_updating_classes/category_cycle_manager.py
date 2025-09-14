import os
import msvcrt
from companies.models import Category

class CategoryCycleManager:
    """A class to detect and repair cycles in category hierarchies."""

    def __init__(self, command, company):
        self.command = command
        self.company = company
        self.cycles_found_and_repaired = 0

    def repair_cycles_interactive(self):
        self.command.stdout.write(self.style.SUCCESS(f"Starting interactive cycle repair for {self.company.name}..."))
        # Loop to find and fix one cycle at a time until none are left
        while self._find_and_repair_one_cycle():
            self.cycles_found_and_repaired += 1
            self.command.stdout.write(self.style.SUCCESS("--- Cycle repaired. Searching for next cycle... ---"))
            # Pause for user to read
            msvcrt.getch()

        if self.cycles_found_and_repaired > 0:
            self.command.stdout.write(self.style.SUCCESS(f"\nFinished. Repaired {self.cycles_found_and_repaired} cycle(s)."))
        else:
            self.command.stdout.write(self.style.SUCCESS("\nNo cycles found for this company."))

    def _find_and_repair_one_cycle(self):
        all_company_categories = Category.objects.filter(company=self.company).prefetch_related('parents')
        for category in all_company_categories:
            # For each category, trace its parents to detect a loop
            path = []
            curr = category
            while curr and curr.id not in path:
                path.append(curr.id)
                # This assumes a category has at most one parent path for simplicity of diagnosis
                # A more complex scenario involves multiple parents
                parent = curr.parents.first()
                if parent and parent.id in path:
                    # Cycle detected!
                    cycle_start_index = path.index(parent.id)
                    cycle_path_ids = path[cycle_start_index:] + [curr.id]
                    cycle_nodes = Category.objects.filter(id__in=cycle_path_ids).in_bulk()
                    # Ensure order is preserved
                    ordered_cycle_nodes = [cycle_nodes[id] for id in cycle_path_ids]
                    self._present_and_repair_cycle(ordered_cycle_nodes)
                    return True # Signal that a cycle was found and repaired
                curr = parent
        return False # No cycles found in this pass

    def _present_and_repair_cycle(self, cycle_nodes):
        self.command.stdout.write(self.style.ERROR("\n--- Cycle Detected! ---"))
        # cycle_nodes is e.g. [A, B, C, A] where A->B, B->C, C->A
        for i in range(len(cycle_nodes) - 1):
            child = cycle_nodes[i]
            parent = cycle_nodes[i+1]

            os.system('cls' if os.name == 'nt' else 'clear')
            self.command.stdout.write(self.style.WARNING("The following categories form a loop. Please identify the incorrect link."))
            path_str = " -> ".join([f'{c.name}' for c in cycle_nodes])
            self.command.stdout.write(f"Cycle: {path_str}")
            self.command.stdout.write("-" * 50)
            self.command.stdout.write(f"Is this relationship correct?\n  CHILD:  {self.style.SQL_FIELD(child.name)}\n  PARENT: {self.style.SQL_FIELD(parent.name)}")
            
            while True:
                self.command.stdout.write(self.style.HTTP_REDIRECT("\nCorrect parent? [y/n/s(kip link)]: "), ending="")
                self.command.flush()
                choice = msvcrt.getch().decode('utf-8').lower()
                self.command.stdout.write(choice + '\n')
                if choice in ['y', 'n', 's']:
                    break
                self.command.stdout.write(self.style.ERROR("Invalid input."))

            if choice == 'n':
                self.command.stdout.write(self.style.WARNING(f"Removing parent '{parent.name}' from '{child.name}'..."))
                child.parents.remove(parent)
                self.command.stdout.write(self.style.SUCCESS("Link removed. The cycle is broken."))
                # Once broken, we return and the outer loop will re-scan
                return
            elif choice == 's':
                continue # Move to the next link in the cycle