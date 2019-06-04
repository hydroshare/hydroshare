from django.db import models

class model1(models.Model):
    field1 = models.charField(max_length=255)
    field2 = models.charfield(max_length=255)
    field3 = models.charfield(max_length=255)

class model2(models.Model):
    fields1 = models.charField(max_length=255)
    fields2 = models.charField(max_length=255)
    fields3 = models.charField(max_length=255)


class model3(models.Model):
    fields12 = models.charField(max_length=255)
    fields22 = models.charField(max_length=255)
    fields32 = models.charField(max_length=255)

