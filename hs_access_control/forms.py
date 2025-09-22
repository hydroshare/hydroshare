from django import forms
from sorl.thumbnail import ImageField as ThumbnailImageField, get_thumbnail


class CommunityForm(forms.Form):
    """A form to validate data for a community"""
    name = forms.CharField(required=True)
    description = forms.CharField(required=True)
    purpose = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    url = forms.URLField(required=False)
    picture = ThumbnailImageField()
    banner = ThumbnailImageField()
    auto_approve_resource = forms.BooleanField(required=False)
    auto_approve_group = forms.BooleanField(required=False)

    def update_image_fields(self, community, request):
        """sets the picture and banner image fields of the community record"""

        # set the picture field of the community
        if 'picture' in request.FILES:
            # resize uploaded logo image
            img = request.FILES['picture']
            img.image = get_thumbnail(img, 'x150', crop='center')
            community.picture = img
            community.save()

        # set the banner field of the community
        if 'banner' in request.FILES:
            # resize uploaded banner image
            img = request.FILES['banner']
            img.image = get_thumbnail(img, '1200x200', crop='center')
            community.banner = img
            community.save()


class RequestNewCommunityForm(CommunityForm):
    """A form to validate data for RequestCommunity record and create this record"""

    def save(self, request):
        form_data = self.cleaned_data

        new_community_request = request.user.uaccess.create_community_request(
            title=form_data['name'],
            description=form_data['description'],
            purpose=form_data['purpose'],
            auto_approve_resource=form_data['auto_approve_resource'],
            auto_approve_group=form_data['auto_approve_group'],
            email=form_data['email'],
            url=form_data['url'])

        self.update_image_fields(community=new_community_request.community_to_approve, request=request)
        return new_community_request


class UpdateCommunityForm(CommunityForm):
    """A form to update data for a Community record and update that record"""

    def update(self, community, request):
        form_data = self.cleaned_data

        community = request.user.uaccess.update_community(
            this_community=community,
            title=form_data['name'],
            description=form_data['description'],
            purpose=form_data['purpose'],
            auto_approve_resource=form_data['auto_approve_resource'],
            auto_approve_group=form_data['auto_approve_group'],
            email=form_data['email'],
            url=form_data['url']
        )

        self.update_image_fields(community=community, request=request)
        return community
