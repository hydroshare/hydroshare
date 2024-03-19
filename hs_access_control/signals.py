import django.dispatch

access_changed = django.dispatch.Signal(providing_args=['users', 'resources'])
