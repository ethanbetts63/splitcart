class TallyCounter:
    """A simple class to manage and display a running tally of created and updated items."""
    def __init__(self):
        self.created = 0
        self.updated = 0

    def increment(self, created: bool):
        """Increments the created or updated counter."""
        if created:
            self.created += 1
        else:
            self.updated += 1

    def display(self, command_instance):
        """Displays the current tally using the provided command's stdout."""
        tally_msg = f"--- Tally: {self.created} Created, {self.updated} Updated ---"
        command_instance.stdout.write(tally_msg)
