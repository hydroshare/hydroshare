
# Access Control Tests
### Tests cases to check proper implementation of Hydroshare access control policies.

## Overview

Users: Admin, Test
	- Admin is actually an admin, i.e. superuser
	- Test is an arbitrary non-superuser user

Future users:
	- FakeAdmin is a normal user whose username is 'admin'

Resources Types: GENERIC
	- we use only generic resources for now to limit the manual labor

Permissions: NONE, VIEW, EDIT, OWN
	- VIEW allows another user READONLY access
	- EDIT lets another user make changes to the content/metadata
	- OWN lets another user delete the resource

Actions:
	1. VIEW resource page

	2. VIEW edit button
	3. VIEW edit page (load page in edit_mode)
	4. COMMIT EDITS in the edit page

	5. VIEW delete button
	6. DELETE resource

For each pair of (permissions X actions) we evaluate whether a user with the
given permissions can perform the given action. 

## Test Results

======================
with NO permissions:
===========
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

======================
with VIEW permissions:
===========

Test & Admin:
1. YES 
2. NO
3. N/A
4. N/A
5. NO
6. N/A

-- as expected: can see resource, but cant see edit buttons so cant (easily) load 
		edit page or delete the resource

-- NB: injecting a form to load the page in edit mode results in the edit page
	loading, but saving changes results in a 500 (internal server error)

======================
with EDIT permissions:
===========

Test & Admin:
1. YES
2. YES
3. YES
4. YES
5. NO
6. N/A

-- as expected: can view & edit, but cant see delete button

======================
with OWN permissions:
===========

Test & Admin:
1. YES 
2. YES
3. YES
4. YES
5. YES
6. YES

-- as expected: can view, edit, and delete

