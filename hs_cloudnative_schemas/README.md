# HydroShare-Cloud-Native-Data
Exploration of cloud native data storage for HydroShare.




## Connecting to Kubernetes Deployment

```
project-id = apps-320517
cluster-id = hydroshare-workflows
```

Make sure that you're connected to the correct project:

`gcloud projects list`

`gcloud config set project PROJECT ID`

Connect to the correct cluster: 

`gcloud container clusters list`

`gcloud container clusters get-credentials --zone <LOCATION> <NAME>`

List all contexts, you should see the cluster specified in the command above

`kubectl config get-contexts`

Attach to this context

`kubectl config set current-context MY-CONTEXT`

