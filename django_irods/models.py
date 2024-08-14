from django.db import models as m

class AVU(m.Model):
    name = m.TextField()
    attName = m.TextField()
    attVal = m.TextField()

    class Meta:
        verbose_name = 'AVU'
        constraints = [
            m.UniqueConstraint(fields=['name', 'attName'], name='unique_avu')
        ]
