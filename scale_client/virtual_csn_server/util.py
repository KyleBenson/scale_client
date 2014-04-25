# coding=utf-8

"""
Util module for route management and date handling.

"""

import datetime

# Parses ISO format, with or without microseconds.
DATETIME_FMT = '%Y-%m-%dT%H:%M:%S.%f'
URL_DATE_FORMAT = '%Y-%m-%dT%H-%M-%S.%f'
# ISO order, but without separators ([:.] not allowed by taskqueue).
JOB_DATE_FORMAT = '%Y%m%d%H%M%S%f'


def date_format(datetime_obj, url_format=False):
    """
    Put date in expected ISO serialized format without microseconds.

    Parameters
    ----------
    datetime_obj : datetime.datetime
        The date to format into `DATETIME_FMT` format.

    Returns
    -------
    datetime_str : string
        The `string` version of the provided `datetime` object.

    Notes
    -----
    Both date functions belong in a utility class, but creating one for just
    these two functions is a bit much. They can live in `base_handler` for now.

    Examples
    --------
    >>> util.date_format(datetime.datetime.utcnow())
    '2013-02-26T19:50:43.912'

    """
    if url_format:
        return datetime_obj.strftime(URL_DATE_FORMAT)[:-3]
    else:
        # Using .isoformat() strips the fractional seconds if there are none.
        return datetime_obj.strftime(DATETIME_FMT)[:-3]


def parse_date(datetime_str, url_format=False):
    """
    Return `datetime` object from expected ISO serialized format.

    Parameters
    ----------
    datetime_str : string
        The ISO formatted date to convert back to a `datetime` object.

    Returns
    -------
    datetime_obj : datetime.datetime
        The `datetime` object represented by the provided `string`.

    Examples
    --------
    >>> util.parse_date('2013-02-26T19:50:43.912')
    datetime.datetime(2013, 2, 26, 19, 50, 43, 912000)

    """
    try:
        if url_format:
            return datetime.datetime.strptime(datetime_str, URL_DATE_FORMAT)
        else:
            return datetime.datetime.strptime(datetime_str, DATETIME_FMT)
    except ValueError:
        raise InvalidRequest(
            'Datetime object "{}" was not parseable.'.format(datetime_str))


def modify_cache(memcache_key, modifier, gen_entity=None,
                 entity=None, memcache_client=None, limit=100):
    """
    Update memcache using a modifier function.

    Parameters
    ----------
    memcache_key : string
        Key to request from memcache.
    modifier : function
        Takes in the cached value and returns the modified value to be stored.
    gen_entity : tuple of function, args
        A function and the arguments necessary to generate an entity to
        populate the cache with.
    entity : entity, optional
        An up-to-date entity of the type we are trying to update the cached
        value of. If the value is not cached, we will set this as the cached
        value.
    memcache_client : google.appengine.ext.memcache.Client
        Memcache Client to use for performing compare-and-set operation.
    limit : int
        A limit on the number of CAS attempts to make. Defaults to 100, which
        is effectively no limit.

    """
    if not memcache_client:
        memcache_client = memcache.Client()
    try:
        for _ in xrange(limit):
            cached_value = memcache_client.gets(memcache_key)
            if cached_value is not None:
                modified = modifier(cached_value)
                if memcache_client.cas(memcache_key, modified):
                    return modified
            elif entity:
                if memcache_client.add(memcache_key, entity):
                    return entity
            elif gen_entity:
                get_entity_fn, arg = gen_entity
                stale_entity = get_entity_fn(arg)
                modified = modifier(stale_entity)
                if memcache_client.add(memcache_key, modifier(stale_entity)):
                    return modified
            else:
                return False
    except NoModificationNecessary:
        pass
    return False


def add_to_cache(memcache_key, entity, limit=100):
    """
    Cache a given entity in memcache.

    Parameters
    ----------
    memcache_key : string
        Key to request from memcache.
    modifier : function
        Takes in the cached value and operates on it.
    entity : entity, optional
        An up-to-date entity of the type we are trying to update the cached
        value of. If the value is not cached, we will set this as the cached
        value.
    memcache_client : google.appengine.ext.memcache.Client
        Memcache Client to use for performing compare-and-set operation.
    limit : int
        A limit on the number of CAS attempts to make. Defaults to 100, which
        is effectively no limit.

    Returns
    -------
    cached_value : entity
        If the value is found in the cache, it is returned. Otherwise, the
        value is set and None is returned.

    """
    for _ in xrange(limit):
        if memcache.add(memcache_key, entity):
            return None
        cached_value = memcache.get(memcache_key)
        if cached_value:
            return cached_value
    return None


def system_time():
    return datetime.datetime.utcnow()


def uri_for(name, **kwargs):
    """Alias for handler.uri_for when handler object is not available."""
    if not 'namespace' in kwargs:
        kwargs['namespace'] = namespace_manager.get_namespace()
    return main.base_app.router.build(None, name, [], kwargs)


class InvalidRequest(Exception):
    pass


class NoModificationNecessary(Exception):
    pass
