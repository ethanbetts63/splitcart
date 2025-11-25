from .internal_group_health_checker import InternalGroupHealthChecker
from .intergroup_comparer import IntergroupComparer

class GroupMaintenanceOrchestrator:
    """
    Orchestrates the overall group maintenance process, calling the health checker and intergroup comparer.
    """
    def __init__(self, command, relaxed_staleness=False):
        self.command = command
        self.relaxed_staleness = relaxed_staleness

    def run(self):
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting Group Maintenance Orchestration ---"))
        
        # Phase 1: Internal Group Maintenance (Health Checks)
        health_checker = InternalGroupHealthChecker(self.command, relaxed_staleness=self.relaxed_staleness)
        health_checker.run()

        # Phase 2: Inter-Group Merging
        merger = IntergroupComparer(self.command, relaxed_staleness=self.relaxed_staleness)
        merger.run()

        self.command.stdout.write(self.command.style.SUCCESS("--- Group Maintenance Orchestration Complete ---"))
