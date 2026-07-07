from django.db import models

class BargainStats(models.Model):
    """
    A model to store pre-calculated bargain statistics as JSON data.
    This is used for data that is expensive to compute and can be updated
    periodically, such as bargain comparisons between companies.
    """
    key = models.CharField(
        max_length=100, 
        primary_key=True,
        help_text="The unique key for the statistic (e.g., 'bargain_stats')."
    )
    data = models.JSONField(
        default=dict,
        help_text="The pre-calculated statistical data."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The timestamp when the statistic was last updated."
    )

    def __str__(self):
        return f"Bargain Stats: {self.key}"

    class Meta:
        verbose_name_plural = "Bargain Stats"
