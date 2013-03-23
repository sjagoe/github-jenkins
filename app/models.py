# Define a custom User class to work with django-social-auth
from django.db import models


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
        return u'{0}/job/{1}'.format(self.location, self.job_name)


class Project(models.Model):
    owner = models.CharField(max_length=128)
    name = models.CharField(max_length=256)

    username = models.CharField(max_length=128)
    password = models.CharField(max_length=128)

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
    project = models.ForeignKey(Project)
    build_number = models.IntegerField()
    build_url = models.CharField(max_length=4096)
    pull_request = models.IntegerField(db_index=True)
    commit = models.CharField(max_length=40)

    @classmethod
    def from_pull_request(cls, pr):
        return cls.objects.filter(pull_request=pr.number).\
            filter(build_number=cls.objects.filter(pull_request=pr.number).\
                   aggregate(Max('build_number'))['build_number__max']).all()

    class Meta:
        unique_together = ('project', 'build_number')
