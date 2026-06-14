import uuid
from django.db import models

class Paper(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, null=True, blank=True)
    authors = models.TextField(null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='papers/')
    
    # Process Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(null=True, blank=True)
    
    # Enhanced Metadata
    pdf_size = models.CharField(max_length=50, null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)
    processing_percentage = models.IntegerField(default=0)
    
    # Extraction & AI Outputs
    extracted_text = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    objectives = models.TextField(null=True, blank=True)  # JSON or comma-separated list
    methodology = models.TextField(null=True, blank=True)
    dataset_info = models.TextField(null=True, blank=True)
    results_conclusions = models.TextField(null=True, blank=True)
    keywords = models.CharField(max_length=255, null=True, blank=True)  # Comma-separated values

    def save(self, *args, **kwargs):
        if self.file and not self.pdf_size:
            try:
                size_bytes = self.file.size
                if size_bytes >= 1024 * 1024:
                    self.pdf_size = f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    self.pdf_size = f"{size_bytes / 1024:.1f} KB"
            except Exception as e:
                print(f"Error getting file size on save: {e}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Paper ({self.id})"

class PaperChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    text_content = models.TextField()

    def __str__(self):
        return f"{self.paper.title or self.paper.id} - Chunk {self.chunk_index}"
