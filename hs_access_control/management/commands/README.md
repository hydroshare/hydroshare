# Community editing management command

## Usage

First one must add an alias to make the commands work. **hsctl does not handle tokenized strings correctly and cannot be used to manage communities.** 

```
alias community='docker exec -it -u=hydro-service hydroshare python manage.py community'
```
After this, the `community` command has the following forms: 

* `community {c-name}`  # list what is known about a community 
* `community {c-name} create`  # create a community
* `community {c-name} update`  # update community metadata. 
* `community {c-name} remove`  # remove community record and all connections to groups. 
* Options for community updating commands include:  
    * `--owner={owner-username}`
    * `--description='{description}'`
    * `--purpose='{purpose}'`
* `community {c-name} group {g-name}`  # list what is known about a group member of a community.
* `community {c-name} group {g-name} add`  # add a group to a community 
* `community {c-name} group {g-name} update`  # update group connection metadata 
* `community {c-name} group {g-name} remove`  # remove a group to a community 
* Options for group commands include
    * `--owner={owner-username}`
    * `--prohibit_view`  # prohibit viewing of this group's resources by community. 
    * `--allow_edit`  # allow this group to edit resources of other groups in the community. 
* `community {c-name} owner {o-name} add`  # add an owner
* `community {c-name} owner {o-name} remove`  # remove an owner 

## Some important caveats: 

* **Group and community names need not be unique.**
* You can use either the name or numeric id for either groups or communities. 
* **You are required to use an id** when a name is not unique. 
* **All commands are idempotent.** Repeating a command has no effect. 
* **This does not protect against violating access control rules.** E.g., you must assure that: 
    * Every community has at least one owner. 

## Examples: 

* `community`  # lists communities 
* `community foo`  # lists community "foo"
* `community 5`    # lists community with id 5. 
* `community bar create --owner=alvacouch`  # create a community owned by alvacouch
* `community bar group cats add --owner=alvacouch`  # relate bar to cats with grantor alvacouch
