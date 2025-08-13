from django.db import models

class Division(models.Model):
    """
    Represents a specific division or banner under a parent company.
    e.g., 'Woolworths Metro' is a division under 'Woolworths'.
    """
    # Auto-generated primary key (standard Django practice)
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')

    # External ID from source data (nullable)
    external_id = models.CharField(
        max_length=100,
        unique=True, # Unique if present (globally, or within company if unique_together is added)
        null=True,
        blank=True,
        help_text="The unique identifier for the division from the company's system (e.g., Coles brand ID)."
    )
    
    # Name must not be null, unique within company
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="The human-readable name of the division (e.g., 'Coles Supermarkets', 'SUPERMARKETS')."
    )
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='divisions',
        help_text="The parent company that owns this division."
    )
    
    store_finder_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="A specific ID for the division used in store finder systems."
    )

    class Meta:
        # Name is unique within a company
        unique_together = ('name', 'company') 

        verbose_name = "Division"
        verbose_name_plural = "Divisions"

    def __str__(self):
        return f"{self.name} ({self.company.name})"