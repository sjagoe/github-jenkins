import urllib

from django.db import models
from django.contrib.auth.models import User

import github

import requests


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

    @classmethod
    def get(cls, owner_or_full_name, name=None):
        if '/' in owner_or_full_name and name is not None:
            raise Exception('Can\'t pass full name and name')
        elif '/' not in owner_or_full_name and name is None:
            raise Exception('If the full name is not given, both '
                            'owner and name must be specified')
        elif '/' in owner_or_full_name and name is None:
            owner, name = owner_or_full_name.split('/', 1)
        else:
            owner = owner_or_full_name
        query = cls.objects.filter(owner=owner, name=name)
        if query.count() == 0:
            return None
        return query.all()[0]

    @property
    def full_name(self):
        return '{0}/{1}'.format(self.owner, self.name)

    class Meta:
        unique_together = ('owner', 'name')


class JenkinsBuild(models.Model):

    WAITING = 'Waiting'
    RUNNING = 'Running'
    FAILED = 'Failed'
    ABORTED = 'Aborted'
    SUCCESSFUL = 'Successful'

    project = models.ForeignKey(Project)
    build_name = models.CharField(max_length=256, null=True)
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
    def jenkins_trigger_url(self):
        project = self.project
        return '{0}/buildWithParameters?{1}'.format(
            project.jenkins_job.url,
            urllib.urlencode({'GIT_BASE_REPO': project.full_name,
                              'GIT_HEAD_REPO': self.head_repository,
                              'GIT_SHA1': self.commit,
                              'GITHUB_URL': self.pull_request_url,
                              'PR_NUMBER': self.pull_request}))

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
    def search_pull_request(cls, project, pr_number):
        query = cls.objects.filter(project=project, pull_request=pr_number).\
            filter(build_number=cls.objects.filter(
                project=project, pull_request=pr_number).\
                   aggregate(models.Max('build_number'))['build_number__max'])
        count = query.count()
        if count == 0:
            return None
        elif count == 1:
            return query.all()[0]
        elif count > 1:
            return query.filter(id=cls.objects.filter(pull_request=pr_number).\
                                aggregate(models.Max('id'))['id__max']).all()[0]

    def update_from_jenkins_notification(self, parameters):
        build_phase = parameters['build']['phase']
        self.build_url = parameters['build']['full_url']
        self.build_number = parameters['build']['number']
        self.build_name = parameters['name']

        if build_phase == 'STARTED':
            self.build_status = JenkinsBuild.RUNNING
        else:
            build_status = parameters['build']['status']
            if build_status in ('FAILURE', 'UNSTABLE'):
                self.build_status = JenkinsBuild.FAILED
            elif build_status == 'ABORTED':
                self.build_status = JenkinsBuild.ABORTED
            elif build_status == 'SUCCESS':
                self.build_status = JenkinsBuild.SUCCESSFUL
        self.save()

    def trigger_jenkins(self):
        if self.build_status != JenkinsBuild.WAITING:
            raise Exception('Build already trigerred')
        jenkins = self.project.jenkins_job
        response = requests.post(
            self.jenkins_trigger_url, auth=(jenkins.username, jenkins.password))

    def notify_github(self):
        if self.build_status == JenkinsBuild.WAITING:
            status = 'pending'
            text = 'Build is being scheduled'
        elif self.build_status == JenkinsBuild.RUNNING:
            status = 'pending'
            text = 'Build #{build} is running'
        elif self.build_status == JenkinsBuild.FAILED:
            status = 'failure'
            text = 'Build #{build} failed'
        elif self.build_status == JenkinsBuild.ABORTED:
            status = 'error'
            text = 'Build #{build} aborted'
        elif self.build_status == JenkinsBuild.SUCCESSFUL:
            status = 'success'
            text = 'Build #{build} succeeded'
        else:
            raise Exception('Did not understand status {!r}'.format(
                self.build_status))
        text = text.format(build=self.build_number)
        gh = get_gh(self.project.user)
        repo = gh.get_repo(self.head_repository) # ??
        commit = repo.get_commit(self.commit)
        commit.create_status(status, self.build_url, text)
