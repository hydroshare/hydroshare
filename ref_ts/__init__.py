
class ReftsException(Exception):
    def __init__(self, args):
        super(ReftsException, self).__init__(args)
        self.msg = args[0]

    def __str__(self):
        msg = "Refts Error: {0} ."
        return msg.format(self.msg)

    def __unicode__(self):
        return unicode(str(self))