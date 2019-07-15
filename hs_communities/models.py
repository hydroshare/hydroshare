from django.db import models


class Topic(models.Model):
    name = models.CharField(editable=True, null=False, max_length=255)

    def __str__(self):
        return "{}".format(self.name)


class TopicEntry(models.Model):
    topic = models.ForeignKey(Topic,
                              null=False,
                              editable=True,
                              help_text='One topic entry for a resource')
    order = models.IntegerField(null=False,
                                editable=True,
                                help_text='Position of this entry: 1-n')

    def __str__(self):
        return "{} {}".format(self.topic, self.order)


class Topics(models.Model):
    topics = models.ManyToManyField(TopicEntry,
                                    editable=True,
                                    help_text='A list of topics, in order')

    def add(self, new_topic):
        """

        :param topic:
        :return:
        """
        topic_entry = TopicEntry()
        topic_entry.topic = new_topic
        topics_list = self.topics.values_list("order", flat=True)
        topic_entry.order = max(topics_list if topics_list else [0]) + 1

        topic_entry.save()

    # def delete(self, id):
    #     """
    #
    #     :param id:
    #     :return:
    #     """
    #     print("would delete topic id {}".format(id))

    def __str__(self):
        return "{}".format(self.topics)
