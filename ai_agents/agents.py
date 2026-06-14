import json
import random
from papers.models import Paper, PaperChunk
from gaps.models import ResearchGap
from ideas.models import ProjectIdea
from literature.models import LiteratureReview
from experiments.models import ExperimentalPlan

from services.pdf_service import PDFService
from services.chroma_service import ChromaService
from services.ai_service import AIService

class PaperReadingAgent:
    """
    Agent responsible for extracting raw content from PDF papers,
    cleaning the text, splitting it into semantic chunks, and loading
    them into both PostgreSQL and ChromaDB for vector similarity search.
    """
    def __init__(self):
        self.pdf_service = PDFService()
        self.chroma_service = ChromaService()

    def process_paper(self, paper_id):
        try:
            paper = Paper.objects.get(id=paper_id)
            paper.status = 'PROCESSING'
            paper.processing_percentage = 10
            paper.save()
            
            # 1. Extract text
            raw_text = self.pdf_service.extract_text(paper.file.path)
            
            # Extract file size & page count
            try:
                size_bytes = paper.file.size
                if size_bytes >= 1024 * 1024:
                    paper.pdf_size = f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    paper.pdf_size = f"{size_bytes / 1024:.1f} KB"
            except Exception as e:
                print(f"Error getting file size: {e}")

            try:
                paper.page_count = self.pdf_service.get_page_count(paper.file.path)
            except Exception as e:
                print(f"Error getting page count: {e}")

            paper.processing_percentage = 30
            paper.save()
            
            # 2. Clean text
            clean_text = self.pdf_service.clean_text(raw_text)
            paper.extracted_text = clean_text
            paper.processing_percentage = 40
            paper.save()
            
            # 3. Chunk text
            chunks = self.pdf_service.split_into_chunks(clean_text)
            
            # Remove any existing chunks for this paper first (to avoid duplicates)
            PaperChunk.objects.filter(paper=paper).delete()
            self.chroma_service.delete_paper_chunks(paper.id)
            
            # Save chunks to DB
            paper_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk_obj = PaperChunk(
                    paper=paper,
                    chunk_index=i,
                    text_content=chunk_text
                )
                paper_chunks.append(chunk_obj)
            PaperChunk.objects.bulk_create(paper_chunks)
            paper.processing_percentage = 50
            paper.save()
            
            # Load chunks into ChromaDB
            self.chroma_service.add_chunks(paper.id, chunks)
            paper.processing_percentage = 60
            paper.save()
            
            # 4. Try parsing basic details (like title/authors) from text if not set
            if not paper.title:
                lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
                paper.title = lines[0][:150] if lines else f"Paper {paper.id}"
                
            paper.processing_percentage = 65
            paper.save()
            return True, "Paper processed successfully"
            
        except Exception as e:
            try:
                paper = Paper.objects.get(id=paper_id)
                paper.status = 'FAILED'
                paper.error_message = str(e)
                paper.processing_percentage = 0
                paper.save()
            except:
                pass
            return False, f"Paper processing failed: {str(e)}"


class SummaryAgent:
    """
    Agent responsible for generating a comprehensive summary,
    aims/objectives, methodologies, dataset information, results/conclusions,
    and extraction of key metadata.
    """
    def __init__(self):
        self.ai_service = AIService()

    def analyze_paper(self, paper_id):
        try:
            paper = Paper.objects.get(id=paper_id)
            if not paper.extracted_text:
                return False, "Paper has no extracted text. Run PaperReadingAgent first."
                
            paper.processing_percentage = 70
            paper.save()

            # Call AI analysis
            analysis = self.ai_service.generate_summary(paper.extracted_text)
            
            # Update fields
            paper.summary = analysis.get("summary", "")
            paper.methodology = analysis.get("methodology", "")
            paper.dataset_info = analysis.get("dataset_info", "")
            paper.results_conclusions = analysis.get("results_conclusions", "")
            
            # Convert list fields
            objectives = analysis.get("objectives", [])
            paper.objectives = json.dumps(objectives) if isinstance(objectives, list) else str(objectives)
            
            keywords = analysis.get("keywords", [])
            paper.keywords = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
            
            paper.processing_percentage = 95
            paper.status = 'COMPLETED'
            paper.save()
            return True, "Paper analyzed successfully"
        except Exception as e:
            try:
                paper = Paper.objects.get(id=paper_id)
                paper.status = 'FAILED'
                paper.error_message = str(e)
                paper.processing_percentage = 0
                paper.save()
            except:
                pass
            return False, f"Paper analysis failed: {str(e)}"


class GapDetectionAgent:
    """
    Agent responsible for analyzing multiple research papers to identify
    common themes, frequently used methods, limitations, underexplored areas,
    and formulating concrete research gaps.
    """
    def __init__(self):
        self.ai_service = AIService()

    def detect_gaps(self, paper_ids=None):
        try:
            if paper_ids:
                papers = Paper.objects.filter(id__in=paper_ids, status='COMPLETED')
            else:
                papers = Paper.objects.filter(status='COMPLETED')
                
            if not papers.exists():
                return []
                
            papers_data = []
            for p in papers:
                papers_data.append({
                    "id": str(p.id),
                    "title": p.title,
                    "summary": p.summary or "",
                    "methodology": p.methodology or "",
                    "keywords": p.keywords or ""
                })
                
            gaps = self.ai_service.detect_gaps(papers_data)
            
            created_gaps = []
            for gap in gaps:
                raw_conf = gap.get("confidence_score", 80)
                if raw_conf <= 1.0:
                    conf_val = float(raw_conf * 100)
                else:
                    conf_val = float(raw_conf)
                
                gap_obj = ResearchGap.objects.create(
                    title=gap.get("title", "Unnamed Gap"),
                    description=gap.get("description", ""),
                    confidence_score=conf_val,
                    novelty_score=int(gap.get("novelty_score", random.randint(75, 95))),
                    impact_score=int(gap.get("impact_score", random.randint(75, 95))),
                    difficulty_score=int(gap.get("difficulty_score", random.randint(60, 85)))
                )
                
                # Link supporting papers matching titles
                supp_titles = gap.get("supporting_papers", [])
                for title in supp_titles:
                    # Match title case-insensitively
                    matched_papers = Paper.objects.filter(title__icontains=title.strip())
                    if matched_papers.exists():
                        gap_obj.supporting_papers.add(*matched_papers)
                        
                # If no matching supporting papers, associate with all passed papers
                if not gap_obj.supporting_papers.exists() and papers.exists():
                    gap_obj.supporting_papers.add(*papers)
                    
                gap_obj.save()
                created_gaps.append(gap_obj)
                
            return created_gaps
        except Exception as e:
            print(f"Gap detection failed: {str(e)}")
            return []


class ProjectIdeaAgent:
    """
    Agent responsible for generating fully realized project titles,
    problem statements, proposed methodologies, outcomes, difficulty,
    and innovation ratings based on a detected gap.
    """
    def __init__(self):
        self.ai_service = AIService()

    def generate_idea(self, gap_id):
        try:
            gap = ResearchGap.objects.get(id=gap_id)
            idea_data = self.ai_service.generate_project_idea(gap.title, gap.description)
            
            idea_obj = ProjectIdea.objects.create(
                research_gap=gap,
                title=idea_data.get("title", f"Project Idea: {gap.title}"),
                problem_statement=idea_data.get("problem_statement", ""),
                proposed_methodology=idea_data.get("proposed_methodology", ""),
                expected_outcome=idea_data.get("expected_outcome", ""),
                difficulty_level=idea_data.get("difficulty_level", "MEDIUM").upper(),
                innovation_score=idea_data.get("innovation_score", 7.0),
                novelty_score=int(idea_data.get("novelty_score", random.randint(75, 95))),
                impact_score=int(idea_data.get("impact_score", random.randint(75, 95))),
                difficulty_score=int(idea_data.get("difficulty_score", random.randint(60, 85))),
                estimated_timeline=idea_data.get("estimated_timeline", "2-3 Months")
            )
            return idea_obj
        except Exception as e:
            print(f"Project idea generation failed: {str(e)}")
            return None


class LiteratureReviewAgent:
    """
    Agent responsible for synthesizing selected research papers into a
    fully structured academic literature review.
    """
    def __init__(self):
        self.ai_service = AIService()

    def generate_review(self, paper_ids, title="Literature Review"):
        try:
            papers = Paper.objects.filter(id__in=paper_ids, status='COMPLETED')
            if not papers.exists():
                return None
                
            papers_data = []
            for p in papers:
                papers_data.append({
                    "id": str(p.id),
                    "title": p.title,
                    "authors": p.authors or "Unknown Authors",
                    "summary": p.summary or "",
                    "methodology": p.methodology or "",
                })
                
            review_data = self.ai_service.generate_literature_review(papers_data)
            
            review_obj = LiteratureReview.objects.create(
                title=title,
                introduction=review_data.get("introduction", ""),
                existing_approaches=review_data.get("existing_approaches", ""),
                comparison_of_methods=review_data.get("comparison_of_methods", ""),
                limitations=review_data.get("limitations", ""),
                research_opportunities=review_data.get("research_opportunities", ""),
                references=review_data.get("references", "")
            )
            review_obj.papers.add(*papers)
            review_obj.save()
            return review_obj
        except Exception as e:
            print(f"Literature review generation failed: {str(e)}")
            return None


class ExperimentPlanningAgent:
    """
    Agent responsible for planning architectures, datasets, training loops,
    evaluation protocols, and anticipating potential engineering challenges.
    """
    def __init__(self):
        self.ai_service = AIService()

    def generate_plan(self, idea_id):
        try:
            idea = ProjectIdea.objects.get(id=idea_id)
            plan_data = self.ai_service.generate_experimental_plan(
                idea.title,
                idea.problem_statement,
                idea.proposed_methodology
            )
            
            # Parse list fields to formatted text
            datasets = plan_data.get("datasets", [])
            datasets_str = "\n".join([f"- {d}" for d in datasets]) if isinstance(datasets, list) else str(datasets)
            
            ai_models = plan_data.get("ai_models", [])
            models_str = "\n".join([f"- {m}" for m in ai_models]) if isinstance(ai_models, list) else str(ai_models)
            
            evaluation = plan_data.get("evaluation_metrics", [])
            eval_str = "\n".join([f"- {e}" for e in evaluation]) if isinstance(evaluation, list) else str(evaluation)
            
            plan_obj = ExperimentalPlan.objects.create(
                project_idea=idea,
                title=f"Experimental Plan: {idea.title}",
                datasets=datasets_str,
                ai_models=models_str,
                training_approach=plan_data.get("training_approach", ""),
                evaluation_metrics=eval_str,
                expected_challenges=plan_data.get("expected_challenges", "")
            )
            return plan_obj
        except Exception as e:
            print(f"Experimental plan generation failed: {str(e)}")
            return None
