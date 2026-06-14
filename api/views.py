import os
import time
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from papers.models import Paper, PaperChunk
from gaps.models import ResearchGap
from ideas.models import ProjectIdea
from literature.models import LiteratureReview
from experiments.models import ExperimentalPlan

from api.serializers import (
    PaperSerializer, PaperChunkSerializer, ResearchGapSerializer, 
    ProjectIdeaSerializer, LiteratureReviewSerializer, ExperimentalPlanSerializer
)

from ai_agents.agents import (
    PaperReadingAgent, SummaryAgent, GapDetectionAgent, 
    ProjectIdeaAgent, LiteratureReviewAgent, ExperimentPlanningAgent
)
from services.chroma_service import ChromaService

class PaperViewSet(viewsets.ModelViewSet):
    queryset = Paper.objects.all().order_by('-upload_date')
    serializer_class = PaperSerializer

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Runs PaperReadingAgent to extract and chunk, then runs SummaryAgent 
        to analyze objectives, methodology, keywords, etc.
        """
        paper = self.get_object()
        start_time = time.time()
        
        # 1. Read & chunk
        reader = PaperReadingAgent()
        success, msg = reader.process_paper(paper.id)
        if not success:
            return Response({"error": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # 2. Summarize & analyze
        summarizer = SummaryAgent()
        success, msg = summarizer.analyze_paper(paper.id)
        if not success:
            return Response({"error": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # Calculate and store processing time
        duration = round(time.time() - start_time, 1)
        paper.refresh_from_db()
        paper.processing_time = duration
        paper.processing_percentage = 100
        paper.status = 'COMPLETED'
        paper.save()
        
        # Return updated paper
        serializer = self.get_serializer(paper)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def semantic_search(self, request):
        """
        Search for paper chunks similar to a query using ChromaDB,
        and attach paper details.
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Query parameter 'q' is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        chroma = ChromaService()
        similar_chunks = chroma.search_similar_chunks(query, top_k=5)
        
        results = []
        for chunk in similar_chunks:
            paper_id = chunk['metadata'].get('paper_id')
            try:
                paper = Paper.objects.get(id=paper_id)
                paper_serializer = PaperSerializer(paper)
                results.append({
                    "chunk_id": chunk['id'],
                    "text_content": chunk['content'],
                    "distance": chunk['distance'],
                    "chunk_index": chunk['metadata'].get('chunk_index'),
                    "paper": paper_serializer.data
                })
            except Paper.DoesNotExist:
                continue
                
        return Response(results)

    def destroy(self, request, *args, **kwargs):
        """
        Deletes the paper database record, clears associated chunks in ChromaDB,
        and deletes the physical PDF/PowerPoint file on the disk.
        """
        instance = self.get_object()
        paper_id = instance.id
        file_path = instance.file.path if instance.file else None
        
        # 1. Clean vectors out of ChromaDB
        try:
            chroma = ChromaService()
            chroma.delete_paper_chunks(paper_id)
        except Exception as e:
            print(f"ChromaDB chunk deletion failed: {e}")
            
        # 2. Clean physical document file on disk
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"File system removal failed: {e}")
                
        return super().destroy(request, *args, **kwargs)


class ResearchGapViewSet(viewsets.ModelViewSet):
    queryset = ResearchGap.objects.all().order_by('-created_at')
    serializer_class = ResearchGapSerializer

    @action(detail=False, methods=['post'])
    def detect(self, request):
        """
        Triggers GapDetectionAgent to analyze all completed papers and save detected gaps.
        """
        paper_ids = request.data.get('paper_ids', None)
        agent = GapDetectionAgent()
        created_gaps = agent.detect_gaps(paper_ids)
        
        serializer = self.get_serializer(created_gaps, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def generate_idea(self, request, pk=None):
        """
        Triggers ProjectIdeaAgent to construct a project idea based on the gap.
        """
        gap = self.get_object()
        agent = ProjectIdeaAgent()
        idea = agent.generate_idea(gap.id)
        
        if not idea:
            return Response({"error": "Failed to generate project idea"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        serializer = ProjectIdeaSerializer(idea)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectIdeaViewSet(viewsets.ModelViewSet):
    queryset = ProjectIdea.objects.all().order_by('-created_at')
    serializer_class = ProjectIdeaSerializer

    @action(detail=True, methods=['post'])
    def generate_plan(self, request, pk=None):
        """
        Triggers ExperimentPlanningAgent to compile an experimental plan for this idea.
        """
        idea = self.get_object()
        agent = ExperimentPlanningAgent()
        plan = agent.generate_plan(idea.id)
        
        if not plan:
            return Response({"error": "Failed to generate experimental plan"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        serializer = ExperimentalPlanSerializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LiteratureReviewViewSet(viewsets.ModelViewSet):
    queryset = LiteratureReview.objects.all().order_by('-created_at')
    serializer_class = LiteratureReviewSerializer

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Triggers LiteratureReviewAgent to generate a review for the specified papers.
        """
        paper_ids = request.data.get('paper_ids', [])
        title = request.data.get('title', 'Literature Review of Selected Papers')
        
        if not paper_ids:
            return Response({"error": "paper_ids list is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        agent = LiteratureReviewAgent()
        review = agent.generate_review(paper_ids, title)
        
        if not review:
            return Response({"error": "Failed to generate literature review"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ExperimentalPlanViewSet(viewsets.ModelViewSet):
    queryset = ExperimentalPlan.objects.all().order_by('-created_at')
    serializer_class = ExperimentalPlanSerializer
