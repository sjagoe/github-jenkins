import json
import logging

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.messages.api import get_messages

from social_auth import __version__ as version

from github_jenkins.app.models import Project, JenkinsBuild
from github_jenkins.app.debugging import log_error

logger = logging.getLogger(__name__)


@log_error(logger)
def home(request):
    """Home view, displays login mechanism"""
    if request.user.is_authenticated():
        return redirect('projects')
    else:
        return render_to_response('home.html', {'version': version},
                                  RequestContext(request))


@login_required
@log_error(logger)
def projects(request):
    """Displays projects"""
    ctx = {
        'projects': Project.objects.all(),
        'version': version,
        'last_login': request.session.get('social_auth_last_login_backend')
    }
    return render_to_response('projects.html', ctx, RequestContext(request))


def _make_pr_id(pr):
    return 'pull-request-{0}'.format(pr.number)


def _get_pr_build_list(project, pull_requests):
    return [(_make_pr_id(pr), pr, JenkinsBuild.search_pull_request(
        project, pr.number)) for pr in pull_requests]


@login_required
@log_error(logger)
def pull_requests(request, owner, project):
    project_ = Project.objects.filter(owner=owner, name=project).all()[0]
    ctx = {'project': project_}
    return render_to_response('pull_requests.html', ctx,
                              RequestContext(request))


def _get_row_dict(project, pr, build):
    return {
        'open': pr.state == 'open',
        'pr_id': _make_pr_id(pr),
        'pr_issue_url': pr.issue_url,
        'pr_number': pr.number,
        'pr_title': pr.title,
        'build_url': build.build_url if build is not None else None,
        'build_number': build.build_number if build is not None else None,
        'build_status': build.build_status if build is not None else None,
        'build_now_url': reverse(
            'rebuild', kwargs={
                'owner': project.owner,
                'project': project.name,
                'pr': pr.number,
            }),
        'update_url': reverse(
            'update_pull_request', kwargs={
                'owner': project.owner,
                'project': project.name,
                'pr_number': pr.number,
            }),
    }


@login_required
@log_error(logger)
def pull_request_row(request, owner, project, pr_number):
    project_ = Project.objects.filter(owner=owner, name=project).all()[0]
    pr = project_.get_pull_request(request.user, int(pr_number))
    if pr.state != 'open':
        data = {'open': False, 'pr_id': _make_pr_id(pr)}
        return HttpResponse(json.dumps(data), content_type='application/json')
    build = JenkinsBuild.search_pull_request(project_, pr.number)
    row = _get_row_dict(project_, pr, build)
    return HttpResponse(json.dumps(row), content_type='application/json')


@login_required
@log_error(logger)
def new_pull_request_rows(request, owner, project, old_max_pr_number):
    old_max_pr_number = int(old_max_pr_number)
    project_ = Project.objects.filter(owner=owner, name=project).all()[0]

    prs = []
    for pr in project_.get_pull_requests(request.user):
        if pr.number <= old_max_pr_number:
            break
        prs.append(pr)

    pr_builds = _get_pr_build_list(project_, prs)

    if len(pr_builds) > 0:
        max_pr = max(pr.number for _, pr, _ in pr_builds)
    else:
        max_pr = old_max_pr_number

    response = {
        'rows': [_get_row_dict(project_, pr, build)
                 for pr_id, pr, build in pr_builds],
        'update_url': reverse(
            'new_pull_requests', kwargs={
                'owner': project_.owner,
                'project': project_.name,
                'old_max_pr_number': max_pr,
            }),
    }

    return HttpResponse(json.dumps(response), content_type='application/json')


@login_required
@log_error(logger)
def rebuild_pr(request, owner, project, pr):
    project_ = Project.objects.filter(owner=owner, name=project).all()[0]
    pull_request = project_.get_pull_request(request.user, int(pr))
    build = JenkinsBuild.new_from_project_pr(project_, pull_request)
    build.trigger_jenkins()
    return HttpResponse(status=204, content_type='application/json')


@login_required
@log_error(logger)
def add_service_hook(request, owner, project):
    project_ = Project.objects.filter(owner=owner, name=project).all()[0]
    if project_.install_hook(request.user):
        return HttpResponse(status=204, content_type='application/json')
    else:
        return HttpResponse(status=404, content_type='application/json')


@log_error(logger)
def error(request):
    """Error view"""
    messages = get_messages(request)
    return render_to_response('error.html', {'version': version,
                                             'messages': messages},
                              RequestContext(request))


@log_error(logger)
def logout(request):
    """Logs out user"""
    auth_logout(request)
    return HttpResponseRedirect('/github-jenkins')
