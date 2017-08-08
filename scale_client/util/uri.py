# This file intended to hold various helper functions, constants, and eventually a
# registration system for URIs within the scale client.

import uritools


# NOTE: underscores not allowed in scheme!
DEFAULT_SCALE_URI_SCHEME = 'scale-local'
# we somewhat support the idea of namespaces so that someone could manage URIs for their own purposes
# without interfering in the core scale client URI namespace
DEFAULT_SCALE_URI_NAMESPACE = 'scale'
DEFAULT_SCALE_URI_PATH_BASE = DEFAULT_SCALE_URI_NAMESPACE


def build_uri(scheme=DEFAULT_SCALE_URI_SCHEME, namespace=DEFAULT_SCALE_URI_NAMESPACE,
              path=None, relative_path=None, **kwargs):
    """
    Build a URI from the specified parameters.  If you don't specify path to create a complete path,
     you can specify a relative path to have it build one for you on top of the optionally-specified
    namespace that helps avoid collision with core scale client URIs.

    NOTE: these parameters are just for conventional purposes and don't do any significant
     namespace separation, management, or API exposure currently...

    :param scheme: first part of the URI identifying the protocol/scheme/etc. (default is scale-specific for local use)
    :param namespace: the scale core may handle the different namespaces separately
    :param path: an absolute URI path (will skip over the relative one)
    :param relative_path: e.g. your/path/goes/here but note that you are responsible for managing this path hierarchy!
    :param kwargs: all these are passed to uritools.uricompose
    :return:
    """

    # First build up the path we'll use
    # TODO: test all of this!
    parts_to_use = [namespace]

    if path is None and relative_path is None:
        raise ValueError("must specify at least a component path (can be a simple name string) or ")
    elif path is None and relative_path is not None:
        parts_to_use.append(relative_path)
    else:
        parts_to_use.append(path)

    # First, trim any leading/trailing slashes
    final_parts = []
    for part in parts_to_use:
        while part.startswith('/'):
            part = part[1:]
        while part.endswith('/'):
            part = part[:-1]
        final_parts.append(part)
    # Note that we enforce a leading / for the path!
    path = '/' + '/'.join(final_parts)

    return uritools.uricompose(scheme=scheme, path=path, **kwargs)

# TODO: get_namespace_from_path

def parse_uri(uri):
    """
    Returns a parsed object for the given URI that you can further extract info from:
    gethost, getpath, getport, getquerydict, etc.
    :param uri:
    :return:
    """
    return uritools.urisplit(uri)
