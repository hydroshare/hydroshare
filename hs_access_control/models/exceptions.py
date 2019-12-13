#############################################
# exceptions
#
# These are used by all access control classes.
#############################################


class PolymorphismError(Exception):
    """ A function is called with an inappropriate combination of arguments """
    # This is a generic exception.
    pass
