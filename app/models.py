import urllib

from django.db import models
from django.contrib.auth.models import User

import github


def get_gh(user):
    auth = user.social_auth.all()[0]
    token = auth.tokens['access_token']
    return github.Github(token)


# def get_projects(user):
#     gh = get_gh(user)
#     for project in Project.objects.all():
#         yield gh.get_repo(project.full_name)


class CustomUserManager(models.Manager):
    def create_user(self, username, email):
        return self.model._default_manager.create(username=username)


class CustomUser(models.Model):
    username = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    def is_authenticated(self):
        return True


class JenkinsJob(models.Model):
    location = models.CharField(max_length=2048)
    job_name = models.CharField(max_length=2048)

    username = models.CharField(max_length=128)
    password = models.CharField(max_length=128)

    def __unicode__(self):
        return u'{0}: {1}'.format(self.location, self.job_name)

    @property
    def url(self):
        return u'{0}/job/{1}'.format(self.location, self.job_name)


class Project(models.Model):
    owner = models.CharField(max_length=128)
    name = models.CharField(max_length=256)

    user = models.ForeignKey(User)

    jenkins_job = models.ForeignKey(JenkinsJob)

    def __unicode__(self):
        return u'{0}/{1}'.format(self.owner, self.name)

    def get_pull_requests(self, user):
        gh = get_gh(user)
        repo = gh.get_repo(self.full_name)
        return repo.get_pulls()

    def get_pull_request(self, user, pr_id):
        gh = get_gh(user)
        repo = gh.get_repo(self.full_name)
        return repo.get_pull(pr_id)

    @property
    def full_name(self):
        return '{0}/{1}'.format(self.owner, self.name)

    class Meta:
        unique_together = ('owner', 'name')


class JenkinsBuild(models.Model):

    WAITING = 'Waiting'
    RUNNING = 'Running'
    FAILED = 'Failed'
    COMPLETED = 'Completed'

    project = models.ForeignKey(Project)
    build_number = models.IntegerField(null=True)
    build_url = models.CharField(max_length=4096, null=True)
    build_status = models.CharField(max_length=16, default=WAITING)

    pull_request = models.IntegerField(db_index=True)
    pull_request_url = models.CharField(max_length=4096)
    commit = models.CharField(max_length=40)
    head_repository = models.CharField(max_length=512)

    def __repr__(self):
        return u'<JenkinsBuild project={project}, build_number={num}, pr={pr}>'.\
            format(project=self.project, num=self.build_number,
                   pr=self.pull_request)

    @property
    def trigger_url(self):
        project = self.project
        return '{0}/buildWithParameters?{1}'.format(
            project.jenkins_job.url,
            urllib.urlencode({'GIT_BASE_REPO': project.full_name,
                              'GIT_HEAD_REPO': self.head_repository,
                              'GIT_SHA1': self.commit,
                              'GITHUB_URL': self.pull_request_url}))

    @classmethod
    def new_from_project_pr(cls, project, pr):
        build = JenkinsBuild(project=project,
                             pull_request=pr.number,
                             pull_request_url=pr.issue_url,
                             commit=pr.head.sha,
                             head_repository=pr.head.repo.full_name)
        build.save()
        return build

    @classmethod
    def search_pull_request(cls, pr):
        query = cls.objects.filter(pull_request=pr.number).\
            filter(build_number=cls.objects.filter(pull_request=pr.number).\
                   aggregate(models.Max('build_number'))['build_number__max'])
        count = query.count()
        if count == 0:
            return None
        elif count == 1:
            return query.all()[0]
        elif count > 1:
            return query.filter(id=cls.objects.filter(pull_request=pr.number).\
                                aggregate(models.Max('id'))['id__max']).all()[0]
