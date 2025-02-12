from django.contrib import admin

from .models import Category, Location, Post, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'is_published',
        'created_at',
        'slug'
    )
    list_filter = (
        'title',
    )
    search_fields = (
        'title',
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'created_at',
        'is_published'
    )
    list_filter = (
        'name',
    )
    search_fields = (
        'name',
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'pub_date',
        'author',
        'category',
        'location',
    )
    list_filter = (
        'author',
        'category',
        'location'
    )
    search_fields = (
        'title',
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass
