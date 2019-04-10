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
  * hydroshare/local_settings.py
  * hydroshare/settings.py
  * nginx/config-files/hydroshare-ssl-nginx.conf.template
  * scripts/templates/docker-compose.template
- [ ] Deployed to Beta
- [ ] check_resource beta results match current www results
- [ ] Review the search and discovery pages
- [ ] Create a new user and update profile
- [ ] Create iROD account, test connection and delete iROD account
- [ ] Create a new resource, check sharing/permission settings, delete new resource
- [ ] Developers test around issues
- [ ] QA testing around issues
- [ ] Stakeholders approval

<!-- Update the checklist as items are completed -->
### Production Deployment
- [ ] Deployed to Production
  * Make manual changes to files identified in Beta Deployment
- [ ] Maps API key is correct and maps are displaying correctly
- [ ] check_resource www results match pre-deployment www results
- [ ] Review the search and discovery pages
- [ ] Create a new user and update profile
- [ ] Create iROD account, test connection and delete iROD account
- [ ] Create a new resource, check sharing/permission settings, delete new resource
- [ ] Developers test around issue

### Notes relevant to deployment
1. [Enter Notes here]
