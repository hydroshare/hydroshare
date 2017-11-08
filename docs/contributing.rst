Contributing
============

We want you to contribute to Hydroshare development, and we want you to be
as successful as possible in doing so. This document's aim is to provide you
with everything you need to succeed in your contributions.

Just Have a Question or Want to Report a Bug?
---------------------------------------------

We defintely want your feedback. There's a few ways this can go.

- If you have a bug, please open an `issue here on GitHub`_
- If you want to have a discussion, or if you have a question, email help@cuahsi.org. You can also request an invite to our Slack team.
.. _issue here on GitHub: https://github.com/hydroshare/hydroshare/issues/new

Want to Develop a Hydroshare App?
---------------------------------

Apps are generally developed as web applications that interact with our system via OAuth and the REST API.

Documentation is available `here`_.

.. _here: https://help.hydroshare.org/apps/

Want to Develop on Hydroshare Itself?
-------------------------------------

#) Fork the repo under your own name

#) Set up your Hydroshare development environment by following the `installation directions`_

#) Create an issue at the main hydroshare/hydroshare repository to start a discussion

#) Make the required edits to the code

#) Push to your fork and `submit a pull request`_ Be sure you include the text "fixes #" and then the id number of the issue you created directly after the "#".

.. _installation directions: https://github.com/hydroshare/hydroshare#simplified-installation-instructions
.. _submit a pull request: https://github.com/hydroshare/hydroshare/compare/

After You've Submitted a Pull Request
-------------------------------------

The Hydroshare team does our best to respond to pull requests within three business days.

Starting on Sept 1, 2017, CUAHSI will assume the role of the "benevolent dictator" of the production Hydroshare code base. After that point, pull requests into develop (and ultimately master) will only be merged by CUAHSI staff or other appointed staff from partner institutions. Other users can still:

#) Create issues and/or pull requests
#) Request reviews from anybody
#) Participate in code reviews

Pull requests will not be merged until at least one code review is accepted. Additionally, a stakeholder outside of the core development team must review the work to make sure that their issue is resolved or that it doesn't cause any additional technical or philosophical problems.

We may suggest some changes or improvements or alternatives. Below is a list of best practices that will help expedite the process of accepting developer code into the master branch:

- Creating an issue to pair your pull request with
- Including a reference to the corresponding issue in the description of the pull request
- Writing unit and functional tests to compliment the feature or bugfix code you've written
- Following the `PEP8 style guide`_
- Writing `clear and concise commit messages` to help code reviewers

.. _PEP8 style guide: https://www.python.org/dev/peps/pep-0008/
.. _clear and concise commit messages: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
