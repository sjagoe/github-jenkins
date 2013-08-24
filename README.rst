==============
Github-Jenkins
==============

This is a project to bridge Github and Jenkins to provide support for
automatically building Pull Requests in a similar fashion to Travis-CI.


License
=======

Github-Jenkins is available under the terms of the 3-clause BSD license.


Work required
=============

Github-Jenkins was mostly written in a weekend to solve an immediate
problem.  As soon as it was ready to fulfil my needs I stopped working
on it to focus on other work.

It is currently in a less-than-ideal state with no tests and is slightly
fragile in some areas.  Configuration is not straightforward and there
is no documentation.  If there is interest in this project, I will try
to rectify that.


Dependencies
============

- ``django``
- ``dango-social-auth``
- ``pygithub``
- ``requests``
