import os
import json
import re
import random
import openai
import google.generativeai as genai

class AIService:
    @classmethod
    def _get_api_client(cls):
        """
        Determines which client to use based on env variables.
        Returns: ('gemini', api_key) or ('openai', api_key) or (None, None)
        """
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            return "gemini", gemini_key
            
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return "openai", openai_key
            
        return None, None

    @classmethod
    def _call_gemini(cls, api_key, prompt, system_instruction=None):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={"response_mime_type": "application/json"},
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {str(e)}. Falling back to Mock.")
            return None

    @classmethod
    def _call_openai(cls, api_key, prompt, system_instruction=None):
        try:
            client = openai.OpenAI(api_key=api_key)
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {str(e)}. Falling back to Mock.")
            return None

    @classmethod
    def generate_summary(cls, text):
        """
        Analyzes research paper text and returns a dictionary with summary,
        objectives, methodology, dataset_info, results_conclusions, and keywords.
        """
        system_instruction = (
            "You are an expert academic research assistant. Extract details from the provided research paper text. "
            "You MUST return a JSON object with the following fields: "
            "summary (paragraph), objectives (list of strings), methodology (paragraph), "
            "dataset_info (paragraph describing datasets used or 'Not specified'), "
            "results_conclusions (paragraph summarizing findings), keywords (list of strings)."
        )
        prompt = f"Analyze the following research paper text and extract the required fields in JSON:\n\n{text[:15000]}"
        
        provider, api_key = cls._get_api_client()
        result_text = None
        
        if provider == "gemini":
            result_text = cls._call_gemini(api_key, prompt, system_instruction)
        elif provider == "openai":
            result_text = cls._call_openai(api_key, prompt, system_instruction)
            
        if result_text:
            try:
                # Clean up json wrappers if any
                clean_json = re.sub(r'^```json\s*|\s*```$', '', result_text.strip())
                return json.loads(clean_json)
            except Exception as e:
                print(f"JSON parsing error: {e}")
                
        # If API fails or is not configured, run Mock AI
        return cls._mock_summary(text)

    @classmethod
    def detect_gaps(cls, papers):
        """
        Analyze multiple papers (list of dict with id, title, content, summary)
        and identify potential research gaps.
        Returns a list of dictionaries with: title, description, confidence_score, supporting_papers_ids.
        """
        if not papers:
            return []
            
        system_instruction = (
            "You are a Senior Research Strategist. Compare the analyzed papers. "
            "Identify 3 distinct research gaps/limitations. "
            "You MUST return a JSON object containing a key 'gaps' which is a list of objects. "
            "Each object must have: 'title' (short descriptive name), 'description' (detailed explanation "
            "of what is missing or underexplored), 'confidence_score' (integer between 0 and 100), "
            "'novelty_score' (integer between 0 and 100), 'impact_score' (integer between 0 and 100), "
            "'difficulty_score' (integer between 0 and 100), "
            "'supporting_papers' (list of titles of the papers that highlight this gap)."
        )
        
        papers_summary_str = ""
        for i, p in enumerate(papers):
            papers_summary_str += f"Paper {i+1}: {p.get('title')}\nSummary: {p.get('summary')}\nMethodology: {p.get('methodology')}\n\n"
            
        prompt = f"Compare these research papers to find research gaps:\n\n{papers_summary_str}"
        
        provider, api_key = cls._get_api_client()
        result_text = None
        
        if provider == "gemini":
            result_text = cls._call_gemini(api_key, prompt, system_instruction)
        elif provider == "openai":
            result_text = cls._call_openai(api_key, prompt, system_instruction)
            
        if result_text:
            try:
                clean_json = re.sub(r'^```json\s*|\s*```$', '', result_text.strip())
                parsed = json.loads(clean_json)
                if 'gaps' in parsed:
                    return parsed['gaps']
                return parsed
            except Exception as e:
                print(f"JSON parsing error: {e}")
                
        return cls._mock_gaps(papers)

    @classmethod
    def generate_project_idea(cls, gap_title, gap_description):
        """
        Generates a project idea from a research gap.
        Returns a dictionary with: title, problem_statement, proposed_methodology,
        expected_outcome, difficulty_level, innovation_score.
        """
        system_instruction = (
            "You are a Research Innovation Architect. Based on the research gap, propose a concrete project idea. "
            "You MUST return a JSON object with: 'title', 'problem_statement', "
            "'proposed_methodology', 'expected_outcome', 'difficulty_level' (Easy, Medium, Hard, Advanced), "
            "'innovation_score' (float between 1.0 and 10.0), 'novelty_score' (integer between 0 and 100), "
            "'impact_score' (integer between 0 and 100), 'difficulty_score' (integer between 0 and 100), "
            "'estimated_timeline' (string, one of: '1-2 Weeks', '1 Month', '2-3 Months', '3-6 Months', '6+ Months')."
        )
        prompt = f"Propose a project idea for this research gap:\nGap Title: {gap_title}\nDescription: {gap_description}"
        
        provider, api_key = cls._get_api_client()
        result_text = None
        
        if provider == "gemini":
            result_text = cls._call_gemini(api_key, prompt, system_instruction)
        elif provider == "openai":
            result_text = cls._call_openai(api_key, prompt, system_instruction)
            
        if result_text:
            try:
                clean_json = re.sub(r'^```json\s*|\s*```$', '', result_text.strip())
                return json.loads(clean_json)
            except Exception as e:
                print(f"JSON parsing error: {e}")
                
        return cls._mock_project_idea(gap_title, gap_description)

    @classmethod
    def generate_literature_review(cls, papers):
        """
        Generates a literature review based on selected papers.
        Returns a dictionary with: introduction, existing_approaches, comparison_of_methods,
        limitations, research_opportunities, references.
        """
        system_instruction = (
            "You are a Principal Academic Writer. Synthesize a structured literature review. "
            "You MUST return a JSON object with: 'introduction', 'existing_approaches', "
            "'comparison_of_methods', 'limitations', 'research_opportunities', 'references' (bulleted list)."
        )
        
        papers_summary_str = ""
        for i, p in enumerate(papers):
            papers_summary_str += f"Paper {i+1}: {p.get('title')} by {p.get('authors')}\nSummary: {p.get('summary')}\nMethodology: {p.get('methodology')}\n\n"
            
        prompt = f"Create a structured literature review for the following papers:\n\n{papers_summary_str}"
        
        provider, api_key = cls._get_api_client()
        result_text = None
        
        if provider == "gemini":
            result_text = cls._call_gemini(api_key, prompt, system_instruction)
        elif provider == "openai":
            result_text = cls._call_openai(api_key, prompt, system_instruction)
            
        if result_text:
            try:
                clean_json = re.sub(r'^```json\s*|\s*```$', '', result_text.strip())
                return json.loads(clean_json)
            except Exception as e:
                print(f"JSON parsing error: {e}")
                
        return cls._mock_literature_review(papers)

    @classmethod
    def generate_experimental_plan(cls, project_title, problem_statement, methodology):
        """
        Proposes an experimental plan for a project idea.
        Returns a dictionary with: datasets, ai_models, training_approach, evaluation_metrics, expected_challenges.
        """
        system_instruction = (
            "You are a Senior AI and Machine Learning Architect. Propose a highly custom, project-specific experimental validation protocol. "
            "Do NOT use generic or static templates. Tailor the datasets, models, training approach, and metrics specifically to the project's domain, problem, methodology, and outcome.\n\n"
            "You MUST return a JSON object with the following fields:\n"
            "- 'datasets': A list of 2-4 highly specific, relevant datasets or benchmark sources (e.g., 'TriviaQA mobile index' instead of 'academic benchmarks').\n"
            "- 'ai_models': A list of 2-4 specific model architectures or baseline configurations to test.\n"
            "- 'training_approach': A detailed paragraph describing the training strategy, optimization protocols, and custom loss functions.\n"
            "- 'evaluation_metrics': A list of specific metrics AND concrete success criteria thresholds (e.g., 'Raspberry Pi CPU Latency < 150ms', 'Hallucination rate < 10%').\n"
            "- 'expected_challenges': A detailed paragraph describing specific engineering/scientific risks and their corresponding mitigations."
        )
        prompt = (
            f"Generate a customized validation protocol for this project idea:\n\n"
            f"Project Title: {project_title}\n"
            f"Problem Statement: {problem_statement}\n"
            f"Methodology: {methodology}\n\n"
            f"Make sure to formulate different protocols for different types of projects (e.g. latency/memory for edge RAG, faithfulness/trust for explainable AI, consistency/truthfulness for hallucination detection)."
        )
        
        provider, api_key = cls._get_api_client()
        result_text = None
        
        if provider == "gemini":
            result_text = cls._call_gemini(api_key, prompt, system_instruction)
        elif provider == "openai":
            result_text = cls._call_openai(api_key, prompt, system_instruction)
            
        if result_text:
            try:
                clean_json = re.sub(r'^```json\s*|\s*```$', '', result_text.strip())
                return json.loads(clean_json)
            except Exception as e:
                print(f"JSON parsing error: {e}")
                
        return cls._mock_experimental_plan(project_title, problem_statement, methodology)

    # ================= MOCK FALLBACKS =================

    @classmethod
    def _mock_summary(cls, text):
        """
        Scans paper text for sections and extracts actual sentences contextually.
        """
        # Find paper Title and Authors (heuristic: first few lines)
        lines = [line.strip() for line in text.split('\n') if line.strip()][:10]
        title = lines[0] if lines else "Research Paper"
        
        # Simple extraction heuristics using regex
        objectives = []
        methodology_sentences = []
        findings_sentences = []
        datasets = []
        
        # Search for patterns
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for s in sentences:
            s = s.strip().replace('\n', ' ')
            if len(s) < 30 or len(s) > 300:
                continue
            
            # Extract objective clues
            if any(k in s.lower() for k in ["objective", "aim of this", "we propose to", "purpose of", "this paper investigates"]):
                if len(objectives) < 3 and s not in objectives:
                    objectives.append(s)
            
            # Extract methodology clues
            if any(k in s.lower() for k in ["methodology", "proposed framework", "architecture", "algorithm", "we implement", "experimental setup"]):
                if len(methodology_sentences) < 3:
                    methodology_sentences.append(s)
                    
            # Extract findings clues
            if any(k in s.lower() for k in ["conclude", "we found that", "results show", "outperforms", "significant improvement", "experimental results"]):
                if len(findings_sentences) < 3:
                    findings_sentences.append(s)
                    
            # Extract dataset clues
            if any(k in s.lower() for k in ["dataset", "data source", "corpus", "benchmarks"]):
                if len(datasets) < 2 and s not in datasets:
                    datasets.append(s)

        # Fallbacks if regex found nothing
        if not objectives:
            objectives = ["Investigate performance and limitations of the studied architecture.",
                          "Analyze efficiency trade-offs under varying computational bounds."]
        if not methodology_sentences:
            methodology_sentences = ["The methodology focuses on evaluating empirical performance across different baseline configurations."]
        if not findings_sentences:
            findings_sentences = ["The results demonstrate substantial optimization potential, with specific bottlenecks observed in scalable workloads."]
        if not datasets:
            datasets = ["Evaluated on standard benchmark representations and synthetic datasets."]

        # Clean keywords extraction
        words = re.findall(r'\b[a-zA-Z]{5,15}\b', text.lower())
        stop_words = {"this", "that", "with", "from", "their", "using", "paper", "proposed", "results", "model", "analysis", "system"}
        keywords = list(set([w for w in words if w not in stop_words]))[:6]
        if not keywords:
            keywords = ["analysis", "evaluation", "methodology", "framework"]

        summary = (
            f"This paper explores {keywords[0] if len(keywords) > 0 else 'research'} concepts, proposing an "
            f"integrated framework to solve key bottlenecks. The authors evaluate their system against baseline "
            f"approaches and detail computational trade-offs, aiming to provide a solid foundation for future designs."
        )

        return {
            "summary": summary,
            "objectives": objectives,
            "methodology": " ".join(methodology_sentences),
            "dataset_info": " ".join(datasets),
            "results_conclusions": " ".join(findings_sentences),
            "keywords": keywords
        }

    @classmethod
    def _mock_gaps(cls, papers):
        # We look at the titles and keywords of papers to make gaps contextual
        keywords_pool = []
        for p in papers:
            # check if paper has keywords
            kws = p.get('keywords', [])
            if isinstance(kws, str):
                kws = [k.strip() for k in kws.split(',')]
            keywords_pool.extend(kws)
        
        keywords_pool = list(set([k for k in keywords_pool if k]))
        if len(keywords_pool) < 2:
            keywords_pool = ["Scalability", "Domain Adaptation", "Real-time Execution", "Explainable AI"]

        gaps = [
            {
                "title": f"Robust {keywords_pool[0].capitalize()} in Edge Environments",
                "description": f"The existing papers evaluate performance primarily in controlled server environments. There is a lack of research on adapting these methodology models to resource-constrained edge devices with fluctuating compute capability.",
                "confidence_score": random.randint(82, 92),
                "novelty_score": random.randint(84, 94),
                "impact_score": random.randint(80, 92),
                "difficulty_score": random.randint(70, 85),
                "supporting_papers": [p.get('title') for p in papers[:2]]
            },
            {
                "title": f"Explainable Reasoning for {keywords_pool[1].capitalize()} Architectures",
                "description": f"While current approaches achieve high empirical accuracy, their black-box nature limits deployment in high-stakes fields. A standardized framework for explainability is currently unexplored in literature.",
                "confidence_score": random.randint(85, 95),
                "novelty_score": random.randint(88, 97),
                "impact_score": random.randint(82, 94),
                "difficulty_score": random.randint(65, 80),
                "supporting_papers": [p.get('title') for p in papers]
            },
            {
                "title": f"Cross-Domain Generalization of {keywords_pool[min(2, len(keywords_pool)-1)].capitalize()}",
                "description": f"Most methodology frameworks rely heavily on domain-specific features. A critical research gap is developing unified representations that generalize to unseen target datasets without fine-tuning.",
                "confidence_score": random.randint(78, 88),
                "novelty_score": random.randint(80, 91),
                "impact_score": random.randint(76, 88),
                "difficulty_score": random.randint(72, 88),
                "supporting_papers": [p.get('title') for p in papers]
            }
        ]
        return gaps

    @classmethod
    def _mock_project_idea(cls, gap_title, gap_description):
        title = f"Project: {gap_title.replace('Robust', 'Adaptive').replace('Explainable', 'Intelligent')}"
        problem_statement = (
            f"Currently, there is an unresolved challenge regarding: {gap_description}. "
            f"Existing methods fail to adapt dynamically, leading to degradation of performance and trust."
        )
        proposed_methodology = (
            f"We propose a hierarchical framework that combines self-supervised learning with a meta-adapter layer. "
            f"This allows the system to fine-tune weights on-the-fly based on streaming inputs, mitigating constraints."
        )
        expected_outcome = (
            "An open-source prototype demonstrating a 20% increase in adaptability metrics, "
            "validated through edge hardware deployments and benchmark evaluations."
        )
        
        difficulty_level = random.choice(["Medium", "Hard", "Advanced"])
        innovation_score = round(random.uniform(7.8, 9.4), 1)
        
        novelty_score = random.randint(80, 96)
        impact_score = random.randint(78, 95)
        difficulty_score = random.randint(60, 90)
        estimated_timeline = random.choice(["1-2 Weeks", "1 Month", "2-3 Months", "3-6 Months", "6+ Months"])

        return {
            "title": title,
            "problem_statement": problem_statement,
            "proposed_methodology": proposed_methodology,
            "expected_outcome": expected_outcome,
            "difficulty_level": difficulty_level,
            "innovation_score": innovation_score,
            "novelty_score": novelty_score,
            "impact_score": impact_score,
            "difficulty_score": difficulty_score,
            "estimated_timeline": estimated_timeline
        }

    @classmethod
    def _mock_literature_review(cls, papers):
        # Construct dynamic review content based on paper details
        intro_refs = ", ".join([f"{p.get('title')} ({p.get('authors', 'et al.')})" for p in papers])
        
        introduction = (
            f"Research in this domain has expanded rapidly, highlighted by investigations in {intro_refs}. "
            f"Synthesizing these contributions reveals active progress in optimization, but highlights distinct "
            f"gaps in long-term reliability and adaptability across diverse contexts."
        )
        
        existing_approaches = (
            "Current literature relies heavily on supervised benchmark tuning and rigid model checkpoints. "
            "Authors have focused primarily on model efficiency, scaling parameters to achieve marginal performance gains."
        )
        
        comparison_of_methods = (
            "While early works focus on modular architectures which are interpretable but slow, "
            "more recent approaches leverage end-to-end transformers which offer superior speed but lack explainability."
        )
        
        limitations = (
            "Two primary bottlenecks persist: (1) high sensitivity to out-of-distribution inputs, "
            "and (2) severe performance degradation under constrained computational footprints."
        )
        
        research_opportunities = (
            "Promising avenues include zero-shot cross-domain transfers, hybrid neural-symbolic systems, "
            "and active learning strategies that optimize model checkpoints on streaming local inputs."
        )
        
        references = "\n".join([f"- {p.get('authors', 'Anonymous')}. *{p.get('title')}*. Published Research, 2025." for p in papers])

        return {
            "introduction": introduction,
            "existing_approaches": existing_approaches,
            "comparison_of_methods": comparison_of_methods,
            "limitations": limitations,
            "research_opportunities": research_opportunities,
            "references": references
        }

    @classmethod
    def _mock_experimental_plan(cls, project_title, problem_statement, methodology):
        title_lower = (project_title or "").lower()
        prob_lower = (problem_statement or "").lower()
        method_lower = (methodology or "").lower()
        
        # Check domain: EdgeRAG
        if any(k in title_lower or k in prob_lower or k in method_lower for k in ["rag", "retrieval", "edge", "mobile", "latency", "constrained"]):
            datasets = [
                "TriviaQA passage retrieval index (21M passages)",
                "HotpotQA multi-hop benchmark dataset",
                "MS-MARCO passage ranking benchmark"
            ]
            ai_models = [
                "DistilDPR (dual-encoder retriever backbone)",
                "MobileBERT (4-bit quantized)",
                "Custom lightweight binary embedding adapter"
            ]
            training_approach = (
                "We will adopt a two-phase training protocol. In Phase 1, we freeze the backbone parameters "
                "and train the binary embedding projection adapter on diverse domains. In Phase 2, we perform "
                "quantization-aware fine-tuning (QAT) to reduce precision loss and ensure compatibility with edge CPUs."
            )
            evaluation_metrics = [
                "Passage Retrieval Recall@K (Success: > 85%)",
                "Mobile Device CPU Latency (Success: < 150ms per query)",
                "Embedding Index Memory Footprint (Success: < 100MB)",
                "Exact Match (EM) factuality score"
            ]
            expected_challenges = (
                "Risk: Significant drop in retrieval accuracy due to low-bit binarization. "
                "Mitigation: Implement straight-through estimators (STE) for gradient approximation during adapter "
                "backpropagation, and utilize layer-wise feature imitation loss from a full-precision teacher model."
            )
        # Check domain: Explainable AI
        elif any(k in title_lower or k in prob_lower or k in method_lower for k in ["explain", "interpret", "faithfulness", "attention", "attribute", "rational"]):
            datasets = [
                "CoNLL-2003 Named Entity Recognition benchmark",
                "SQuAD 2.0 explainability validation subset",
                "IMDb sentiment attribution dataset"
            ]
            ai_models = [
                "BERT-Base-Uncased (attention weights visualization baseline)",
                "Llama-3-8B-Instruct (configured for rationale generation)",
                "Integrated Gradients attribution analyzer model"
            ]
            training_approach = (
                "We will train a surrogate explainer model using feature attribution methods (such as Integrated Gradients and attention rollout). "
                "We optimize the generation loop to produce contrastive rationales alongside token predictions, penalizing self-contradictory explanations."
            )
            evaluation_metrics = [
                "Saliency Map Cosine Similarity (Success: > 0.8 compared to human baselines)",
                "User Trust Rating (Success: Mean Likert score > 4.2/5.0)",
                "Feature Attribution Faithfulness (Completeness & Sufficiency scores)",
                "Area Under the Precision-Recall Curve (AUPRC) of attribution maps"
            ]
            expected_challenges = (
                "Risk: Raw attention weights do not always correlate directly with actual model decisions (faithfulness gap). "
                "Mitigation: Implement post-hoc perturbation testing (masking top-k attribution tokens) to verify causal feature importance, "
                "updating the training loss to regularize attention patterns accordingly."
            )
        # Check domain: Hallucination Detection
        elif any(k in title_lower or k in prob_lower or k in method_lower for k in ["hallucinat", "fact", "truth", "consistency", "detect", "contradict"]):
            datasets = [
                "HaluEval comprehensive hallucination benchmark",
                "TruthfulQA alignment evaluation suite",
                "FEVER fact-verification dataset"
            ]
            ai_models = [
                "BART-Score factuality evaluator model",
                "Self-Consistency decoding validator",
                "GPT-4o-Mini reference-based semantic similarity checker"
            ]
            training_approach = (
                "We will train a lightweight classifier to predict token-level and sentence-level factual consistency. "
                "We utilize self-consistency decoding paths to sample alternate completions and compare their semantic overlap using entailment models."
            )
            evaluation_metrics = [
                "Factual Consistency Precision/Recall (Success: F1 > 90%)",
                "Hallucination Rate on TruthfulQA (Success: < 10%)",
                "Natural Language Entailment Score (Success: Entailment probability > 0.92)",
                "ROUGE-L semantic overlap baseline"
            ]
            expected_challenges = (
                "Risk: High latency and cost of querying external reference APIs/LLMs during real-time generation. "
                "Mitigation: Fine-tune a lightweight 3B parameter model specifically on factual entailment pairs, bypassing heavy api requests "
                "via cached vector database indexes of known facts."
            )
        # General Fallback - Dynamic Keyword Extraction
        else:
            # Clean stop words and extract custom keywords
            words = [w.capitalize() for w in re.findall(r'\b[a-zA-Z]{4,20}\b', project_title or "") if w.lower() not in 
                     {"project", "system", "framework", "adaptive", "intelligent", "model", "approach", "using", "based", "design", "method"}]
            kw1 = words[0] if len(words) > 0 else "Baseline"
            kw2 = words[1] if len(words) > 1 else "Target"
            
            datasets = [
                f"Standard open-source {kw1} validation dataset",
                f"Custom synthetic {kw2} test logs",
                f"HuggingFace Hub {kw1.lower()}-{kw2.lower()} domain-specific collection"
            ]
            ai_models = [
                f"Pre-trained {kw1} neural backbone network",
                f"Lightweight {kw2} classification adapter",
                f"Custom hybrid {kw1}{kw2} processor"
            ]
            training_approach = (
                f"We will perform domain adaptation of the {kw1} backbone using self-supervised learning on target datasets. "
                f"Next, we jointly optimize the {kw2} adapter utilizing cross-entropy loss with L2 regularization to prevent overfitting."
            )
            evaluation_metrics = [
                f"{kw1} Accuracy / F1-Score (Success: > 88%)",
                f"{kw2} Processing Latency (Success: < 50ms per inference)",
                f"Model parameter convergence rate (Success: Loss < 0.05)",
                f"Area Under ROC (AUC-ROC) score"
            ]
            expected_challenges = (
                f"Risk: Overfitting to the custom {kw2} training datasets due to limited sample count. "
                f"Mitigation: Apply extensive data augmentation techniques, incorporate dropout layers in the {kw2} adapter, "
                f"and use early stopping based on validation loss."
            )

        return {
            "datasets": datasets,
            "ai_models": ai_models,
            "training_approach": training_approach,
            "evaluation_metrics": evaluation_metrics,
            "expected_challenges": expected_challenges
        }
