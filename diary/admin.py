from django.contrib import admin

from diary.models import Entry


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'content', 'owner__username')
