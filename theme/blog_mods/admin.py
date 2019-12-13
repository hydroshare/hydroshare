
from copy import deepcopy

from mezzanine.blog.admin import BlogPostAdmin
from mezzanine.conf import settings


if settings.BLOG_USE_FEATURED_IMAGE:
    # monkey patch featured_video onto BlogPost
    custom_blog_fieldsets = deepcopy(BlogPostAdmin.fieldsets)
    custom_blog_fieldsets[0][1]["fields"].insert(-2, "featured_video")

    BlogPostAdmin.fieldsets = custom_blog_fieldsets
