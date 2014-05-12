# Copyright (C) 2014 SEE AUTHORS FILE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Unittests.
"""

import pika
import mock

from . import TestCase

from replugin import funcworker

MQ_CONF = {
    'server': '127.0.0.1',
    'port': 5672,
    'vhost': '/',
    'user': 'guest',
    'password': 'guest',
}
CONFIG_FILE = 'conf/example.json'


class TestFuncWorker(TestCase):

    def setUp(self):
        """
        Set up some reusable mocks.
        """
        TestCase.setUp(self)
        self.channel = mock.MagicMock('pika.spec.Channel')
        self.channel.basic_consume = mock.Mock('basic_consume')
        self.channel.basic_ack = mock.Mock('basic_ack')
        self.channel.basic_publish = mock.Mock('basic_publish')

        self.basic_deliver = mock.MagicMock()
        self.basic_deliver.delivery_tag = 123

        self.properties = mock.MagicMock(
            'pika.spec.BasicProperties',
            correlation_id=123,
            reply_to='me')

        self.logger = mock.MagicMock('logging.Logger').__call__()
        self.connection = mock.MagicMock('pika.SelectConnection')

    def _assert_error_conditions(self, worker, error_msg):
        """
        Common asserts for handled errors.
        """
        # The FSM should be notified that this failed
        assert worker.send.call_count == 2  # start then error
        assert worker.send.call_args[0][2] == {'status': 'failed'}

        # Notification should be a failure
        assert worker.notify.call_count == 1
        assert error_msg in worker.notify.call_args[0][1]
        assert worker.notify.call_args[0][2] == 'failed'
        # Log should happen as an error
        assert self.logger.error.call_count == 1

    def test_command_params(self):
        """
        Verify that if params are missing proper responses occur.
        """
        with mock.patch('pika.SelectConnection'):
            with mock.patch('replugin.funcworker.FuncWorker.notify'):
                with mock.patch('replugin.funcworker.FuncWorker.send'):
                    worker = funcworker.FuncWorker(
                        MQ_CONF,
                        config_file=CONFIG_FILE,
                        output_dir='/tmp/logs/')

                    worker._on_open(self.connection)
                    worker._on_channel_open(self.channel)
                    body = {}  # No info in the body -- so no params
                    # Execute the call
                    worker.process(
                        self.channel,
                        self.basic_deliver,
                        self.properties,
                        body,
                        self.logger)
                    self._assert_error_conditions(
                        worker, 'Params dictionary not passed')

    def test_command_whitelist(self):
        """
        Verify that if a command that is not in the whitelist is attempted
        the worker fails properly.
        """
        with mock.patch('pika.SelectConnection'):
            with mock.patch('replugin.funcworker.FuncWorker.notify'):
                with mock.patch('replugin.funcworker.FuncWorker.send'):
                    worker = funcworker.FuncWorker(
                        MQ_CONF,
                        config_file=CONFIG_FILE,
                        output_dir='/tmp/logs/')

                    worker._on_open(self.connection)
                    worker._on_channel_open(self.channel)

                    body = {
                        'params': {
                            'command': 'NOTWHITELISTED',
                        },
                    }

                    # Execute the call
                    worker.process(
                        self.channel,
                        self.basic_deliver,
                        self.properties,
                        body,
                        self.logger)

                    self._assert_error_conditions(
                        worker, 'This worker only handles')

    def test_subcommand_whitelist(self):
        """
        Verify that if a subcommand that is not in the whitelist is attempted
        the worker fails properly.
        """
        with mock.patch('pika.SelectConnection'):
            with mock.patch('replugin.funcworker.FuncWorker.notify'):
                with mock.patch('replugin.funcworker.FuncWorker.send'):
                    worker = funcworker.FuncWorker(
                        MQ_CONF,
                        config_file=CONFIG_FILE,
                        output_dir='/tmp/logs/')

                    worker._on_open(self.connection)
                    worker._on_channel_open(self.channel)

                    body = {
                        'params': {
                            'command': 'service',
                            'subcommand': 'UNKNOWNSUBCOMMAND',
                        },
                    }

                    # Execute the call
                    worker.process(
                        self.channel,
                        self.basic_deliver,
                        self.properties,
                        body,
                        self.logger)

                    self._assert_error_conditions(
                        worker, 'Requested subcommand for')

    def test_good_request(self):
        """
        Verify when a good request is received the worker executes as
        expected.
        """
        with mock.patch('pika.SelectConnection'):
            with mock.patch('replugin.funcworker.FuncWorker.notify'):
                with mock.patch('replugin.funcworker.FuncWorker.send'):
                    worker = funcworker.FuncWorker(
                        MQ_CONF,
                        config_file=CONFIG_FILE,
                        output_dir='/tmp/logs/')

                    worker._on_open(self.connection)
                    worker._on_channel_open(self.channel)

                    body = {
                        'params': {
                            'command': 'service',
                            'subcommand': 'start',
                            'service': 'test_service'
                        },
                    }

                    # Execute the call
                    worker.process(
                        self.channel,
                        self.basic_deliver,
                        self.properties,
                        body,
                        self.logger)

                    assert worker.send.call_count == 2  # start then success
                    assert worker.send.call_args[0][2] == {
                        'status': 'completed',
                    }

                    # Notification should be a failure
                    assert worker.notify.call_count == 1
                    expected = 'successfully executed'
                    assert expected in worker.notify.call_args[0][1]
                    assert worker.notify.call_args[0][2] == 'completed'
                    # Log should happen as an error
                    assert self.logger.info.call_count >= 1
