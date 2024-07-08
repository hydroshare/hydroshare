<!--
Add the issues included in the release and update this document as release tasks are completed.
-->

### Issues in Release
- [ ] Issue 1
- [ ] Issue 2

<!-- Update the checklist as items are completed -->
### Beta Deployment
- [ ] Diff RC to master to identify and manually make changes in the following files:
  * hsctl
  * config/hydroshare-config.yaml
  * scripts/templates/docker-compose.template
- [ ] Changes in hydroshare/local_settings.py need to be coordinated for manual update
- [ ] Smoke test active worker before swap, note whether maintenance will be needed (make sure that you check the active worker AFTER the db migrations have run)
- [ ] Add any management commands necessary for the deploy to the notes section
- [ ] Deployed to Beta
- [ ] Review the search and discovery pages
- [ ] Create a new user and update profile
- [ ] Create iROD account, test connection and delete iROD account
- [ ] Create a new resource, check sharing/permission settings, delete new resource
- [ ] Developers test around issues
- [ ] Hsclient tests pass when targeting beta
- [ ] QA testing around issues
- [ ] Stakeholders approval

<!-- Update the checklist as items are completed -->
### Production Deployment
- [ ] Snapshot the DB and iRods VM before deploy
- [ ] Deployed to Production
  * Make manual changes to files identified in Beta Deployment
- [ ] Review the search and discovery pages
- [ ] Create a new user and update profile
- [ ] Create iROD account, test connection and delete iROD account
- [ ] Create a new resource, check sharing/permission settings, delete new resource
- [ ] Developers test around issue

### Notes relevant to deployment
1. [Enter Notes here]
