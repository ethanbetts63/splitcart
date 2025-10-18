from django.db import models

class FAQ(models.Model):
    question = models.CharField(max_length=255, unique=True)
    answer = models.TextField()
    pages = models.JSONField(default=list, help_text="A list of page identifiers where this FAQ should appear (e.g., [\"home\", \"substitutes\"])")

    def __str__(self):
        return self.question

    class Meta:
        verbose_name_plural = "FAQs"
