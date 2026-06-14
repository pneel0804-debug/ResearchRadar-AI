import os
import json
import fitz
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from papers.models import Paper, PaperChunk
from gaps.models import ResearchGap
from ideas.models import ProjectIdea
from literature.models import LiteratureReview
from experiments.models import ExperimentalPlan
from services.chroma_service import ChromaService

class Command(BaseCommand):
    help = "Seeds the database with high-quality academic papers, summaries, gaps, ideas, reviews, and plans, generating real document files."

    def _create_placeholder_pdf(self, filename, title, authors, text_content):
        """
        Generates a valid, renderable PDF placeholder using fitz (PyMuPDF)
        so that clicking 'Open Document' has a real, readable file to load.
        """
        media_papers_dir = os.path.join(settings.MEDIA_ROOT, 'papers')
        os.makedirs(media_papers_dir, exist_ok=True)
        file_path = os.path.join(media_papers_dir, filename)
        
        # Initialize fitz document
        doc = fitz.open()
        page = doc.new_page(width=595, height=842) # A4 Size
        
        # 1. Header Banner (Indigo background)
        page.draw_rect(fitz.Rect(36, 36, 559, 120), color=(0.23, 0.25, 0.46), fill=(0.23, 0.25, 0.46))
        
        # Insert Title (shortened if too long)
        display_title = title if len(title) < 45 else title[:45] + "..."
        page.insert_text(fitz.Point(54, 75), display_title, fontsize=15, color=(1, 1, 1))
        
        # Insert Authors
        display_authors = f"Authors: {authors}" if len(authors) < 70 else f"Authors: {authors[:70]}..."
        page.insert_text(fitz.Point(54, 98), display_authors, fontsize=9, color=(0.85, 0.85, 0.85))
        
        # 2. Page body contents
        page.insert_text(fitz.Point(54, 160), "ABSTRACT & AI EXTRACTS", fontsize=12, color=(0.54, 0.17, 0.89))
        page.draw_line(fitz.Point(54, 170), fitz.Point(180, 170), color=(0.54, 0.17, 0.89), width=1.5)
        
        # Simple word wrap logic
        words = text_content.split(' ')
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 75:
                lines.append(' '.join(current_line))
                current_line = []
        if current_line:
            lines.append(' '.join(current_line))
            
        y = 195
        for line in lines[:25]:
            page.insert_text(fitz.Point(54, y), line, fontsize=9.5, color=(0.15, 0.15, 0.15))
            y += 18
            
        # Draw a subtle watermark footer
        page.insert_text(fitz.Point(54, 800), "Research Gap Finder AI - Academic Knowledge Seeder System", fontsize=8, color=(0.6, 0.6, 0.6))
        
        # Save and close document
        doc.save(file_path)
        doc.close()
        
        return f"papers/{filename}"

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding with physical document files...")
        
        try:
            with transaction.atomic():
                # Clear existing data
                Paper.objects.all().delete()
                ResearchGap.objects.all().delete()
                ProjectIdea.objects.all().delete()
                LiteratureReview.objects.all().delete()
                ExperimentalPlan.objects.all().delete()
                
                chroma = ChromaService()
                # Clear Chroma collection
                try:
                    chroma.client.delete_collection("research_papers")
                except:
                    pass
                chroma.collection = chroma.client.get_or_create_collection(
                    name="research_papers",
                    embedding_function=chroma.embedding_function
                )
                
                # Create files and model instances
                f1 = self._create_placeholder_pdf(
                    "attention_is_all_you_need.pdf",
                    "Attention Is All You Need",
                    "Ashish Vaswani, Noam Shazeer, Niki Parmar, et al.",
                    "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train."
                )
                p1 = Paper.objects.create(
                    title="Attention Is All You Need",
                    authors="Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin",
                    file=f1,
                    status="COMPLETED",
                    pdf_size="2.4 MB",
                    page_count=18,
                    processing_time=12.3,
                    processing_percentage=100,
                    extracted_text="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
                    summary="This seminal paper introduces the Transformer architecture, which replaces recurrent (LSTM/GRU) and convolutional layers entirely with self-attention mechanisms. The model allows for massive parallelization during training, achieving state-of-the-art translation quality while reducing training times significantly.",
                    objectives=json.dumps([
                        "Propose the Transformer network architecture based solely on self-attention mechanisms.",
                        "Eliminate recurrence and convolutions to enable highly parallelized training.",
                        "Evaluate performance on standard WMT 2014 English-to-German and English-to-French machine translation benchmarks."
                    ]),
                    methodology="The Transformer uses stacked self-attention and point-wise, fully connected layers for both the encoder and decoder. Encoder layers utilize multi-head self-attention and position-wise feed-forward networks, while decoder layers insert multi-head attention over the encoder output to resolve sequence alignments.",
                    dataset_info="Evaluated on the WMT 2014 English-to-German dataset (4.5 million sentence pairs) and WMT 2014 English-to-French dataset (36 million sentence pairs).",
                    results_conclusions="The Transformer model achieves state-of-the-art results on translation tasks, outperforming previous recurrent or convolutional benchmarks while training in a fraction of the time. The self-attention mechanism provides superior alignment representations.",
                    keywords="Transformers, Self-Attention, Machine Translation, NLP, Parallel Processing"
                )
                
                f2 = self._create_placeholder_pdf(
                    "bert_pretraining_transformers.pdf",
                    "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                    "Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova",
                    "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks."
                )
                p2 = Paper.objects.create(
                    title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                    authors="Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova",
                    file=f2,
                    status="COMPLETED",
                    pdf_size="1.8 MB",
                    page_count=12,
                    processing_time=9.5,
                    processing_percentage=100,
                    extracted_text="We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks.",
                    summary="BERT introduces a bidirectional approach to pre-training Transformers for language modeling. By masking tokens in sentences and predicting next sentences, BERT learns deep context from both left and right directions, establishing new baselines for fine-tuning on diverse NLP benchmarks.",
                    objectives=json.dumps([
                        "Introduce a deep bidirectional language representation model using Transformers.",
                        "Design pre-training strategies (Masked Language Modeling and Next Sentence Prediction) to capture bidirectional context.",
                        "Demonstrate generalizability by fine-tuning on eleven distinct NLP tasks with minimal architecture modifications."
                    ]),
                    methodology="BERT is structured as a multi-layer bidirectional Transformer encoder. It undergoes pre-training on large corpora using two unsupervised tasks: Masked LM (masking 15% of input tokens) and Next Sentence Prediction (predicting if sentence B follows sentence A).",
                    dataset_info="Pre-trained on BooksCorpus (800 million words) and English Wikipedia (2,500 million words).",
                    results_conclusions="BERT achieves state-of-the-art performance across 11 NLP tasks, including GLUE, SQuAD v1.1, and SQuAD v2.0. The bidirectional context representation outperforms unidirectional (left-to-right) pre-training methods.",
                    keywords="BERT, Bidirectional Encoders, Pre-training, Transfer Learning, Language Representations"
                )
                
                f3 = self._create_placeholder_pdf(
                    "retrieval_augmented_generation_nlp.pdf",
                    "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                    "Patrick Lewis, Ethan Perez, Aleksandara Piktus, et al.",
                    "Large pre-trained language models have been shown to store implicit knowledge in their parameters. However, their ability to access and precisely manipulate knowledge is still limited. We explore Retrieval-Augmented Generation (RAG) models which combine pre-trained parametric (generator) and non-parametric (retriever) memory. RAG models produce responses that are more factual, specific, and diverse than parametric-only models."
                )
                p3 = Paper.objects.create(
                    title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                    authors="Patrick Lewis, Ethan Perez, Aleksandara Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela",
                    file=f3,
                    status="COMPLETED",
                    pdf_size="3.1 MB",
                    page_count=22,
                    processing_time=15.1,
                    processing_percentage=100,
                    extracted_text="Large pre-trained language models have been shown to store implicit knowledge in their parameters. However, their ability to access and precisely manipulate knowledge is still limited. We explore Retrieval-Augmented Generation (RAG) models which combine pre-trained parametric (generator) and non-parametric (retriever) memory. RAG models produce responses that are more factual, specific, and diverse than parametric-only models.",
                    summary="RAG models combine parametric memory (a pre-trained seq2seq generator) with non-parametric memory (a dense passage retriever querying Wikipedia). By retrieving relevant documents dynamically before generating a response, the system significantly improves factuality and mitigates hallucination.",
                    objectives=json.dumps([
                        "Bridge the gap between parametric parameter knowledge and external non-parametric document sources.",
                        "Build an end-to-end differentiable retriever-generator model (RAG).",
                        "Evaluate RAG on open-domain question answering, abstractive QA, and jeopardy generation tasks."
                    ]),
                    methodology="RAG integrates a Dense Passage Retriever (DPR) querying a Wikipedia passage index with a BART generator. The retriever queries passage embeddings using maximum inner product search (MIPS) to retrieve the top documents, which are prepended to the user query for seq2seq generation.",
                    dataset_info="Wikipedia December 2018 dump split into 21-million 100-word passages. Evaluated on Natural Questions, TriviaQA, WebQuestions, and CuratedTREC.",
                    results_conclusions="RAG models establish new state-of-the-art results on open-domain question answering benchmarks, outperforming parametric-only models. It generates more factual, diverse responses and reduces hallucinations.",
                    keywords="RAG, Dense Passage Retrieval, Open-domain QA, Knowledge Retrieval, Hallucination Mitigation"
                )
                
                # Chunks for vector database
                chunks_p1 = [
                    "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration.",
                    "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
                    "The Transformer uses stacked self-attention and point-wise, fully connected layers for both the encoder and decoder to resolve sequence alignments."
                ]
                chunks_p2 = [
                    "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
                    "BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
                    "BERT undergoes pre-training on large corpora using two unsupervised tasks: Masked LM and Next Sentence Prediction."
                ]
                chunks_p3 = [
                    "We explore Retrieval-Augmented Generation (RAG) models which combine pre-trained parametric (generator) and non-parametric (retriever) memory.",
                    "RAG integrates a Dense Passage Retriever (DPR) querying a Wikipedia passage index with a BART generator to extract relevant contexts.",
                    "RAG models produce responses that are more factual, specific, and diverse, effectively mitigating common hallucination bottlenecks."
                ]
                
                # Bulk create PaperChunk in SQL
                chunks_objs = []
                for i, text in enumerate(chunks_p1):
                    chunks_objs.append(PaperChunk(paper=p1, chunk_index=i, text_content=text))
                for i, text in enumerate(chunks_p2):
                    chunks_objs.append(PaperChunk(paper=p2, chunk_index=i, text_content=text))
                for i, text in enumerate(chunks_p3):
                    chunks_objs.append(PaperChunk(paper=p3, chunk_index=i, text_content=text))
                PaperChunk.objects.bulk_create(chunks_objs)
                
                # Add chunks to ChromaDB
                chroma.add_chunks(p1.id, chunks_p1)
                chroma.add_chunks(p2.id, chunks_p2)
                chroma.add_chunks(p3.id, chunks_p3)
                
                # 3. Create Research Gaps
                g1 = ResearchGap.objects.create(
                    title="Real-time Retrieval Latency Bottlenecks in Low-Compute RAG",
                    description="While RAG architectures successfully integrate external documents, Dense Passage Retrieval (DPR) requires massive indexing and maximum inner product searches. Running these retrieval pipelines on edge or low-compute devices in real-time introduces significant latency. Adapting these pipelines to high-throughput, low-latency devices remains an underexplored territory.",
                    confidence_score=89.0,
                    novelty_score=92,
                    impact_score=87,
                    difficulty_score=74
                )
                g1.supporting_papers.add(p3)
                
                g2 = ResearchGap.objects.create(
                    title="Bidirectional Context Representation Overfitting in Generation Tasks",
                    description="BERT's deep bidirectional training is highly effective for encoding and classification but can lead to representation overfitting in open-ended sequence generation. Balancing the bidirectional context encoder representation with causal, auto-regressive decoding constraints is a major gap in modern hybrid generation workflows.",
                    confidence_score=82.0,
                    novelty_score=85,
                    impact_score=90,
                    difficulty_score=68
                )
                g2.supporting_papers.add(p1, p2)
                
                # 4. Create Project Ideas
                idea = ProjectIdea.objects.create(
                    research_gap=g1,
                    title="Project EdgeRAG: Quantized Dual-Encoder Retrieval for Low-Latency Mobile QA",
                    problem_statement="Modern Dense Passage Retrieval models require server-grade GPUs with large memory footprints to query passage indices, rendering them impractical for edge-device deployments.",
                    proposed_methodology="Implement a distilled dual-encoder retriever using binary neural networks (BNNs) to shrink embedding projections, paired with a quantized 3B parameter generative model running local inference.",
                    expected_outcome="A fully working prototype showing a 3x speedup on edge CPUs with less than 2% drop in TriviaQA retrieval accuracy.",
                    difficulty_level="HARD",
                    innovation_score=8.7,
                    novelty_score=91,
                    impact_score=88,
                    difficulty_score=72,
                    estimated_timeline="3-6 Months"
                )
                
                # 5. Create Literature Review
                review = LiteratureReview.objects.create(
                    title="Literature Synthesis: The Evolution of Transformer Encoders and Retrieval Pipelines",
                    introduction="Since the introduction of the Transformer model (Vaswani et al., 2017), language modeling has transitioned from recurrence to self-attention. Bidirectional encoders like BERT (Devlin et al., 2018) further improved context understanding. Recently, Retrieval-Augmented Generation (Lewis et al., 2020) has bridged parametric networks with document databases.",
                    existing_approaches="Early models focused on task-specific fine-tuning of deep bidirectional networks. More recent architectures combine these representations with Dense Passage Retrieval (DPR) to reference external knowledge bases.",
                    comparison_of_methods="Bidirectional encoders offer superior classification scores but lack generative capabilities. Generative models scale well but hallucinate facts, which retrieval-augmented models address by supplying context.",
                    limitations="Main computational limitations include massive GPU memory requirements for vector indexes, high latency during MIPS queries, and generative hallucinations when retrieved context is noisy.",
                    research_opportunities="Promising research opportunities include binary quantization of retrieval weights, unified vector search, and edge-device hardware acceleration.",
                    references="Ashish Vaswani et al. Attention Is All You Need. 2017.\nJacob Devlin et al. BERT: Pre-training of Deep Bidirectional Transformers. 2018.\nPatrick Lewis et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. 2020."
                )
                review.papers.add(p1, p2, p3)
                
                # 6. Create Experimental Plan
                ExperimentalPlan.objects.create(
                    project_idea=idea,
                    title="Experimental Validation Protocol for Project EdgeRAG",
                    datasets="- TriviaQA open-domain QA dataset\n- MS MARCO passage retrieval collection\n- Wikipedia 2020 preprocessed clean dump",
                    ai_models="- DistilDPR (dual-encoder retriever backbone)\n- Llama-3-3B-Instruct (4-bit quantized generator)\n- Custom binary embedding projection layers",
                    training_approach="Knowledge distillation will transfer representation distributions from a full-precision retriever to a 4-bit binary retriever, followed by quantization-aware fine-tuning (QAT) of the Llama generator.",
                    evaluation_metrics="- Recall@K passage retrieval performance\n- Exact Match (EM) and F1 scores on TriviaQA\n- Average token generation latency (ms) on a Raspberry Pi 4 edge platform",
                    expected_challenges="The primary challenge is gradient approximation for binary layers, which we will address using straight-through estimators (STE) to ensure training stability."
                )
                
                # Create seeding marker file
                from pathlib import Path
                Path(settings.BASE_DIR).joinpath('.seeded').touch()
                
            self.stdout.write(self.style.SUCCESS("Database seeded successfully with documents generated!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Seeding failed: {str(e)}"))
            raise e
