from django.db import models


class Topic(models.Model):
    name = models.CharField(editable=True, null=False, max_length=255)


class TopicEntry(models.Model):
    topic = models.ForeignKey(Topic,
                              null=False,
                              editable=True,
                              help_text='One topic entry for a resource')
    order = models.IntegerField(null=False,
                                editable=True,
                                help_text='Position of this entry: 1-n')


class Topics(models.Model):
    topics = models.ManyToManyField(TopicEntry,
                                    editable=True,
                                    help_text='A list of topics, in order')
    def add(self, topic):
        """

        :param topic:
        :return:
        """
        t = TopicEntry()
        t.topic = topic
        l = self.topics.values_list("order", flat=True)
        t.order = max(l if l else [0]) + 1  # TODO comment for Scott

        t.save()
