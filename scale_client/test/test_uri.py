import unittest

from scale_client.util import uri


class TestUri(unittest.TestCase):
    """
    Test Scale client URI system for properly formatting URIs, especially given incorrect input.

    FUTURE WORK will look at the URI registry system.
    """

    def test_default_uri(self):
        """test a local uri with defaults"""
        default_uri = uri.build_uri(relative_path='my/events')
        self.assertTrue('my/events' in default_uri, 'relative path missing!')
        self.assertTrue(uri.DEFAULT_SCALE_URI_NAMESPACE in default_uri, 'should have default namespace!')
        self.assertTrue(uri.DEFAULT_SCALE_URI_SCHEME in default_uri, 'should have default scheme!')
        has_ip = uri.parse_uri(default_uri).gethost()
        self.assertFalse(has_ip, 'default_uri should not have IP address!')

    def test_custom_local_uri(self):
        """test a local uri with custom fields"""
        custom_uri = uri.build_uri(namespace='custom', relative_path='path/to/stuff')
        self.assertTrue('/' + uri.DEFAULT_SCALE_URI_NAMESPACE not in custom_uri,
                        'custom uri should not contain default namespace: %s' % custom_uri)
        self.assertTrue('path/to/stuff' in custom_uri)

        custom_uri = uri.build_uri(namespace=None, relative_path='path/to/stuff')
        self.assertTrue('/' + uri.DEFAULT_SCALE_URI_NAMESPACE not in custom_uri,
                        'custom uri with no namespace should not contain default namespace: %s' % custom_uri)

        # Should generate an exception if we don't specify any path components!
        self.assertRaises(ValueError, uri.build_uri)

        # Absolute path overrides relative path!
        rel_path = 'relative/path/to/something'
        abs_path = 'absolute/path/to/nothing'
        custom_uri = uri.build_uri(path=abs_path, relative_path=rel_path)
        self.assertTrue(rel_path not in custom_uri, "Absolute path should override relative path: %s" % custom_uri)

        # Absolute path overrides namespace!
        namespace = 'anon/ns'
        abs_path = 'absolute/path/to/nothing'
        custom_uri = uri.build_uri(path=abs_path, namespace=namespace)
        self.assertTrue(rel_path not in custom_uri, "Absolute path should override namespace: %s" % custom_uri)

    def test_path_formatting(self):
        """test proper path formatting e.g. sanitization of input, especially for leading/trailing slashes"""

        # these should all build the same URI
        no_slash_uri = uri.build_uri(relative_path='path/to/stuff')
        leading_slashes_uri = uri.build_uri(relative_path='//path/to/stuff')
        trailing_slashes_uri = uri.build_uri(relative_path='path/to/stuff///')
        surrounding_slashes_uri = uri.build_uri(relative_path='/path/to/stuff/')

        self.assertEqual(no_slash_uri, leading_slashes_uri)
        self.assertEqual(trailing_slashes_uri, leading_slashes_uri)
        self.assertEqual(surrounding_slashes_uri, trailing_slashes_uri)
        self.assertEqual(no_slash_uri, surrounding_slashes_uri)

        self.assertTrue(uri.parse_uri(no_slash_uri).path.startswith('/'), "URI path must always start with /")
        self.assertFalse(uri.parse_uri(no_slash_uri).path.endswith('/'), "URI path must never end with /")

        # same tests but with absolute path and namespace
        no_slash_uri = uri.build_uri(path='path/to/stuff', namespace='custom/ns')
        leading_slashes_uri = uri.build_uri(path='//path/to/stuff', namespace='/custom/ns')
        trailing_slashes_uri = uri.build_uri(path='path/to/stuff///', namespace='custom/ns//')
        surrounding_slashes_uri = uri.build_uri(path='/path/to/stuff/', namespace='//custom/ns//')

        self.assertEqual(no_slash_uri, leading_slashes_uri)
        self.assertEqual(trailing_slashes_uri, leading_slashes_uri)
        self.assertEqual(surrounding_slashes_uri, trailing_slashes_uri)
        self.assertEqual(no_slash_uri, surrounding_slashes_uri)

        self.assertTrue(uri.parse_uri(no_slash_uri).path.startswith('/'), "URI path must always start with /")
        self.assertFalse(uri.parse_uri(no_slash_uri).path.endswith('/'), "URI path must never end with /")

        # verify we don't get double slashes in paths
        no_ns_uri = uri.build_uri(namespace='', relative_path='path/to/stuff')
        self.assertTrue('//' not in no_ns_uri, "double slash // present when requesting empty namespace!")


    # TODO: test_parse_uri

    def test_remote_uri(self):
        """
        Tests whether we can properly determine whether a SensedEvent came from our local node or not.
        :return:
        """
        local_path = 'my/uri/path'
        local_uri = uri.build_uri(path=local_path)
        # test some simple remote uri strings
        self.assertFalse(uri.is_remote_uri('my_uri'))
        self.assertFalse(uri.is_remote_uri(local_uri), "default URI isn't local!")
        self.assertTrue(uri.is_remote_uri('http://www.google.com'))
        self.assertFalse(uri.is_remote_uri('file:///home/my/stuff'))

        # test defaults
        remote_uri = uri.get_remote_uri('dummy_uri/blah')
        self.assertTrue(remote_uri.startswith(uri.DEFAULT_REMOTE_URI_PROTOCOL + '://'))
        self.assertTrue(':%d/' % uri.DEFAULT_REMOTE_URI_PORT in remote_uri)
        self.assertTrue('://%s' % uri.DEFAULT_REMOTE_URI_HOST in remote_uri)
        self.assertTrue(remote_uri.endswith('/dummy_uri/blah'))
        self.assertTrue(uri.is_remote_uri(remote_uri))

        # test custom
        remote_uri = uri.get_remote_uri(local_uri, protocol='mqtt', host='www.google.com', port=1884)
        self.assertEqual(remote_uri, 'mqtt://www.google.com:1884/%s' % local_path)
        self.assertTrue(uri.is_remote_uri(remote_uri))


if __name__ == '__main__':
    unittest.main()