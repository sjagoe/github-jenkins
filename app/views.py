from django.http import HttpResponseRedirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.messages.api import get_messages

from social_auth import __version__ as version
from social_auth.utils import setting

import requests

from app.models import Project, JenkinsBuild


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
    project_ = Project.objects.filter(owner=owner, name=project).only()[0]
    pr_builds = ((pr, JenkinsBuild.search_pull_request(pr))
                 for pr in project_.get_pull_requests(request.user))
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
    jenkins = project_.jenkins_job
    response = requests.post(build.trigger_url, auth=(jenkins.username, jenkins.password))
    return redirect('pull_requests', owner, project)


@login_required
def done(request):
    """Login complete view, displays user data"""
    ctx = {
        'version': version,
        'last_login': request.session.get('social_auth_last_login_backend')
    }
    return render_to_response('done.html', ctx, RequestContext(request))


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


def form(request):
    if request.method == 'POST' and request.POST.get('username'):
        name = setting('SOCIAL_AUTH_PARTIAL_PIPELINE_KEY', 'partial_pipeline')
        request.session['saved_username'] = request.POST['username']
        backend = request.session[name]['backend']
        return redirect('socialauth_complete', backend=backend)
    return render_to_response('form.html', {}, RequestContext(request))


def form2(request):
    if request.method == 'POST' and request.POST.get('first_name'):
        request.session['saved_first_name'] = request.POST['first_name']
        name = setting('SOCIAL_AUTH_PARTIAL_PIPELINE_KEY', 'partial_pipeline')
        backend = request.session[name]['backend']
        return redirect('socialauth_complete', backend=backend)
    return render_to_response('form2.html', {}, RequestContext(request))


def close_login_popup(request):
    return render_to_response('close_popup.html', {}, RequestContext(request))
