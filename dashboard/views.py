from django.shortcuts import render
from papers.models import Paper
from gaps.models import ResearchGap
from ideas.models import ProjectIdea
from literature.models import LiteratureReview
from experiments.models import ExperimentalPlan

from django.core.management import call_command

def index(request):
    # Auto-seed database if empty and not seeded before
    from django.conf import settings
    from pathlib import Path
    marker_file = Path(settings.BASE_DIR) / '.seeded'
    if Paper.objects.count() == 0 and not marker_file.exists():
        try:
            call_command('seed_data')
            marker_file.touch()
        except Exception as e:
            print(f"Auto-seeding database failed: {e}")

    total_papers = Paper.objects.count()
    completed_papers = Paper.objects.filter(status='COMPLETED').count()
    gaps_count = ResearchGap.objects.count()
    ideas_count = ProjectIdea.objects.count()
    reviews_count = LiteratureReview.objects.count()
    plans_count = ExperimentalPlan.objects.count()
    
    # Calculate some dynamic percentages/stats
    gaps_per_paper = round(gaps_count / max(completed_papers, 1), 1)
    
    # Calculate additional summary metrics
    from django.db.models import Sum, Avg
    completed_papers_qs = Paper.objects.filter(status='COMPLETED')
    total_pages_processed = completed_papers_qs.aggregate(Sum('page_count'))['page_count__sum'] or 0
    
    all_keywords = set()
    for paper in completed_papers_qs:
        if paper.keywords:
            for kw in paper.keywords.split(','):
                kw_clean = kw.strip().lower()
                if kw_clean:
                    all_keywords.add(kw_clean)
    total_domains = len(all_keywords) if all_keywords else 0
    if total_domains == 0 and completed_papers_qs.exists():
        total_domains = 5  # fallback matching seeded keywords
        
    ideas_stats = ProjectIdea.objects.aggregate(
        avg_novelty=Avg('novelty_score'),
        avg_impact=Avg('impact_score'),
        avg_difficulty=Avg('difficulty_score')
    )
    avg_novelty = round(ideas_stats['avg_novelty'] or 0.0, 1)
    avg_impact = round(ideas_stats['avg_impact'] or 0.0, 1)
    avg_difficulty = round(ideas_stats['avg_difficulty'] or 0.0, 1)
    
    recent_papers = Paper.objects.all().order_by('-upload_date')[:5]
    recent_gaps = ResearchGap.objects.all().order_by('-created_at')[:4]
    
    context = {
        'total_papers': total_papers,
        'completed_papers': completed_papers,
        'gaps_count': gaps_count,
        'ideas_count': ideas_count,
        'reviews_count': reviews_count,
        'plans_count': plans_count,
        'gaps_per_paper': gaps_per_paper,
        'total_pages_processed': total_pages_processed,
        'total_domains': total_domains,
        'avg_novelty': avg_novelty,
        'avg_impact': avg_impact,
        'avg_difficulty': avg_difficulty,
        'recent_papers': recent_papers,
        'recent_gaps': recent_gaps,
    }
    return render(request, 'dashboard/index.html', context)

def upload(request):
    papers = Paper.objects.all().order_by('-upload_date')
    return render(request, 'dashboard/upload.html', {'papers': papers})

def summaries(request):
    papers = Paper.objects.filter(status='COMPLETED').order_by('-upload_date')
    all_papers = Paper.objects.all().order_by('-upload_date')
    return render(request, 'dashboard/summaries.html', {'papers': papers, 'all_papers': all_papers})

def gaps(request):
    gaps_list = ResearchGap.objects.all().order_by('-created_at')
    completed_papers = Paper.objects.filter(status='COMPLETED').order_by('title')
    return render(request, 'dashboard/gaps.html', {
        'gaps': gaps_list,
        'papers': completed_papers
    })

def ideas(request):
    ideas_list = ProjectIdea.objects.all().order_by('-created_at')
    gaps_list = ResearchGap.objects.all().order_by('title')
    return render(request, 'dashboard/ideas.html', {
        'ideas': ideas_list,
        'gaps': gaps_list
    })

def literature(request):
    reviews = LiteratureReview.objects.all().order_by('-created_at')
    completed_papers = Paper.objects.filter(status='COMPLETED').order_by('title')
    return render(request, 'dashboard/literature.html', {
        'reviews': reviews,
        'papers': completed_papers
    })

def experiments(request):
    plans = ExperimentalPlan.objects.all().order_by('-created_at')
    ideas_list = ProjectIdea.objects.all().order_by('title')
    return render(request, 'dashboard/experiments.html', {
        'plans': plans,
        'ideas': ideas_list
    })
