import json
import logging
import os
import random
import time
import unittest

import novaclient.exceptions as nova_exceptions

from openstack_plugin_common import (
    API_CALL_ATTEMPTS,
    ExceptionRetryProxy,
    _nova_exception_handler
)

RETRY_AFTER = 1
# Time during which no retry could possibly happen.
NO_POSSIBLE_RETRY_TIME = RETRY_AFTER / 2.0

PROVIDER_CONTEXTS_WITHOUT_PREFIX = (
    {},
    {
        'cloudify': {

        }
    },
    {
        'cloudify': {
            'resources_prefix': ''
        }
    },
    {
        'cloudify': {
            'resources_prefix': None
        }
    },
)


def set_mock_provider_context(ctx, provider_context):
    def mock_provider_context(provider_name_unused):
        return provider_context
    ctx.get_provider_context = mock_provider_context


def set_mock_provider_context_from_file(ctx, file_name=None):
    file_name = file_name or 'provider-context'
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    full_file_name = os.path.join(cur_dir, file_name) + '.json'
    with open(full_file_name) as f:
        provider_context = json.loads(f.read())['context']
    set_mock_provider_context(ctx, provider_context)


class ExceptionRetryProxyTestCase(unittest.TestCase):

    class MockClient(object):
        def __init__(self):
            self.attribute = 'attribute'

        def raise_over_limit(self, retry_after=None):
            if retry_after is not None:
                kw = {'retry_after': retry_after}
            else:
                kw = {}
            raise nova_exceptions.OverLimit(code=413, **kw)

        def normal_method(self):
            return 'normal'

        def raise_other(self):
            raise RuntimeError()

    def setUp(self):
        random.seed(0)  # Make tests run in same amount of time each time
        logging.basicConfig()
        logger = logging.getLogger('test')
        logger.setLevel(logging.DEBUG)
        self.client = ExceptionRetryProxy(
            self.MockClient(),
            exception_handler=_nova_exception_handler,
            logger=logger)

    def test(self):
        self.assertRaises(AttributeError,
                          lambda: self.client.non_existent_attribute)

        start = time.time()
        self.assertEqual(self.client.attribute, 'attribute')
        self.assertLess(time.time() - start, NO_POSSIBLE_RETRY_TIME)

        start = time.time()
        self.assertEqual(self.client.normal_method(), 'normal')
        self.assertLess(time.time() - start, NO_POSSIBLE_RETRY_TIME)

        start = time.time()
        self.assertRaises(RuntimeError, self.client.raise_other)
        self.assertLess(time.time() - start, NO_POSSIBLE_RETRY_TIME)

        start = time.time()
        self.assertRaises(nova_exceptions.OverLimit,
                          self.client.raise_over_limit,
                          retry_after=RETRY_AFTER)
        t = time.time() - start
        self.assertGreater(t, (API_CALL_ATTEMPTS - 1) * RETRY_AFTER)
        self.assertLess(t, (API_CALL_ATTEMPTS - 1) * 2 * RETRY_AFTER)
