## Rules for managing usernames and email addresses in xDCIShare 

###1.	Purpose
1.1.	Usernames are used by xDCIShare for users to identify themselves at sign in.  They should in general not be displayed or used as identifiers anywhere else in the system.  A user may use their email address as their username, but they do not have to.

1.2.	Email addresses are used by xDCIShare to uniquely identify users and validate who they are, going by the premise that the identity of person behind an email account is sufficiently verifiable for xDCIShare.  When resources in xDCIShare are shared, it really means that they are shared with users who have gained entry to the system with this email address.  

1.3.	To achieve the above purposes both username and email address should be associated with only one xDCIShare account.
###2.	Usernames
2.1.	Each user account should have a separate and unique username that they specify at the time of account creation.  

2.2.	In the case that a user requests a username that exists in the system generate a message that the username is already taken and that they need to request another username.  

2.3.	A user may change their username using their profile page.  If when changing a username a user requests a username that exists in the system generate a message that the username is already taken and that they need to request another username 
###3.	Email addresses
3.1.	Each user account should have a separate and unique email address that they specify at the time of account creation.

3.2.	In the case that a user requests to create an account and an account already exists that uses that email address the user is informed that an account with that email address exists.  This message should provide links to retrieve forgotten username and password.

3.3.	Email addresses should be validated by an email being sent to the user and the user being required to click on a link in the email.  An account should not be created until the email address has been validated (Technically this may mean that there is an account that exists but is activated by the clicking).  A time limit should be set for a user to click on the link and validate the email.  This time limit should be adjustable by a xDCIShare system administrator via a system administrator interface.  The initial value of this time limit should be 24 hours and conveyed to the user in the email and in the request account landing page.

3.4.	If the user does not validate the account within the time limit any temporary information retained in the system about creating their account should be deleted.

3.5.	If a user attempts to create an account with an email address for which a validation is pending the user should receive a message that indicates that creation of this account is pending validation of the email address.  This message should suggest the user look in their junk mail in case the validation email is there.  This message should provide a button for the validation email to be resent.  

3.6.	A user may change their email address using their profile page.  If when changing an email address the user requests an email address that exists in the system generate a message that an account with that email address already exists.  This message should provide links to retrieve forgotten username and password.

3.7.	The request to change an email should generate validation emails sent to both the new and the old email address.

3.8.	The email change validation email sent to the new email address should include a link for the user to click on to validate the new email address.  Changes in the email address should only be enacted when this is clicked.  This validation should be active for the same time limit as validation of account creation email.

3.9.	The email change validation sent to the old email address should indicate that a user (probably you) have requested to change the email address for your xDCIShare account to <give new email address>.  If this is correct no action is needed.  If this is incorrect (which may mean someone is tampering with the account without your permission) provide a link to click on and revoke the email change.  This link to revoke the email change is intended to reduce the chance that someone can hijack a xDCIShare account and should never expire.  So while an email change in the profile is made as soon as the new email account is verified, information needs to be retained so that this may be rolled back if the link to revoke the change is ever clicked.  
###4.	Privacy
4.1.	Email addresses in xDCIShare are not private.  They are used for disambiguation in the identification of users when sharing resources and inviting users to groups.  

4.2.	xDCIShare should not publish email addresses on user profiles as this provides a way for spammers to discover emails.  Rather a button should be provided on the public user page "Send message" that allows a user to type a message to another user that xDCIShare will then send to the user.  The from and reply to field in this email should have the email address of the originating user.

