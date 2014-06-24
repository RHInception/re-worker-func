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

import func
import pika
import mock

from contextlib import nested

from . import TestCase

from replugin import funcworker
import replugin.funcworker.nagios
from func.minion.codes import FuncException


MQ_CONF = {
    'server': '127.0.0.1',
    'port': 5672,
    'vhost': '/',
    'user': 'guest',
    'password': 'guest',
}

@mock.patch('func.overlord.client.Client')
class TestParserLookup(TestCase):

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
        assert worker.send.call_args[0][2]['status'] == 'failed'

        # Notification should be a failure
        assert worker.notify.call_count == 1
        assert error_msg in worker.notify.call_args[0][1]
        assert worker.notify.call_args[0][2] == 'failed'
        # Log should happen as an error
        assert self.logger.error.call_count == 1

    def test_good_parser_lookup(self, fc):
        """
        The parser lookup mechanism succeeds for valid parameters
        """
        results = [
            0,
            "stdout here",
            "stderr here"
        ]

        # The output from job_status ...
        fc().job_status.return_value = (
            func.jobthing.JOB_ID_FINISHED,
            {'nagios.example.com': results})

        config_file = 'conf/nagios.json'
        # Nagios 'ScheduleDowntime' with the parameters we provided
        # actually calls a different func method than the provided
        # subcommand.
        func_real_subcmd = 'schedule_svc_downtime'
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

            target = getattr(getattr(fc(), 'nagios'), func_real_subcmd)
            target.return_value = results
            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            body = {
                'parameters': {
                    'command': 'nagios',
                    'subcommand': 'ScheduleDowntime',
                    'hosts': ['downtime.this.host.example.com'],
                    'minutes': 1,
                    'service': 'TESTSERVICE',
                    'nagios_url': 'nagios.example.com'
                }
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
            assert fc.call_count >= 3
            # When initializing the client, we actually call the
            # method on the nagios server.
            assert fc.call_args[0][0] == 'nagios.example.com'
            # And the client should execute expected calls
            self.assertEqual(target.call_count, 1)
            target.assert_called_with(*['downtime.this.host.example.com',
                                        ['TESTSERVICE'],
                                        1])
            # Force reset
            fc.reset_mock()
            fc.call_count = 0
            self._reset_mocks()

    # TODO: Figure out how to check that invalid subcommands are
    # caught and raised.
    # def test_bad_parser_lookup(self, fc):
    #     """
    #     The parser lookup mechanism raises for invalid parameters
    #     """
    #     results = [
    #         0,
    #         "stdout here",
    #         "stderr here"
    #     ]

    #     # The output from job_status ...
    #     fc().job_status.return_value = (
    #         func.jobthing.JOB_ID_FINISHED,
    #         {'nagios.example.com': results})

    #     config_file = 'conf/nagios.json'
    #     # Nagios 'ScheduleDowntime' with the parameters we provided
    #     # actually calls a different func method than the provided
    #     # subcommand.
    #     func_real_subcmd = 'schedule_svc_downtime'
    #     with nested(
    #             mock.patch('pika.SelectConnection'),
    #             mock.patch('replugin.funcworker.FuncWorker.notify'),
    #             mock.patch('replugin.funcworker.FuncWorker.send')):
    #         worker = funcworker.FuncWorker(
    #             MQ_CONF,
    #             logger=self.app_logger,
    #             config_file=config_file,
    #             output_dir='/tmp/logs/')

    #         # Make the Func return data
    #         # NOTE: this causes fc's call count to ++

    #         target = getattr(getattr(fc(), 'nagios'), func_real_subcmd)
    #         target.return_value = results
    #         worker._on_open(self.connection)
    #         worker._on_channel_open(self.channel)
    #         body = {
    #             'parameters': {
    #                 'command': 'nagios',
    #                 # NOTE: This is the actual invalid parameter
    #                 'subcommand': 'ScheduleDowntimeDoesNotExist',
    #                 'hosts': ['downtime.this.host.example.com'],
    #                 'minutes': 1,
    #                 'service': 'TESTSERVICE',
    #                 'nagios_url': 'nagios.example.com'
    #             }
    #         }

    #         # Execute the call
    #         worker.process(
    #             self.channel,
    #             self.basic_deliver,
    #             self.properties,
    #             body,
    #             self.logger)

    #         # TODO: How to test this? I couldn't find any record of
    #         # the FuncWorkerError that is raised in
    #         # FuncWorker.parse_params when checking with
    #         # _assert_error_conditions

    #         # Force reset
    #         fc.reset_mock()
    #         fc.call_count = 0
    #         self._reset_mocks()
