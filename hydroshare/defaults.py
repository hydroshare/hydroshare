from ConfigParser import SafeConfigParser

from mezzanine.conf import register_setting

def append_setting(key, value):
    register_setting(
        name="TEMPLATE_ACCESSIBLE_SETTINGS",
        editable=False,
        default=(key,),
        append=True,
    )


    register_setting(
        name=key,
        editable=False,
        default=value,
    )

    return

config = SafeConfigParser()
config.read('hydroshare/customize.cfg')

for section in config.sections():
    for key, value in config.items(section):
        append_setting(key.upper(),value)

