import math


def unique(series):
    return series.unique().size == series.size


def some_null(series):
    return series.count() < series.size


def all_null(series):
    return series.count() == 0

def mostly_null(series):
    return series.count() < series.size / 2

def not_null(series):
    return series.count() == series.size


def categorical(series):
    return series.unique().size < math.sqrt(series.size)


def continuous(series):
    return series.dtype.name != 'object' and not categorical(series)


def uniform(series):
    return series.unique().size == 1