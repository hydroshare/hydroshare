from django.db import models


class Topic(models.Model):
    name = models.CharField(editable=True, null=False, max_length=255)

    # order = models.IntegerField(null=False,
    #                             default=0,
    #                             editable=True,
    #                             help_text='Position of this entry: 1-n')

    def __str__(self):
        return "{}".format(self.name)

    @classmethod
    def add(cls, new_topic):
        """
        Add a new topic

        :param new_topic: string topic to be added
        :return:
        """
        topic = cls()
        topic.name = new_topic
        # topics_list = Topic.objects.all.values_list("order", flat=True)
        # topic.order = max(topics_list if topics_list else [0]) + 1

        topic.save()
