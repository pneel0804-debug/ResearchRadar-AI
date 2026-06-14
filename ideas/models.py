import uuid
from django.db import models
from gaps.models import ResearchGap

class ProjectIdea(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
        ('ADVANCED', 'Advanced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    research_gap = models.ForeignKey(ResearchGap, on_delete=models.CASCADE, related_name='project_ideas', null=True, blank=True)
    title = models.CharField(max_length=255)
    problem_statement = models.TextField()
    proposed_methodology = models.TextField()
    expected_outcome = models.TextField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    innovation_score = models.FloatField(default=5.0)  # scale of 1-10
    novelty_score = models.IntegerField(default=0)
    impact_score = models.IntegerField(default=0)
    difficulty_score = models.IntegerField(default=0)
    estimated_timeline = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
