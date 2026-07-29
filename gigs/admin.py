from django.contrib import admin

from .models import Category, Gig


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Gig)
class GigAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'poster', 'budget', 'location', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'category__name')
