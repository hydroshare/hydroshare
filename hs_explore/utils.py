
class Utils(object):
    """
    Features appropriate for machine learning analysis of our databases.
    """

    @staticmethod
    def write_dict(filename, some_dict):
        target = open(filename, 'a')
        # s = ""
        # for user_resource, val in user_resource_dict.iteritems():
        #     s = user_resource[0] + " " + user_resource[1] + " " + str(val) + "\n"
        #     print s
        target.write(str(some_dict))