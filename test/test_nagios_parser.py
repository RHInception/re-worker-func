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
Unittests for the special nagios parser
"""

from . import TestCase
import mock
import replugin.funcworker.nagios

class TestNagiosParser(TestCase):
    def setUp(self):
        self.app_logger = mock.MagicMock('logging.Logger').__call__()

    def test_good_params_ScheduleDowntime(self):
        """nagios:ScheduleDowntime: Parsing a correct parameter dict works"""
        # Just setting downtime for services
        params_services = {
            'nagios_url': 'nagios.example.com',
            'minutes': 1,
            'service': ['TESTSERVICE'],
            'hosts': ['testhost.example.com']
        }
        print "Test: Downtime for services"
        (_p, _m) = replugin.funcworker.nagios._parse_ScheduleDowntime(
            params_services, self.app_logger)

        # Set downtime for a single service
        params_service = {
            'nagios_url': 'nagios.example.com',
            'minutes': 1,
            'service': 'TESTSERVICE',
            'hosts': ['testhost.example.com']
        }
        print "Test: Downtime for a service"
        (_p, _m) = replugin.funcworker.nagios._parse_ScheduleDowntime(
            params_service, self.app_logger)

        # Set downtime for a single service using a float for minutes
        params_service_float = {
            'nagios_url': 'nagios.example.com',
            'minutes': 1.0,
            'service': 'TESTSERVICE',
            'hosts': ['testhost.example.com']
        }
        print "Test: Downtime for a service with minutes as a float"
        (_p, _m) = replugin.funcworker.nagios._parse_ScheduleDowntime(
            params_service_float, self.app_logger)

        # Set downtime for the host
        params_host = {
            'nagios_url': 'nagios.example.com',
            'minutes': 1,
            'hosts': ['testhost.example.com']
        }
        print "Test: Downtime for a host"
        (_p, _m) = replugin.funcworker.nagios._parse_ScheduleDowntime(
            params_host, self.app_logger)

        # Set downtime for a service host
        params_service_host = {
            'nagios_url': 'nagios.example.com',
            'minutes': 1,
            'service_host': 'TESTSERVICE',
            'hosts': ['testhost.example.com']
        }
        print "Test: Downtime for a service host"
        (_p, _m) = replugin.funcworker.nagios._parse_ScheduleDowntime(
            params_service_host, self.app_logger)

        # Set downtime for a host and ALL services on the host
        params_service_ALL = {
            'nagios_url': 'nagios.example.com',
            'minutes': 1,
            'service': 'ALL',
            'hosts': ['testhost.example.com']
        }
        print "Test: Downtime for a host and ALL services on it"
        (_p, _m) = replugin.funcworker.nagios._parse_ScheduleDowntime(
            params_service_ALL, self.app_logger)

    def test_bad_params_ScheduleDowntime(self):
        """nagios:ScheduleDowntime: Parsing an incorrect parameter dict raises"""
        # Set downtime for a single service using a string for minutes
        params_service_string_minutes = {
            'nagios_url': 'nagios.example.com',
            'minutes': "1",
            'service': 'TESTSERVICE',
            'hosts': ['testhost.example.com']
        }

        with self.assertRaises(TypeError):
            print "Test: Downtime for a service with minutes as a string"
            replugin.funcworker.nagios._parse_ScheduleDowntime(
                params_service_string_minutes, self.app_logger)

    def test_good_process_result(self):
        """nagios:ProcessResult: Test processing nagios command results"""
        # TODO: Implement the process_result function
        replugin.funcworker.nagios.process_result(None)

    def test_bad_process_result(self):
        """nagios:ProcessResult: Test processing nagios command results failure"""
        # TODO: Implement the process_result function
        replugin.funcworker.nagios.process_result(None)

    @mock.patch('replugin.funcworker.nagios._parse_ScheduleDowntime')
    def test_good_parse_target_params(self, scheduledt):
        """nagios:ParseTargetParams: Test looking up a special parser passes"""
        scheduledt.return_value = ({}, [])

        params = {
            'command': 'nagios',
            'subcommand': 'ScheduleDowntime'
        }
        (_params_result,
         _method_args) = replugin.funcworker.nagios.parse_target_params(params,
                                                                        self.app_logger)
        self.app_logger.debug.assert_called_once_with("Found parser: _parse_ScheduleDowntime")
        self.app_logger.reset_mock()

    @mock.patch('replugin.funcworker.nagios._parse_ScheduleDowntime')
    def test_bad_parse_target_params(self, scheduledt):
        """nagios:ParseTargetParams: Invalid subcommands raise while looking for parser"""
        scheduledt.return_value = ({}, [])

        params = {
            'command': 'nagios',
            'subcommand': 'ScheduleTestTime'
        }

        ptp = replugin.funcworker.nagios.parse_target_params

        with self.assertRaises(ValueError):
            (_params_result,
             _method_args) = ptp(params, self.app_logger)
