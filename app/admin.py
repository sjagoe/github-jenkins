from django.contrib import admin
from app.models import Project

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name')

admin.site.register(Project, ProjectAdmin)
