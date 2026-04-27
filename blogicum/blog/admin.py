from django.contrib import admin
from .models import Topic, Venue, Article, Discussion


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'created_at')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'pub_date', 'is_published')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'text')


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'post', 'created_at')
    search_fields = ('text',)
