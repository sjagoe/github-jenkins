import logging
import urllib

import github
import requests

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from github_jenkins.app.debugging import log_error


logger = logging.getLogger(__name__)


def get_gh(user):
    auth = user.social_auth.all()[0]
    token = auth.tokens['access_token']
    return github.Github(token)


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
    # FIXME
    HOOK_URL = 'https://uk.enthought.com/github-jenkins/notification/github/'

    owner = models.CharField(max_length=128)
    name = models.CharField(max_length=256)

    user = models.ForeignKey(User)

    jenkins_job = models.ForeignKey(JenkinsJob)

    def __unicode__(self):
        return u'{0}/{1}'.format(self.owner, self.name)

    def get_hook(self, user):
        repo = self.get_repo(user)
        for hook in repo.get_hooks():
            if hook.config['url'] == self.HOOK_URL:
                return hook
        return None

    def install_hook(self, user):
        if not user.is_staff:
            return False
        hook = self.get_hook(user)
        if hook is None:
            repo = self.get_repo(user)
            config = {u'content_type': u'json',
                      u'url': self.HOOK_URL}
            repo.create_hook('web', config, [u'pull_request'], True)
        return True

    def get_repo(self, user):
         gh = get_gh(user)
         return gh.get_repo(self.full_name)

    def get_pull_requests(self, user):
        return self.get_repo(user).get_pulls()

    def get_pull_request(self, user, pr_id):
        return self.get_repo(user).get_pull(pr_id)

    def reload_pull_requests(self, user):
        found_numbers = set()
        if not user.is_staff:
            return False
        for source_pr in self.get_pull_requests(user):
            pr = PullRequest._update_pull_request(source_pr, self)
            found_numbers.add(pr.number)
        for old_pr in PullRequest.objects.filter(project=self).\
                exclude(number__in=found_numbers).all():
            old_pr.open = False
            old_pr.save()
        return True

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


class PullRequest(models.Model):

    number = models.IntegerField(db_index=True)
    project = models.ForeignKey(Project)

    title = models.CharField(max_length=8192)
    html_url = models.CharField(max_length=4096)
    issue_url = models.CharField(max_length=4096)
    head_repo = models.CharField(max_length=1024)
    head_sha = models.CharField(max_length=40)
    open = models.BooleanField()

    mergeable = models.BooleanField()
    merged = models.BooleanField()

    class Meta:
        unique_together = ('project', 'number')

    def __unicode__(self):
        return u'{0}, {1}'.format(self.project.full_name, self.number)

    @classmethod
    def update_pull_request(cls, pr_number, project_name, html_url):
        project = Project.get(project_name)
        if project is None:
            logger.warn('Project {0!r} not found'.format(project_name))
            return None

        try:
            source_pr = project.get_pull_request(project.user, pr_number)
        except Exception:
            if logger.level == logging.DEBUG:
                exc_info = True
            else:
                exc_info = False
            message = 'Pull request {0!r} not found'.format(pr_number)
            logger.warn(message, exc_info=exc_info)
            return None

        if source_pr.html_url != html_url:
            logger.warn(('HTML URL for the pull request does not match what GutHub tells '
                         'us: {0!r} != {1!r}').format(html_url, source_pr.html_url))
            return None

        logger.info('Passed checks, updating PR {0} {1}'.format(
            project_name, pr_number))

        return cls._update_pull_request(source_pr, project)

    @classmethod
    def _update_pull_request(cls, source_pr, project):
        try:
            pr = cls.objects.get(project=project, number=source_pr.number)
        except ObjectDoesNotExist:
            pr = cls(project=project, number=source_pr.number)

        pr.title = source_pr.title
        pr.html_url = source_pr.html_url
        pr.issue_url = source_pr.issue_url
        pr.head_repo = source_pr.head.repo.full_name
        pr.head_sha = source_pr.head.sha
        pr.open = source_pr.state == 'open'
        pr.mergeable = source_pr.mergeable \
            if source_pr.mergeable is not None else False # FIXME
        pr.merged = source_pr.merged
        pr.save()
        return pr


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

    pull_request = models.ForeignKey(PullRequest)
    build_sha = models.CharField(max_length=40)

    def __repr__(self):
        return u'<JenkinsBuild project={project}, build_number={num}, pr={pr}>'.\
            format(project=self.project, num=self.build_number,
                   pr=self.pull_request.number)

    @property
    def jenkins_trigger_url(self):
        project = self.project
        return '{0}/buildWithParameters?{1}'.format(
            project.jenkins_job.url,
            urllib.urlencode({'GIT_BASE_REPO': project.full_name,
                              'GIT_HEAD_REPO': self.pull_request.head_repo,
                              'GIT_SHA1': self.build_sha,
                              'GITHUB_URL': self.pull_request.html_url,
                              'PR_NUMBER': self.pull_request.number}))

    @classmethod
    def new_from_project_pr(cls, project, pr):
        if isinstance(pr, PullRequest):
            head_sha = pr.head_sha
            pull_request = pr
        else:
            head_sha = pr.head.sha
            pull_request = PullRequest._update_pull_request(pr, project)
        logger.info('Creating build for {0} at {1}'.format(pr.number, head_sha))
        build = JenkinsBuild(project=project, pull_request=pull_request,
                             build_sha=head_sha)
        build.save()
        return build

    @classmethod
    def search_pull_request(cls, project, pr_number, build_number=None):
        try:
            pr = PullRequest.objects.get(number=pr_number)
        except ObjectDoesNotExist:
            return None
        query = cls.objects.filter(project=project, pull_request=pr)
        if build_number is not None:
            subquery = query.filter(build_number=build_number)
            if subquery.count() > 0:
                query = subquery
        query = query.filter(
            id=cls.objects.filter(project=project, pull_request=pr).\
            aggregate(models.Max('id'))['id__max'])
            # FIXME?
            # filter(build_number=cls.objects.filter(
            #     project=project, pull_request=pr).\
            #        aggregate(models.Max('build_number'))['build_number__max'])
        count = query.count()
        if count == 0:
            return None
        elif count == 1:
            return query.all()[0]
        elif count > 1:
            raise Exception('Multiple identical primary keys?')

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

    @log_error(logger)
    def trigger_jenkins(self):
        if self.build_status != JenkinsBuild.WAITING:
            raise Exception('Build already trigerred')
        jenkins = self.project.jenkins_job
        response = requests.post(
            self.jenkins_trigger_url, auth=(jenkins.username, jenkins.password))

    @log_error(logger)
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
        logger.info('Notifying GitHub of status for PR #{0}, {1!r}: {2!r}. {3!r}'.format(
            self.pull_request.number, self.build_sha, status, text))
        gh = get_gh(self.project.user)
        repo = gh.get_repo(self.pull_request.head_repo) # ??
        commit = repo.get_commit(self.build_sha)
        if self.build_url is not None:
            commit.create_status(status, target_url=self.build_url,
                                 description=text)
        else:
            commit.create_status(status, description=text)
