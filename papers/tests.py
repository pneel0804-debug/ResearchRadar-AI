from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from papers.models import Paper, PaperChunk
from gaps.models import ResearchGap
from ideas.models import ProjectIdea
from services.pdf_service import PDFService
from services.ai_service import AIService
from ai_agents.agents import PaperReadingAgent, SummaryAgent, GapDetectionAgent

class PDFServiceTest(TestCase):
    def test_clean_text(self):
        dirty_text = "This is a de-\nvelopment of the paper.  It has   multiple spaces."
        clean = PDFService.clean_text(dirty_text)
        self.assertEqual(clean, "This is a development of the paper. It has multiple spaces.")

    def test_split_into_chunks(self):
        text = "word " * 300  # 1500 chars
        chunks = PDFService.split_into_chunks(text, chunk_size=500, chunk_overlap=100)
        self.assertTrue(len(chunks) > 1)
        self.assertTrue(all(len(c) <= 500 for c in chunks))

class AIServiceMockTest(TestCase):
    def test_mock_summary(self):
        text = "Introduction. The objective is to evaluate deep learning frameworks. We propose convolutional nets."
        summary_data = AIService.generate_summary(text)
        self.assertIn("summary", summary_data)
        self.assertTrue(len(summary_data["objectives"]) > 0)
        self.assertTrue(len(summary_data["keywords"]) > 0)

    def test_mock_gaps(self):
        papers = [{"id": "1", "title": "Paper A", "summary": "Summary A", "keywords": "AI, ML"}]
        gaps = AIService.detect_gaps(papers)
        self.assertTrue(len(gaps) > 0)
        self.assertIn("title", gaps[0])
        self.assertIn("description", gaps[0])

class AgentPipelineTest(TestCase):
    def setUp(self):
        # Create a mock paper record
        pdf_content = b"%PDF-1.4 Mock PDF Content"
        uploaded_file = SimpleUploadedFile("test_paper.pdf", pdf_content, content_type="application/pdf")
        self.paper = Paper.objects.create(
            title="Test AI Synthesis Paper",
            authors="John Doe, Jane Smith",
            file=uploaded_file,
            status="PENDING"
        )

    def test_summary_agent_with_extracted_text(self):
        # Setup extracted text on the paper
        self.paper.extracted_text = "Objective: Study neural optimization. Methodology: We evaluate baseline architectures. Findings: Significant performance gains."
        self.paper.save()
        
        agent = SummaryAgent()
        success, msg = agent.analyze_paper(self.paper.id)
        self.assertTrue(success)
        
        # Verify paper was updated
        self.paper.refresh_from_db()
        self.assertIsNotNone(self.paper.summary)
        self.assertTrue(len(self.paper.summary) > 0)
        self.assertIsNotNone(self.paper.keywords)

class PaperAPITest(TestCase):
    def setUp(self):
        # Create a mock paper record
        pdf_content = b"%PDF-1.4 Mock PDF Content"
        uploaded_file = SimpleUploadedFile("test_paper_api.pdf", pdf_content, content_type="application/pdf")
        self.paper = Paper.objects.create(
            title="Test API Paper",
            authors="API Tester",
            file=uploaded_file,
            status="COMPLETED"
        )
        
    def test_delete_paper_api(self):
        from rest_framework.test import APIClient
        client = APIClient()
        paper_id = self.paper.id
        # Reverse detail url for paper
        url = f"/api/papers/{paper_id}/"
        response = client.delete(url)
        self.assertEqual(response.status_code, 204)
        
        # Verify it was deleted from db
        self.assertFalse(Paper.objects.filter(id=paper_id).exists())
