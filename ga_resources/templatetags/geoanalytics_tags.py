from django.contrib.auth import REDIRECT_FIELD_NAME
from django.db.models import Model
from mezzanine import template
from django.template import Node
from django.core.exceptions import ImproperlyConfigured
from lxml import etree
from mezzanine.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

# _page_mapping = importlib.import_module(settings.SUBPAGE_MAPPING_MODULE)
from mezzanine.core.fields import RichTextField
from mezzanine.core.forms import get_edit_form


def is_editable(obj, request):
    """
    Returns ``True`` if the object is editable for the request. First
    check for a custom ``editable`` handler on the object, otherwise
    use the logged in user and check change permissions for the
    object's model.
    """
    return obj.can_change(request)

#    if hasattr(obj, "is_editable"):
#        return obj.is_editable(request)
#    else:
#        perm = obj._meta.app_label + "." + obj._meta.get_change_permission()
#        return obj.can_change(request)





_pages = {

}

_contenttypes = {
    'catalogpage' : [
        ("Catalog Page", "ga_resources.models", "CatalogPage"),
        ("Data Resource", "ga_resources.models", "DataResource"),
        ("Styled Map", "ga_resources.models", "RenderedLayer"),
        ("Style", "ga_resources.models", "Style")
    ],
    'dataresource' : [
        ("Page", "mezzanine.pages.models", "RichTextPage"),
        ("Styled Map", "ga_resources.models", "RenderedLayer"),
        ("Style", "ga_resources.models", "Style"),
    ]
}

register = template.Library()

class SubpageNode(Node):
    def render(self, context):
        page = context['page']
        if page.slug in _pages:
            div = etree.Element('div', attrib={'class' : 'btn-group'})
            a = etree.SubElement(div, 'a', attrib={
                'href' : '#',
                'data-toggle' : 'dropdown',
                'class' : 'btn dropdown-toggle'
            })
            a.append(etree.Element("span", attrib={'class': 'caret'}))
            a.text = 'Create new '
            ul = etree.SubElement(div, 'ul', attrib={
                "class" : "dropdown-menu"
            })
            for title, package, model in _pages[page.slug]:
                li = etree.SubElement(ul, "li")
                a = etree.SubElement(li, 'a', attrib={
                    'href' : '/ga_resources/createpage/?module={module}&classname={classname}&parent={slug}'.format(
                        module=package,
                        classname=model,
                        slug=page.slug)
                })
                a.text = title

        elif page.content_model in _contenttypes:
            div = etree.Element('div', attrib={'class' : 'btn-group'})
            a = etree.SubElement(div, 'button', attrib={
                #'href': '#',
                'data-toggle': 'dropdown',
                'class': 'btn dropdown-toggle'
            })
            a.text = 'Create new '
            a.append(etree.Element("span", attrib={'class' : 'caret'}))
            ul = etree.SubElement(div, 'ul', attrib={
                "class": "dropdown-menu"
            })
            for title, package, model in _contenttypes[page.content_model]:
                li = etree.SubElement(ul, "li")
                a = etree.SubElement(li, 'a', attrib={
                    'href': '/ga_resources/createpage/?module={module}&classname={classname}&parent={slug}'.format(
                        module=package,
                        classname=model,
                        slug=page.slug)
                })
                a.text = title
        else:
            return ""

        print etree.tostring(div, pretty_print=True)
        return etree.tostring(div, pretty_print=True)


@register.tag("subpage_button")
def do_add_subpage(parser, token):
    return SubpageNode()


@register.render_tag
def set_ppm_permissions(context, token):
    """
    Assigns a permissions dict to the given page instance, combining
    Django's permission for the page's model and a permission check
    against the instance itself calling the page's ``can_add``,
    ``can_change`` and ``can_delete`` custom methods.

    Used within the change list for pages, to implement permission
    checks for the navigation tree.
    """

    page = context[token.split_contents()[1]]
    model = page.get_content_model()

    try:
        opts = model._meta
    except AttributeError:
        if model is None:
            error = _("Could not load the model for the following page, "
                      "was it removed?")
            obj = page
        else:
            # A missing inner Meta class usually means the Page model
            # hasn't been directly subclassed.
            error = _("An error occured with the following class. Does "
                      "it subclass Page directly?")
            obj = model.__class__.__name__
        raise ImproperlyConfigured(error + " '%s'" % obj)
    perm_name = opts.app_label + ".%s_" + opts.object_name.lower()
    request = context["request"]
    setattr(page, "perms", {})
    for perm_type in ("add", "change", "delete"):
        perm = request.user.has_perm(perm_name % perm_type)
        perm = perm or getattr(model, "can_%s" % perm_type)(request)
        page.perms[perm_type] = perm
    return ""


@register.inclusion_tag("includes/editable_loader.html", takes_context=True)
def ga_editable_loader(context):
    """
    Set up the required JS/CSS for the in-line editing toolbar and controls.
    """
    user = context["request"].user
    page = context['page']
    permission = page.can_change(context['request'])
    context["has_site_permission"] = permission #  has_site_permission(user)
    if settings.INLINE_EDITING_ENABLED and permission:
        t = get_template("includes/ga_editable_toolbar.html")
        context["REDIRECT_FIELD_NAME"] = REDIRECT_FIELD_NAME
        context["toolbar"] = t.render(Context(context))
        context["richtext_media"] = RichTextField().formfield().widget.media
    return context


@register.to_end_tag
def ga_editable(parsed, context, token):
    """
    Add the required HTML to the parsed content for in-line editing,
    such as the icon and edit form if the object is deemed to be
    editable - either it has an ``editable`` method which returns
    ``True``, or the logged in user has change permissions for the
    model.
    """

    def parse_field(field):
        field = field.split(".")
        obj = context.get(field.pop(0), None)
        attr = field.pop()
        while field:
            obj = getattr(obj, field.pop(0))
        return obj, attr

    fields = [parse_field(f) for f in token.split_contents()[1:]]
    if fields:
        fields = [f for f in fields if len(f) == 2 and f[0] is fields[0][0]]
    if not parsed.strip():
        try:
            parsed = "".join([str(getattr(*field)) for field in fields])
        except AttributeError:
            pass

    if settings.INLINE_EDITING_ENABLED and fields and "request" in context:
        obj = fields[0][0]
        if isinstance(obj, Model) and is_editable(obj, context["request"]):
            field_names = ",".join([f[1] for f in fields])
            context["editable_form"] = get_edit_form(obj, field_names)
            context["original"] = parsed
            t = get_template("includes/ga_editable_form.html")
            return t.render(Context(context))
    return parsed