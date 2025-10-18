from django.db import models

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    page = models.CharField(max_length=50, help_text="Identifier for the page this FAQ belongs to (e.g., 'home', 'about').")

    def __str__(self):
        return self.question

    class Meta:
        verbose_name_plural = "FAQs"
        unique_together = ('question', 'page')
