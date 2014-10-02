from mezzanine.pages.models import Page
from django.core import exceptions as ex

class PagePermissionsViewableMiddleware(object):
    """If a page implements "can_view(request)" we honor the permission and
    raise a 403 if the logged in user would normally not be able to view the
    content"""

    def process_request(self, request):
        slug = request.path
        if slug != '/':
            slug = slug.strip('/')
        if slug == '':
            return None
        page_or_none = Page.objects.filter(slug=slug)
        if page_or_none.exists():
            page = page_or_none[0]
            try:
                content = page.get_content_model()
                if hasattr(content, 'can_view'):
                    if content.can_view(request):
                        return None
                    else:
                        raise ex.PermissionDenied('User does not have permission to view')
            except AttributeError:
                return None
            except KeyError:
                return None

