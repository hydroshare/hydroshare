from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models

from hs_core.models import BaseResource

PUBLICATION_STATUSES = [
    ('pending', 'Pending Approval'),
    ('approved', 'Publication Approved'),
    ('denied', 'Publication Request Denied')
]


class PublicationQueue(models.Model):
    resource = models.ForeignKey(BaseResource)
    status = models.CharField(max_length=8, choices=PUBLICATION_STATUSES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    note = models.TextField(blank=True, null=False)

    def save(self, *args, **kwargs):
        if self.pk:
            send_mail(
                'Your resource publication',
                'Your resource publication status has changed to: {}\n\n' +
                'Explanation:\n{}'.format(self.status, self.note),
                'publication@cuahsi.org',
                [self.resource.user.email],
                fail_silently=False,
            )
        super(PublicationQueue, self).save(*args, **kwargs)

    def __str__(self):
        return self.resource.metadata.title.value

    class Meta:
        verbose_name = "Publication Queue Item"
        verbose_name_plural = "Publication Queue Items"