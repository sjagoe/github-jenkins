import json
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from github_jenkins.app.models import Project, JenkinsBuild

logger = logging.getLogger(__name__)


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

    return HttpResponse(status=204)


@csrf_exempt
def github(request):
    data = json.loads(request.body)
    action = data['action']
    if action not in ('opened', 'synchronize'):
        return HttpResponse(status=204)
    pull_request = data['pull_request']

    project_name = pull_request['base']['repo']['full_name']
    project = Project.get(project_name)
    if project is None:
        logger.warn('Project {0!r} not found'.format(project_name))
        return HttpResponse(status=404)

    pr_number = int(pull_request["number"])
    pr_url = pull_request["html_url"]

    try:
        pr = project.get_pull_request(project.user, pr_number)
    except Exception:
        if logger.level == logging.DEBUG:
            exc_info = True
        else:
            exc_info = False
        message = 'Pull request {0!r} not found'.format(pr_number)
        logger.warn(message, exc_info=exc_info)
        return HttpResponse(message, status=404)
    if pr.html_url != pr_url:
        logger.warn(('HTML URL for the pull request does not match what GutHub tells '
                     'us: {0!r} != {1!r}').format(html_url, pr.html_url))
        return HttpResponse(status=404)

    build = JenkinsBuild.new_from_project_pr(project, pr)
    build.trigger_jenkins()

    return HttpResponse(status=204)