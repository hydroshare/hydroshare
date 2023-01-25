
# Access Control Tests
### Tests cases to check proper implementation of Hydroshare access control policies.

## Overview

Users: `Admin, Test`
- `Admin` is actually an admin, i.e. superuser
- `Test` is an arbitrary non-superuser user

Future users:
- `FakeAdmin` is a normal user whose username is 'admin'

Resources Types: `COMPOSITE`
- we use only composite resources for now to limit the manual labor

Permissions: `NONE, VIEW, EDIT, OWN`
- `VIEW` allows another user READONLY access
- `EDIT` lets another user make changes to the content/metadata
- `OWN` lets another user delete the resource

Actions:
1. `VIEW` resource page
2. `VIEW` edit button
3. `VIEW` edit page (load page in edit_mode)
4. `COMMIT EDITS` in the edit page
5. `VIEW` delete button
6. `DELETE` resource

For each pair of (permissions X actions) we evaluate whether a user with the
given permissions can perform the given action.

We also consider the case of a user whose username is 'Admin'. 

## Test Results

#### with NO permissions:

Test & Admin:
1. NO
2. N/A
3. N/A
4. N/A
5. N/A
6. N/A

-- as expected: cant see, so cant do anything. access denied w/ 403 Forbidden.
		Error should probably be 'Unknown Resource' to not divulge the
		existence of the resource

#### with VIEW permissions:

Test & Admin:
1. YES 
2. NO
3. N/A
4. N/A
5. NO
6. N/A

-- as expected: can see resource, but cant see edit buttons so cant (easily)
		load edit page or delete the resource

-- NB: injecting a form to load the page in edit mode results in the edit page
	loading, but saving changes results in a 500 (internal server error)

#### with EDIT permissions:

Test & Admin:
1. YES
2. YES
3. YES
4. YES
5. NO
6. N/A

-- as expected: can view & edit, but cant see delete button

#### with OWN permissions:

Test & Admin:
1. YES 
2. YES
3. YES
4. YES
5. YES
6. YES

-- as expected: can view, edit, and delete

## Conclusions

* Permissions:
The existing implementation of the permissions model works mostly as expected.
I could not get it to commit the ultimate failure of letting a user mutate a 
resource without adequate permissions. However, the user (with some form 
trickery) can view pages they should not, even if they cannot make any changes
once there. 

Specific changes:
1. Server should respond with a 404 when asking for a resource that the user
does not have permission to see, so as not to leak info about the existence
of the resource
2. Server should not respond with a 500 when a user attempts to save changes
they are not authorized to make. Instead, send a 403 (forbidden) or 404. 

* Admin Username:
Usernames must be unique, so as long as the DB comes configured with a user
with username = 'admin', then normal users will not be able to create a user
that can masquerade as the superuser. However, this is pretty flimsy, and 
reimplementing access control such that it does not manually inspect the 
username would be more robust.

* Changing Ownership
The existing implementation compares the user making the request to the user
who created the resource, and if equal grants access. However, while this seems
to lead to a security hole wherein the creator could lose access to a resource
but still be listed as the creator does not occur. In testing, trying to view
a resource which the user had originally created but then been removed from
ownership resulted in a 403, which makes sense.
