class TallyCounter:
    """A simple class to manage and display a running tally of created and updated items."""
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.created_per_company = {}

    def increment(self, created: bool, company_name: str = None):
        """Increments the created or updated counter."""
        if created:
            self.created += 1
            if company_name:
                self.created_per_company[company_name] = self.created_per_company.get(company_name, 0) + 1
        else:
            self.updated += 1

    def display(self, command_instance):
        """Displays the current tally using the provided command's stdout."""
        company_breakdown = []
        for company, count in self.created_per_company.items():
            company_breakdown.append(f"{company}: {count}")
        
        company_breakdown_str = ""
        if company_breakdown:
            company_breakdown_str = " (" + ", ".join(company_breakdown) + ")"

        tally_msg = f"--- Tally: {self.created} Created{company_breakdown_str}, {self.updated} Updated ---"
        command_instance.stdout.write(tally_msg)