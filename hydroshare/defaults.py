# make the DEBUG setting available to templates in hydroshare

from mezzanine.conf import register_setting

register_setting(
    name="TEMPLATE_ACCESSIBLE_SETTINGS",
    description=("Sequence of setting names available within templates."),
    editable=True,
    default=("DEBUG",),
    append=True,
)
