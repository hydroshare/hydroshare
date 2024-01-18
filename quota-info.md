# HydroShare Quota Notes #

<!-- TODO 5228 -->

Although back-end code implementation for HydroShare quota management is included in the HydroShare code base and will make its way into next production deployment, front-end quota notification messaging and email notification languages may need some tweaks to better notify users about their quota situation and the actions they need to take. As a result, we need to turn quota front-end notification messaging off until the languages are approved by the team. The following lines in the code base need to be commented out in order to turn the quota front-end notification messaging off, and uncommented to turn the quota front-end notification messaging back on. Specifically, to turn off the quota front-end notification messaging, follow the steps below:

- Comment out the line as shown in https://github.com/hydroshare/hydroshare/blob/develop/theme/templates/accounts/profile.html#L357 by enclosing the line ```<div class="text-muted">{{ quota_message }}</div>``` with ```{#``` and ```#}```.
- Comment out the three lines as shown in https://github.com/hydroshare/hydroshare/blob/develop/theme/views.py#L309-L311 so they look like the following:
```
# add_msg = get_quota_message(authenticated_user)
# if add_msg:
#    login_msg += add_msg
```  
- Comment out the lines as shown in https://github.com/hydroshare/hydroshare/blob/develop/theme/management/commands/update_used_storage.py#L85..L94 so they look like the following:
```
# user = uq.user
# uemail = user.email
# msg_str = 'Dear ' + uname + ':\n\n'
# msg_str += get_quota_message(user)

# msg_str += '\n\nHydroShare Support'
# subject = 'Quota warning'
# # send email for people monitoring and follow-up as needed
# send_mail(subject, msg_str, settings.DEFAULT_FROM_EMAIL,
#           [uemail])
```

To turn on the front-end quota notification messaging and quota warning email notification, simply uncomment the code snippets above.

Note that quota enforcement does take effect even though the front-end quota notification is turned off. If the nightly run script is not wired in, every user's usage is zero which would never run above the allocated quota. However, if the nightly run script is indeed wired in, the quota enforcement will take effect, in which case, it'd be better to turn on front-end quota notification messaging and emails.