from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView

from .forms import DiscussionForm, ArticleForm, SignUpForm, ProfileEditForm
from .models import Topic, Discussion, Article

ARTICLES_PER_PAGE = 10

User = get_user_model()


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/registration_form.html'

    def get_success_url(self):
        return reverse('login')


def user_can_edit(user, obj):
    return user == obj.author or user.is_staff or user.is_superuser


def is_article_visible(article):
    return (
        article.is_published
        and article.pub_date <= timezone.now()
        and article.category
        and article.category.is_published
    )


def get_published_articles():
    return Article.objects.select_related(
        'author',
        'category',
        'location',
    ).annotate(comment_count=Count('comments')).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    ).order_by('-pub_date')


def paginate(request, queryset):
    paginator = Paginator(queryset, ARTICLES_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def homepage(request):  # бывшая index
    page_obj = paginate(request, get_published_articles())
    return render(
        request,
        'blog/index.html',
        {'page_obj': page_obj},
    )


def topic_posts(request, slug):
    topic = get_object_or_404(Topic, slug=slug, is_published=True)
    page_obj = paginate(
        request,
        get_published_articles().filter(category=topic),
    )
    return render(
        request,
        'blog/category.html',
        {
            'category': topic,
            'page_obj': page_obj,
        },
    )


def article_detail(request, post_id):
    article = get_object_or_404(
        Article.objects.select_related(
            'author',
            'category',
            'location',
        ),
        pk=post_id,
    )
    if request.user != article.author and not is_article_visible(article):
        from django.http import Http404
        raise Http404
    discussion_form = DiscussionForm() if request.user.is_authenticated else None
    discussions = article.comments.select_related(
        'author').order_by('created_at')
    return render(
        request,
        'blog/detail.html',
        {
            'post': article,
            'comment_form': discussion_form,
            'comments': discussions,
        },
    )


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    queryset = Article.objects.select_related(
        'author',
        'category',
        'location',
    ).annotate(comment_count=Count('comments')).filter(author=profile_user)
    if request.user != profile_user:
        queryset = queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    page_obj = paginate(request, queryset.order_by('-pub_date'))
    return render(
        request,
        'blog/profile.html',
        {
            'profile': profile_user,
            'page_obj': page_obj,
        },
    )


@login_required
def update_profile(request):
    form = ProfileEditForm(
        request.POST or None,
        instance=request.user,
    )
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    return render(
        request,
        'blog/user.html',
        {'form': form},
    )


@login_required
def new_article(request):
    form = ArticleForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        article = form.save(commit=False)
        article.author = request.user
        article.save()
        return redirect('blog:profile', username=request.user.username)
    return render(
        request,
        'blog/create.html',
        {
            'form': form,
            'is_edit': False,
        },
    )


@login_required
def edit_article(request, post_id):
    article = get_object_or_404(Article, pk=post_id)
    if not user_can_edit(request.user, article):
        return redirect('blog:post_detail', post_id=article.id)
    form = ArticleForm(
        request.POST or None,
        files=request.FILES or None,
        instance=article,
    )
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=article.id)
    return render(
        request,
        'blog/create.html',
        {
            'form': form,
            'post': article,
            'is_edit': True,
        },
    )


@login_required
def delete_article(request, post_id):
    article = get_object_or_404(Article, pk=post_id)
    if not user_can_edit(request.user, article):
        return redirect('blog:post_detail', post_id=article.id)
    if request.method == 'POST':
        article.delete()
        return redirect('blog:index')
    return render(
        request,
        'blog/delete.html',
        {'post': article},
    )


@login_required
def add_discussion(request, post_id):
    article = get_object_or_404(Article, pk=post_id)
    if not is_article_visible(article) and request.user != article.author:
        from django.http import Http404
        raise Http404
    form = DiscussionForm(request.POST or None)
    if form.is_valid():
        discussion = form.save(commit=False)
        discussion.author = request.user
        discussion.post = article
        discussion.save()
    return redirect('blog:post_detail', post_id=article.id)


@login_required
def edit_discussion(request, post_id, comment_id):
    article = get_object_or_404(Article, pk=post_id)
    discussion = get_object_or_404(Discussion, pk=comment_id, post=article)
    if not user_can_edit(request.user, discussion):
        return redirect('blog:post_detail', post_id=article.id)
    form = DiscussionForm(request.POST or None, instance=discussion)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=article.id)
    return render(
        request,
        'blog/comment.html',
        {
            'form': form,
            'comment': discussion,
            'post': article,
            'is_edit': True,
        },
    )


@login_required
def delete_discussion(request, post_id, comment_id):
    article = get_object_or_404(Article, pk=post_id)
    discussion = get_object_or_404(Discussion, pk=comment_id, post=article)
    if not user_can_edit(request.user, discussion):
        return redirect('blog:post_detail', post_id=article.id)
    if request.method == 'POST':
        discussion.delete()
        return redirect('blog:post_detail', post_id=article.id)
    return render(
        request,
        'blog/delete.html',
        {
            'comment': discussion,
            'post': article,
        },
    )
