from rest_framework import serializers
from papers.models import Paper, PaperChunk
from gaps.models import ResearchGap
from ideas.models import ProjectIdea
from literature.models import LiteratureReview
from experiments.models import ExperimentalPlan

class PaperChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperChunk
        fields = ['id', 'chunk_index', 'text_content']

class PaperSerializer(serializers.ModelSerializer):
    chunks = PaperChunkSerializer(many=True, read_only=True)
    
    class Meta:
        model = Paper
        fields = [
            'id', 'title', 'authors', 'upload_date', 'file', 'status', 
            'error_message', 'extracted_text', 'summary', 'objectives', 
            'methodology', 'dataset_info', 'results_conclusions', 'keywords', 
            'pdf_size', 'page_count', 'processing_time', 'processing_percentage', 'chunks'
        ]

class ResearchGapSerializer(serializers.ModelSerializer):
    supporting_papers = serializers.PrimaryKeyRelatedField(many=True, queryset=Paper.objects.all())
    supporting_papers_details = PaperSerializer(many=True, source='supporting_papers', read_only=True)

    class Meta:
        model = ResearchGap
        fields = [
            'id', 'title', 'description', 'confidence_score', 
            'novelty_score', 'impact_score', 'difficulty_score', 
            'supporting_papers', 'supporting_papers_details', 'created_at'
        ]

class ProjectIdeaSerializer(serializers.ModelSerializer):
    research_gap_details = ResearchGapSerializer(source='research_gap', read_only=True)

    class Meta:
        model = ProjectIdea
        fields = [
            'id', 'research_gap', 'research_gap_details', 'title', 
            'problem_statement', 'proposed_methodology', 'expected_outcome', 
            'difficulty_level', 'innovation_score', 
            'novelty_score', 'impact_score', 'difficulty_score', 'estimated_timeline', 'created_at'
        ]

class LiteratureReviewSerializer(serializers.ModelSerializer):
    papers = serializers.PrimaryKeyRelatedField(many=True, queryset=Paper.objects.all())
    papers_details = PaperSerializer(many=True, source='papers', read_only=True)

    class Meta:
        model = LiteratureReview
        fields = [
            'id', 'title', 'papers', 'papers_details', 'introduction', 
            'existing_approaches', 'comparison_of_methods', 'limitations', 
            'research_opportunities', 'references', 'created_at'
        ]

class ExperimentalPlanSerializer(serializers.ModelSerializer):
    project_idea_details = ProjectIdeaSerializer(source='project_idea', read_only=True)

    class Meta:
        model = ExperimentalPlan
        fields = [
            'id', 'project_idea', 'project_idea_details', 'title', 
            'datasets', 'ai_models', 'training_approach', 
            'evaluation_metrics', 'expected_challenges', 'created_at'
        ]
