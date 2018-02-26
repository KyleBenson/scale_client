"""
Various (often hacky) code snippets used across multiple classes.
"""


def _get_class_by_name(kls):
    """Imports and returns a class reference for the full module name specified in regular Python import format"""

    # The following code taken from http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m