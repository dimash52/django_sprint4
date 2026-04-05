from django.shortcuts import get_object_or_404
from django.shortcuts import render
from .models import Category, Post


NUM_ON_MAIN = 5


def index(request):
    template = 'blog/index.html'
    post_list = Post.objects.category_filter()[:NUM_ON_MAIN]
    context = {'post_list': post_list}
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(Post.objects.category_filter(), pk=post_id)
    context = {'post': post}
    return render(request, template, context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, is_published=True, slug=category_slug)
    post_list = category.posts_for_category.publish_filter()
    context = {
        'category': category,
        'post_list': post_list,
    }
    template = 'blog/category.html'
    return render(request, template, context)
