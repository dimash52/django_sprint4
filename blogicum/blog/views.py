from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView

from .forms import CommentForm, PostForm, RegistrationForm, UserEditForm
from .models import Category, Comment, Post

POSTS_PER_PAGE = 10

User = get_user_model()


class RegistrationCreateView(CreateView):
    form_class = RegistrationForm
    template_name = 'registration/registration_form.html'

    def get_success_url(self):
        return reverse('login')


def is_author_or_admin(user, obj):
    return user == obj.author


def post_is_public(post):
    return (
        post.is_published
        and post.pub_date <= timezone.now()
        and post.category
        and post.category.is_published
    )


def get_public_posts():
    return Post.objects.select_related(
        'author',
        'category',
        'location',
    ).annotate(comment_count=Count('comments')).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    ).order_by('-pub_date')


def paginate_queryset(request, queryset):
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    page_obj = paginate_queryset(request, get_public_posts())
    return render(
        request,
        'blog/index.html',
        {'page_obj': page_obj},
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_published=True)
    page_obj = paginate_queryset(
        request,
        get_public_posts().filter(category=category),
    )
    return render(
        request,
        'blog/category.html',
        {
            'category': category,
            'page_obj': page_obj,
        },
    )


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related(
            'author',
            'category',
            'location',
        ),
        pk=post_id,
    )
    if request.user != post.author and not post_is_public(post):
        raise Http404
    form = CommentForm()
    comments = post.comments.select_related('author').order_by('created_at')
    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'form': form,
            'comments': comments,
        },
    )


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    queryset = Post.objects.select_related(
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
    page_obj = paginate_queryset(request, queryset.order_by('-pub_date'))
    return render(
        request,
        'blog/profile.html',
        {
            'profile': profile_user,
            'page_obj': page_obj,
        },
    )


@login_required
def edit_profile(request):
    form = UserEditForm(
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
def create_post(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
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
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not is_author_or_admin(request.user, post):
        return redirect('blog:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post.id)
    return render(
        request,
        'blog/create.html',
        {
            'form': form,
            'post': post,
            'is_edit': True,
        },
    )


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not is_author_or_admin(request.user, post):
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    return render(
        request,
        'blog/create.html',
        {
            'form': PostForm(instance=post),
            'post': post,
        },
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not post_is_public(post):
        raise Http404
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)
    comments = post.comments.select_related('author').order_by('created_at')
    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'form': form,
            'comments': comments,
        },
    )


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)
    if not is_author_or_admin(request.user, comment):
        return redirect('blog:post_detail', post_id=post.id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post.id)
    return render(
        request,
        'blog/comment.html',
        {
            'form': form,
            'comment': comment,
            'post': post,
            'is_edit': True,
        },
    )


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)
    if not is_author_or_admin(request.user, comment):
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post.id)
    return render(
        request,
        'blog/comment.html',
        {
            'comment': comment,
            'post': post,
        },
    )
