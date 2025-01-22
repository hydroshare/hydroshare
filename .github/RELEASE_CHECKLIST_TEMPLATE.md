<!--
Add the issues included in the release and update this document as release tasks are completed.
-->

### Issues in Release
- [ ] Issue 1
- [ ] Issue 2

<!-- Update the checklist as items are completed -->
### Beta Deployment
- [ ] Diff RC to master to identify and update helm chart for the following files:
  * scripts/templates/docker-compose.template
  * hydroshare/settings.py
  * hydroshare/local_settings.py
- [ ] Determine whether maintenance page will be needed (db migrations etc)
- [ ] Add any management commands necessary for the deploy to the notes section
- [ ] Deployed to Beta
  - [ ] Run collectstatic if it is not run as part of the deployment
- [ ] Review the search and discovery pages
- [ ] Create a new user and update profile
- [ ] Create a new resource, check sharing/permission settings, delete new resource
- [ ] Developers test around issues
- [ ] Hsclient tests pass when targeting beta
- [ ] QA testing around issues
- [ ] Stakeholders approval

<!-- Update the checklist as items are completed -->
### Production Deployment
- [ ] Deployed to Production
  * Make manual changes to files identified in Beta Deployment
  * Run collectstatic if it is not run as part of the deployment
- [ ] Review the search and discovery pages
- [ ] Create a new user and update profile
- [ ] Create a new resource, check sharing/permission settings, delete new resource
- [ ] Developers test around issue

### Notes relevant to deployment
1. [Enter Notes here]
