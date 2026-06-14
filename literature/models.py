import uuid
from django.db import models
from papers.models import Paper

class LiteratureReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    papers = models.ManyToManyField(Paper, related_name='literature_reviews')
    introduction = models.TextField()
    existing_approaches = models.TextField()
    comparison_of_methods = models.TextField()
    limitations = models.TextField()
    research_opportunities = models.TextField()
    references = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
