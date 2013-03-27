from django.contrib import admin

from github_jenkins.app.models import JenkinsBuild, JenkinsJob, Project, \
    PullRequest


class PullRequestAdmin(admin.ModelAdmin):
    list_display = ('number', 'project')
admin.site.register(PullRequest, PullRequestAdmin)


class JenkinsJobAdmin(admin.ModelAdmin):
    list_display = ('location', 'job_name')
admin.site.register(JenkinsJob, JenkinsJobAdmin)


class JenkinsBuildAdmin(admin.ModelAdmin):
    list_display = ('project', 'pull_request', 'build_number')
admin.site.register(JenkinsBuild, JenkinsBuildAdmin)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name')
admin.site.register(Project, ProjectAdmin)
