import uuid
from django.db import models
from papers.models import Paper

class ResearchGap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    confidence_score = models.FloatField(default=0.0)
    novelty_score = models.IntegerField(default=0)
    impact_score = models.IntegerField(default=0)
    difficulty_score = models.IntegerField(default=0)
    supporting_papers = models.ManyToManyField(Paper, related_name='detected_gaps')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
