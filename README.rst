==============
GitHub-Jenkins
==============

This is a project to bridge GitHub and Jenkins to provide support for
automatically building Pull Requests in a similar fashion to Travis-CI.


License
=======

GitHub-Jenkins is available under the terms of the 3-clause BSD license.


Work required
=============

GitHub-Jenkins was mostly written in a weekend to solve an immediate
problem.  As soon as it was ready to fulfil my needs I stopped working
on it to focus on other work.

It is currently in a less-than-ideal state with no tests and is slightly
fragile in some areas.  Configuration is not straightforward and there
is no documentation.  If there is interest in this project, I will try
to rectify that.


Getting Started
===============

In the absence of real documentation, here is the quick and dirty
getting-started guide.


Configuration
-------------

GitHub-Jenkins is largely configured through the Django admin pages,
with some small amount of initial required configuration in the
``github_jenkins/local_settings.py`` file, which is used for
site-specific (private) configuration, and is not versioned in the git
repository.


Site-specific settings
~~~~~~~~~~~~~~~~~~~~~~

An example of the configuration can be found in the
``github_jenkins/local_sessing.example.py`` file.  Required information
is the ``GITHUB_APP_ID`` and the ``GITHUB_API_SECRET``, which must
correspond to an application registered in a GitHub account at
https://github.com/settings/applications.


Application configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

It is recommended that a new GitHub account is created for
GitHub-Jenkins to authenticate for automated building and status
updates.  It is currently an inconvenient process to configure this user
in GitHub-Jenkins.

1. Add the GitHub user to GitHub-Jenkins

   1. Using a browser in private-browsing mode, connect to the local
      GitHub-Jenkins instance in a web browser and log in as the
      GitHub-Jenkins user.  This will add the user to the django
      database.

   2. Edit the URL to point to the following (which will configure
      webhooks): ``/github-jenkins/add_hook/<owner>/<project>/``

2. Configure GitHub-Jenkins

   1. Log in to the django-admin site

   2. Add a Jenkins Job, entering the base location of Jenkins, the job
      name and user credentials.

   3. Add a (GitHub) Project, entering the owner (github user,
   e.g. ``sjagoe``) and project name (e.g. ``github-jenkins``).  Select
   the corresponding GitHub authentication user and the Jenkins job to
   use for building.


Jenkins Job Configuration
-------------------------

The Jenkins Job must be a parameterized job that accepts the following
parameters:

* ``GIT_BASE_REPO``: <missing description>
* ``GIT_HEAD_REPO``: <missing description>
* ``GIT_SHA1``: <missing description>
* ``GITHUB_URL``: <missing description>
* ``PR_NUMBER``: <missing description>

The job must also use the notifications plugin, with a notification
endpoint of ``https://example.com/github-jenkins/notification/jenkins/``.


Dependencies
============

- ``django``
- ``dango-social-auth``
- ``pygithub``
- ``requests``
