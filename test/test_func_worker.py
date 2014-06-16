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

from contextlib import nested

from . import TestCase

from replugin import funcworker

from func.minion.codes import FuncException


MQ_CONF = {
    'server': '127.0.0.1',
    'port': 5672,
    'vhost': '/',
    'user': 'guest',
    'password': 'guest',
}

CONFIG_FILES = (
    # FILENAME            COMMAND    SUBCMD   REQUIRED ARGS
    ('conf/service.json', 'service', 'start', ['service']),
    ('conf/yumcmd.json', 'yumcmd', 'update', []),
    ('conf/nagios.json', 'nagios',
     'schedule_svc_downtime', ["hostname", "services", "minutes"]),
)


@mock.patch('func.overlord.client.Client')
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
        self.app_logger = mock.MagicMock('logging.Logger').__call__()
        self.connection = mock.MagicMock('pika.SelectConnection')

    def tearDown(self):
        """
        After every test.
        """
        TestCase.tearDown(self)
        self._reset_mocks()

    def _reset_mocks(self):
        """
        Force reset mocks.
        """
        self.channel.reset_mock()
        self.channel.basic_consume.reset_mock()
        self.channel.basic_ack.reset_mock()
        self.channel.basic_publish.reset_mock()

        self.basic_deliver.reset_mock()
        self.properties.reset_mock()

        self.logger.reset_mock()
        self.app_logger.reset_mock()
        self.connection.reset_mock()

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

    def test_command_params(self, fc):
        """
        Verify that if params are missing proper responses occur.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.funcworker.FuncWorker.notify'),
                mock.patch('replugin.funcworker.FuncWorker.send')):
            worker = funcworker.FuncWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file=CONFIG_FILES[0][0],
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

    def test_command_whitelist(self, fc):
        """
        Verify that if a command that is not in the whitelist is attempted
        the worker fails properly.
        """
        for config_file, cmd, sub, rargs in CONFIG_FILES:
            with nested(
                    mock.patch('pika.SelectConnection'),
                    mock.patch('replugin.funcworker.FuncWorker.notify'),
                    mock.patch('replugin.funcworker.FuncWorker.send')):
                worker = funcworker.FuncWorker(
                    MQ_CONF,
                    logger=self.app_logger,
                    config_file=config_file,
                    output_dir='/tmp/logs/')

                worker._on_open(self.connection)
                worker._on_channel_open(self.channel)

                body = {
                    'parameters': {
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
            # Force reset
            self._reset_mocks()

    def test_subcommand_whitelist(self, fc):
        """
        Verify that if a subcommand that is not in the whitelist is attempted
        the worker fails properly.
        """
        for config_file, cmd, sub, rargs in CONFIG_FILES:
            with nested(
                    mock.patch('pika.SelectConnection'),
                    mock.patch('replugin.funcworker.FuncWorker.notify'),
                    mock.patch('replugin.funcworker.FuncWorker.send')):
                worker = funcworker.FuncWorker(
                    MQ_CONF,
                    logger=self.app_logger,
                    config_file=config_file,
                    output_dir='/tmp/logs/')

                worker._on_open(self.connection)
                worker._on_channel_open(self.channel)

                body = {
                    'parameters': {
                        'command': cmd,
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

            # Force reset
            self._reset_mocks()

    def test_missing_hosts(self, fc):
        """
        Verify that if no hosts variablr is passed we fail as expected.
        """
        for config_file, cmd, sub, rargs in CONFIG_FILES:
            with nested(
                    mock.patch('pika.SelectConnection'),
                    mock.patch('replugin.funcworker.FuncWorker.notify'),
                    mock.patch('replugin.funcworker.FuncWorker.send')):
                worker = funcworker.FuncWorker(
                    MQ_CONF,
                    logger=self.app_logger,
                    config_file=config_file,
                    output_dir='/tmp/logs/')

                worker._on_open(self.connection)
                worker._on_channel_open(self.channel)

                body = {
                    'parameters': {
                        'command': cmd,
                        'subcommand': sub,
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
                    worker, 'This worker requires hosts to be a list of hosts')

            # Force reset
            self._reset_mocks()

    def test_func_client_error(self, fc):
        """
        Check that func errors fail properly.
        """
        for config_file, cmd, sub, rargs in CONFIG_FILES:
            with nested(
                    mock.patch('pika.SelectConnection'),
                    mock.patch('replugin.funcworker.FuncWorker.notify'),
                    mock.patch('replugin.funcworker.FuncWorker.send')):
                worker = funcworker.FuncWorker(
                    MQ_CONF,
                    logger=self.app_logger,
                    config_file=config_file,
                    output_dir='/tmp/logs/')

                worker._on_open(self.connection)
                worker._on_channel_open(self.channel)
                # Make the Func client raise an exception
                fc.side_effect = FuncException('Func error raised.')

                # Good data
                body = {
                    'parameters': {
                        'command': cmd,
                        'subcommand': sub,
                        'hosts': ['127.0.0.1']
                    }
                }
                for key in rargs:
                    body['parameters'][key] = 'test_data'

                # Execute the call
                worker.process(
                    self.channel,
                    self.basic_deliver,
                    self.properties,
                    body,
                    self.logger)

                self._assert_error_conditions(
                    worker, 'Func error raised.')
            # Force reset
            self._reset_mocks()

    def test_good_request(self, fc):
        """
        Verify when a good request is received the worker executes as
        expected with one or more hosts.
        """
        for config_file, cmd, sub, rargs in CONFIG_FILES:
            for hosts in (['127.0.0.1'], ['127.0.0.1', '127.0.0.2']):
                with nested(
                        mock.patch('pika.SelectConnection'),
                        mock.patch('replugin.funcworker.FuncWorker.notify'),
                        mock.patch('replugin.funcworker.FuncWorker.send')):
                    worker = funcworker.FuncWorker(
                        MQ_CONF,
                        logger=self.app_logger,
                        config_file=config_file,
                        output_dir='/tmp/logs/')

                    # Make the Func return data
                    # NOTE: this causes fc's call count to ++
                    results = [
                        0,
                        "stdout here",
                        "stderr here"
                    ]

                    target = getattr(getattr(fc(), cmd), sub)
                    target.return_value = results
                    worker._on_open(self.connection)
                    worker._on_channel_open(self.channel)

                    body = {
                        'parameters': {
                            'command': cmd,
                            'subcommand': sub,
                            'hosts': hosts
                        }
                    }
                    for key in rargs:
                        body['parameters'][key] = 'test_data'

                    # Execute the call
                    worker.process(
                        self.channel,
                        self.basic_deliver,
                        self.properties,
                        body,
                        self.logger)

                    assert worker.send.call_count == 2  # start then success
                    assert worker.send.call_args[0][2] == {
                        'status': 'completed', 'data': results,
                    }

                    # Notification should succeed
                    assert worker.notify.call_count == 1
                    expected = 'successfully executed'
                    assert expected in worker.notify.call_args[0][1]
                    assert worker.notify.call_args[0][2] == 'completed'
                    # Log should happen as info at least once
                    assert self.logger.info.call_count >= 1

                    # Func should call to create the client
                    # With mocking and expected calls this will be at least 3
                    assert fc.call_count in (3, 4)
                    assert fc.call_args[0][0] == ";".join(hosts)
                    # And the client should execute expected calls
                    assert target.call_count == 1
                    target.assert_called_with(*[
                        'test_data' for x in range(len(rargs))])

                    # Force reset
                    fc.reset_mock()
                    fc.call_count = 0
                    self._reset_mocks()

    def test_good_request_with_bad_response(self, fc):
        """
        Verify when a good request is received but func notes an issue
        the proper result occurs.
        """
        for config_file, cmd, sub, rargs in CONFIG_FILES:
            with nested(
                    mock.patch('pika.SelectConnection'),
                    mock.patch('replugin.funcworker.FuncWorker.notify'),
                    mock.patch('replugin.funcworker.FuncWorker.send')):
                worker = funcworker.FuncWorker(
                    MQ_CONF,
                    logger=self.app_logger,
                    config_file=config_file,
                    output_dir='/tmp/logs/')

                # Make the Func return data
                # NOTE: this causes fc's call count to ++
                fc_cmd = getattr(getattr(fc(), cmd), sub)
                fc_cmd.return_value = [
                    1,
                    "stdout here",
                    "stderr here"
                ]

                worker._on_open(self.connection)
                worker._on_channel_open(self.channel)

                body = {
                    'parameters': {
                        'command': cmd,
                        'subcommand': sub,
                        'hosts': ['127.0.0.1']
                    }
                }
                for key in rargs:
                    body['parameters'][key] = 'test_data'

                # Execute the call
                worker.process(
                    self.channel,
                    self.basic_deliver,
                    self.properties,
                    body,
                    self.logger)

                self._assert_error_conditions(
                    worker, 'FuncWorker failed trying to execute %s.%s' % (
                        cmd, sub))
            # Force reset
            fc.reset_mock()
            self._reset_mocks()

    def test_good_with_eventually_working_check_script(self, fc):
        """
        When test scripts return non 0 tries should execute.
        """
        # Set up the mock so the first call returns 1 and the second returns 0
        fc_mock = fc().command.run().__getitem__

        def decrement(*args):
            def second_call(*args):
                return 0
            fc_mock.side_effect = second_call
            return 1

        fc_mock.side_effect = decrement

        for config_file, cmd, sub, rargs in CONFIG_FILES:
            with nested(
                    mock.patch('pika.SelectConnection'),
                    mock.patch('replugin.funcworker.FuncWorker.notify'),
                    mock.patch('replugin.funcworker.FuncWorker.send'),
                    mock.patch('replugin.funcworker.sleep')):
                worker = funcworker.FuncWorker(
                    MQ_CONF,
                    logger=self.app_logger,
                    config_file=config_file,
                    output_dir='/tmp/logs/')

                # Make the Func return data
                # NOTE: this causes fc's call count to ++
                results = [
                    0,
                    "stdout here",
                    "stderr here"
                ]

                target = getattr(getattr(fc(), cmd), sub)
                target.return_value = results
                worker._on_open(self.connection)
                worker._on_channel_open(self.channel)

                body = {
                    'parameters': {
                        'command': cmd,
                        'subcommand': sub,
                        'hosts': ['127.0.0.1'],
                        'tries': 2,
                        'check_scripts': ['eventuallyworks'],
                    }
                }
                for key in rargs:
                    body['parameters'][key] = 'test_data'

                # Execute the call
                worker.process(
                    self.channel,
                    self.basic_deliver,
                    self.properties,
                    body,
                    self.logger)

                assert worker.send.call_count == 2  # start then success
                assert worker.send.call_args[0][2] == {
                    'status': 'completed', 'data': results,
                }

                # Notification should succeed
                assert worker.notify.call_count == 1
                expected = 'successfully executed'
                assert expected in worker.notify.call_args[0][1]
                assert worker.notify.call_args[0][2] == 'completed'
                # Log should happen as info at least once
                assert self.logger.info.call_count >= 1

                # No sleeping should have occured as the check script
                # returned 0 or wasn't provided
                assert funcworker.sleep.call_count == 0

                assert fc.call_args[0][0] == '127.0.0.1'
                # And the client should execute expected calls
                assert target.call_count == 2
                target.assert_called_with(*[
                    'test_data' for x in range(len(rargs))])

            # Force reset
            fc.reset_mock()
            self._reset_mocks()

    def test_good_with_check_failing_scripts(self, fc):
        """
        When test scripts are given they should be executed.
        """
        fc().command.run().__getitem__.return_value = 1

        for config_file, cmd, sub, rargs in CONFIG_FILES:
            with nested(
                    mock.patch('pika.SelectConnection'),
                    mock.patch('replugin.funcworker.FuncWorker.notify'),
                    mock.patch('replugin.funcworker.FuncWorker.send'),
                    mock.patch('replugin.funcworker.sleep')):
                worker = funcworker.FuncWorker(
                    MQ_CONF,
                    logger=self.app_logger,
                    config_file=config_file,
                    output_dir='/tmp/logs/')

                # Make the Func return data
                # NOTE: this causes fc's call count to ++
                results = [
                    0,
                    "stdout here",
                    "stderr here"
                ]

                target = getattr(getattr(fc(), cmd), sub)
                target.return_value = results
                worker._on_open(self.connection)
                worker._on_channel_open(self.channel)

                body = {
                    'parameters': {
                        'command': cmd,
                        'subcommand': sub,
                        'hosts': ['127.0.0.1'],
                        'tries': 2,
                        'check_scripts': ['failingcheckscript'],
                    }
                }
                for key in rargs:
                    body['parameters'][key] = 'test_data'

                # Execute the call
                worker.process(
                    self.channel,
                    self.basic_deliver,
                    self.properties,
                    body,
                    self.logger)

                assert worker.send.call_count == 2  # start then success
                print worker.send.call_args[0][2]
                assert worker.send.call_args[0][2] == {
                    'status': 'completed', 'data': results,
                }

                # Notification should succeed
                assert worker.notify.call_count == 1
                expected = 'successfully executed'
                assert expected in worker.notify.call_args[0][1]
                assert worker.notify.call_args[0][2] == 'completed'
                # Log should happen as info at least once
                assert self.logger.info.call_count >= 1

                # No sleeping should have occured as the check script
                # returned 0 or wasn't provided
                assert funcworker.sleep.call_count == 2

                assert fc.call_args[0][0] == '127.0.0.1'
                # And the client should execute expected calls
                assert target.call_count == 2
                target.assert_called_with(*[
                    'test_data' for x in range(len(rargs))])

            # Force reset
            fc.reset_mock()
            self._reset_mocks()

    def test_good_with_check_scripts(self, fc):
        """
        When test scripts are given they should be executed.
        """
        fc().command.run().__getitem__.return_value = 0

        for config_file, cmd, sub, rargs in CONFIG_FILES:
            for check_scripts in ([], ['fakescript']):
                with nested(
                        mock.patch('pika.SelectConnection'),
                        mock.patch('replugin.funcworker.FuncWorker.notify'),
                        mock.patch('replugin.funcworker.FuncWorker.send'),
                        mock.patch('replugin.funcworker.sleep')):
                    worker = funcworker.FuncWorker(
                        MQ_CONF,
                        logger=self.app_logger,
                        config_file=config_file,
                        output_dir='/tmp/logs/')

                    # Make the Func return data
                    # NOTE: this causes fc's call count to ++
                    results = [
                        0,
                        "stdout here",
                        "stderr here"
                    ]

                    target = getattr(getattr(fc(), cmd), sub)
                    target.return_value = results
                    worker._on_open(self.connection)
                    worker._on_channel_open(self.channel)

                    body = {
                        'parameters': {
                            'command': cmd,
                            'subcommand': sub,
                            'hosts': ['127.0.0.1'],
                            'tries': 2,
                            'check_scripts': check_scripts,
                        }
                    }
                    for key in rargs:
                        body['parameters'][key] = 'test_data'

                    # Execute the call
                    worker.process(
                        self.channel,
                        self.basic_deliver,
                        self.properties,
                        body,
                        self.logger)

                    assert worker.send.call_count == 2  # start then success
                    print worker.send.call_args[0][2]
                    assert worker.send.call_args[0][2] == {
                        'status': 'completed', 'data': results,
                    }

                    # Notification should succeed
                    assert worker.notify.call_count == 1
                    expected = 'successfully executed'
                    assert expected in worker.notify.call_args[0][1]
                    assert worker.notify.call_args[0][2] == 'completed'
                    # Log should happen as info at least once
                    assert self.logger.info.call_count >= 1

                    # No sleeping should have occured as the check script
                    # returned 0 or wasn't provided
                    assert funcworker.sleep.call_count == 0

                    assert fc.call_args[0][0] == '127.0.0.1'
                    # And the client should execute expected calls
                    assert target.call_count == (1 + len(check_scripts))
                    target.assert_called_with(*[
                        'test_data' for x in range(len(rargs))])

                # Force reset
                fc.reset_mock()
                self._reset_mocks()

    def test_good_with_check_failing_scripts(self, fc):
        """
        When test scripts are given they should be executed.
        """
        fc().command.run().__getitem__.return_value = 1

        for config_file, cmd, sub, rargs in CONFIG_FILES:
            with nested(
                    mock.patch('pika.SelectConnection'),
                    mock.patch('replugin.funcworker.FuncWorker.notify'),
                    mock.patch('replugin.funcworker.FuncWorker.send'),
                    mock.patch('replugin.funcworker.sleep')):
                worker = funcworker.FuncWorker(
                    MQ_CONF,
                    logger=self.app_logger,
                    config_file=config_file,
                    output_dir='/tmp/logs/')

                # Make the Func return data
                # NOTE: this causes fc's call count to ++
                results = [
                    0,
                    "stdout here",
                    "stderr here"
                ]

                target = getattr(getattr(fc(), cmd), sub)
                target.return_value = results
                worker._on_open(self.connection)
                worker._on_channel_open(self.channel)

                body = {
                    'parameters': {
                        'command': cmd,
                        'subcommand': sub,
                        'hosts': ['127.0.0.1'],
                        'tries': 2,
                        'check_scripts': ['failingcheckscript'],
                    }
                }
                for key in rargs:
                    body['parameters'][key] = 'test_data'

                # Execute the call
                worker.process(
                    self.channel,
                    self.basic_deliver,
                    self.properties,
                    body,
                    self.logger)

                assert worker.send.call_count == 2  # start then success
                print worker.send.call_args[0][2]
                assert worker.send.call_args[0][2] == {
                    'status': 'failed',
                }

                # Notification should succeed
                assert worker.notify.call_count == 1
                expected = 'failed trying to execute'
                assert expected in worker.notify.call_args[0][1]
                assert worker.notify.call_args[0][2] == 'failed'
                # Log should happen as info at least once
                assert self.logger.info.call_count >= 1

                # No sleeping should have occured as the check script
                # returned 0 or wasn't provided
                assert funcworker.sleep.call_count == 2

                assert fc.call_args[0][0] == '127.0.0.1'
                # And the client should execute expected calls
                assert target.call_count == 2
                target.assert_called_with(*[
                    'test_data' for x in range(len(rargs))])

            # Force reset
            fc.reset_mock()
            self._reset_mocks()
