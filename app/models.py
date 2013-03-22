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


class Project(models.Model):
    owner = models.CharField(max_length=128)
    name = models.CharField(max_length=256)

    def get_pull_requests(self, user):
        gh = get_gh(user)
        repo = gh.get_repo(self.full_name)
        return repo.get_pulls()

    @property
    def full_name(self):
        return '{0}/{1}'.format(self.owner, self.name)

    class Meta:
        unique_together = ('owner', 'name')
