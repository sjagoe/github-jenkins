from django.contrib import admin
from app.models import JenkinsJob, Project


class JenkinsJobAdmin(admin.ModelAdmin):
    list_display = ('location', 'job_name')
admin.site.register(JenkinsJob, JenkinsJobAdmin)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name')
admin.site.register(Project, ProjectAdmin)
