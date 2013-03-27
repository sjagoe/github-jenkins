import json
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from github_jenkins.app.models import Project, JenkinsBuild, PullRequest
from github_jenkins.app.debugging import log_error

logger = logging.getLogger(__name__)


def _get_build(project_name, pr_number, build_number=None):
    try:
        project = Project.get(project_name)
    except Exception:
        logger.exception()
        return None
    if project is None:
        logger.info('project not found: {0!r}'.format(
            project_name))
        return None
    build = JenkinsBuild.search_pull_request(
        project, int(pr_number), build_number=build_number)
    if build is None:
        logger.info('Build not found: PR {0}, build {1}'.format(
            pr_number, build_number))
        return None
    return build


@csrf_exempt
@log_error(logger)
def jenkins(request):
    parameters = json.loads(request.body)

    build_phase = parameters['build']['phase']

    pr_number = parameters['build']['parameters']['PR_NUMBER']
    project_name = parameters['build']['parameters']['GIT_BASE_REPO']

    logger.info('Received Jenkins build update: PR #{0}, {1}: {2}'.format(
        pr_number, project_name, build_phase))

    if build_phase not in ('STARTED', 'COMPLETED'):
        return HttpResponse(status=204)

    build_number = parameters['build']['number']
    build = _get_build(project_name, pr_number, int(build_number))
    if build is None:
        return HttpResponse('Unknown pull request', status=404)

    build.update_from_jenkins_notification(parameters)
    build.notify_github()

    return HttpResponse(status=204)


@csrf_exempt
@log_error(logger)
def github(request):
    data = json.loads(request.body)
    action = data['action']
    pull_request = data['pull_request']
    pr_number = int(pull_request["number"])
    project_name = pull_request['base']['repo']['full_name']
    logger.info('Received event from GitHub: PR #{0}, {1}: {2}'.format(
        pr_number, project_name, action))

    pr = PullRequest.update_pull_request(pr_number, project_name)
    if pr is None:
        return HttpResponse(status=404)

    if action not in ('opened', 'synchronize'):
        return HttpResponse(status=204)

    build = JenkinsBuild.new_from_project_pr(project, pr)
    build.trigger_jenkins()
    build.notify_github()

    return HttpResponse(status=204)
