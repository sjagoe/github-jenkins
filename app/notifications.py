import json
import pprint

from django.http import HttpResponse #, HttpResponseRedirect
# from django.contrib.auth import logout as auth_logout
# from django.contrib.auth.decorators import login_required
# from django.template import RequestContext
# from django.shortcuts import render_to_response, redirect
# from django.contrib.messages.api import get_messages

from app.models import Project, JenkinsBuild
from django.views.decorators.csrf import csrf_exempt


def _get_build(project_name, pr_number):
    try:
        project = Project.get(project_name)
    except Exception:
        return None
    if project is None:
        return None
    build = JenkinsBuild.search_pull_request(project, int(pr_number))
    if build is None:
        return None
    return build


@csrf_exempt
def jenkins(request):
    parameters = json.loads(request.body)
    pprint.pprint(parameters)

    build_phase = parameters['build']['phase']
    if build_phase not in ('STARTED', 'COMPLETED'):
        return HttpResponse(status=204)

    pr_number = parameters['build']['parameters']['PR_NUMBER']
    project_name = parameters['build']['parameters']['GIT_BASE_REPO']

    build = _get_build(project_name, pr_number)
    if build is None:
        return HttpResponse('Unknown pull request', status=404)

    build.update_from_jenkins_notification(parameters)
    build.notify_github()

    return HttpResponse()
