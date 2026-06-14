import uuid
from django.db import models
from ideas.models import ProjectIdea

class ExperimentalPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_idea = models.ForeignKey(ProjectIdea, on_delete=models.CASCADE, related_name='experimental_plans', null=True, blank=True)
    title = models.CharField(max_length=255)
    datasets = models.TextField()  # Comma separated or JSON formatted text
    ai_models = models.TextField()  # Comma separated or JSON formatted text
    training_approach = models.TextField()
    evaluation_metrics = models.TextField()
    expected_challenges = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
