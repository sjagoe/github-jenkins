from django.http import HttpResponseRedirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.messages.api import get_messages

from social_auth import __version__ as version
from social_auth.utils import setting

from github_jenkins.app.models import Project, JenkinsBuild


def home(request):
    """Home view, displays login mechanism"""
    if request.user.is_authenticated():
        return redirect('projects')
    else:
        return render_to_response('home.html', {'version': version},
                                  RequestContext(request))


@login_required
def projects(request):
    """Displays projects"""
    ctx = {
        'projects': Project.objects.all(),
        'version': version,
        'last_login': request.session.get('social_auth_last_login_backend')
    }
    return render_to_response('projects.html', ctx, RequestContext(request))


@login_required
def pull_requests(request, owner, project):
    project_ = Project.objects.filter(owner=owner, name=project).all()[0]
    pr_builds = [(pr, JenkinsBuild.search_pull_request(project_, pr.number))
                 for pr in project_.get_pull_requests(request.user)]
    ctx = {
        'pr_builds': pr_builds,
        'project': project_,
    }
    return render_to_response('pull_requests.html', ctx,
                              RequestContext(request))


@login_required
def rebuild_pr(request, owner, project, pr):
    project_ = Project.objects.filter(owner=owner, name=project).only()[0]
    pull_request = project_.get_pull_request(request.user, int(pr))
    build = JenkinsBuild.new_from_project_pr(project_, pull_request)
    build.trigger_jenkins()
    return redirect('pull_requests', owner, project)


def error(request):
    """Error view"""
    messages = get_messages(request)
    return render_to_response('error.html', {'version': version,
                                             'messages': messages},
                              RequestContext(request))


def logout(request):
    """Logs out user"""
    auth_logout(request)
    return HttpResponseRedirect('/github-jenkins')
