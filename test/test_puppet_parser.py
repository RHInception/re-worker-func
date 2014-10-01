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
Unittests for the special puppet parser
"""

from . import TestCase
import mock
import replugin.funcworker.puppet as ppt
import replugin.funcworker.puppet
import datetime
NOW = datetime.datetime.now()


class TestPuppetParser(TestCase):
    def setUp(self):
        self.app_logger = mock.MagicMock('logging.Logger').__call__()

    ##################################################################
    # The "puppet:Run" family
    ##################################################################
    def test_run_no_params(self):
        """puppet:Run with no params parses correctly"""
        expected = ["puppet agent --test --color=false"]
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'puppet',
            'subcommand': 'Run'
        }

        (update, cmd) = ppt._parse_Run(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_run_noop(self):
        """puppet:Run with noop param parses correctly"""
        expected = ["puppet agent --test --noop --color=false"]
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'puppet',
            'subcommand': 'Run',
            'noop': True
        }
        (update, cmd) = ppt._parse_Run(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_run_tags(self):
        """puppet:Run with tags parses correctly"""
        expected = ["puppet agent --test --tags tag1 tag2 tag3 --color=false"]
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'puppet',
            'subcommand': 'Run',
            'tags': ['tag1', 'tag2', 'tag3']
        }
        (update, cmd) = ppt._parse_Run(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_run_server(self):
        """puppet:Run with specific server params parses correctly"""
        expected = ["puppet agent --test --server puppetmaster01.example.com --color=false"]
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'puppet',
            'subcommand': 'Run',
            'server': 'puppetmaster01.example.com'
        }
        (update, cmd) = ppt._parse_Run(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_run_enable(self):
        """puppet:Run with agent enable parses correctly"""
        expected = ["puppet agent --enable --color=false && puppet agent --test --color=false"]
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'puppet',
            'subcommand': 'Run',
            'enable': True
        }
        (update, cmd) = ppt._parse_Run(params, self.app_logger)
        self.assertEqual(cmd, expected)

    ##################################################################
    # The "puppet:Enable" family
    ##################################################################
    def test_enable(self):
        """puppet:Enable with no params parses correctly"""
        expected = ["puppet agent --enable --color=false"]
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'puppet',
            'subcommand': 'Enable'
        }
        (update, cmd) = ppt._parse_Enable(params, self.app_logger)
        self.assertEqual(cmd, expected)

    ##################################################################
    # The "puppet:Disable" family
    ##################################################################
    def test_disable(self):
        """puppet:Disable with no params parses correctly"""

        with mock.patch('replugin.funcworker.puppet.dt') as (
                dt):
            dt.now.return_value = NOW

            # FIXME
            #expected = ["""echo "puppet disabled by Release Engine at %s" >> /etc/motd && puppet agent --disable --color=false""" % NOW]
            expected = ["""puppet agent --disable --color=false"""]
            params = {
                'hosts': ['testhost.example.com'],
                'command': 'puppet',
                'subcommand': 'Disable'
            }
            (update, cmd) = ppt._parse_Disable(params, self.app_logger)
            self.assertEqual(cmd, expected)

    def test_disable_no_motd(self):
        """puppet:Disable with no motd update parses correctly"""
        # This is the same as the test_disable test
        expected = ["puppet agent --disable --color=false"]
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'puppet',
            'subcommand': 'Disable',
            'motd': False
        }
        (update, cmd) = ppt._parse_Disable(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_disable_custom_motd(self):
        """puppet:Disable with custom motd update parses correctly"""

        # FIXME
        #expected = ["""echo "custom message" >> /etc/motd && puppet agent --disable --color=false"""]
        expected = ["""puppet agent --disable --color=false"""]
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'puppet',
            'subcommand': 'Disable',
            'motd': 'custom message'
        }
        (update, cmd) = ppt._parse_Disable(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_disable_custom_motd_with_date(self):
        """puppet:Disable with custom motd with date update parses correctly"""
        with mock.patch('replugin.funcworker.puppet.dt') as (
                dt):
            dt.now.return_value = NOW

            # FIXME
            #expected = ["""echo "custom message %s" >> /etc/motd && puppet agent --disable --color=false""" % NOW]
            expected = ["""puppet agent --disable --color=false"""]
            params = {
                'hosts': ['testhost.example.com'],
                'command': 'puppet',
                'subcommand': 'Disable',
                'motd': 'custom message %s'
            }
            (update, cmd) = ppt._parse_Disable(params, self.app_logger)
            self.assertEqual(cmd, expected)

    @mock.patch('replugin.funcworker.puppet._parse_Enable')
    def test_good_parse_target_params(self, ppt_enable):
        """puppet:Enable: Test looking up a special parser passes"""
        ppt_enable.return_value = ({}, [])

        params = {
            'command': 'puppet',
            'subcommand': 'Enable'
        }
        (_params_result,
         _method_args) = replugin.funcworker.puppet.parse_target_params(params,
                                                                        self.app_logger)
        self.app_logger.debug.assert_called_once_with("Found parser: _parse_Enable")
        self.app_logger.reset_mock()

    @mock.patch('replugin.funcworker.puppet._parse_Enable')
    def test_bad_parse_target_params(self, ppt_enable):
        """puppet:Enable: Invalid subcommands raise while looking for parser"""
        ppt_enable.return_value = ({}, [])

        params = {
            'command': 'puppet',
            'subcommand': 'Unable'
        }

        ptp = replugin.funcworker.puppet.parse_target_params

        with self.assertRaises(ValueError):
            (_params_result,
             _method_args) = ptp(params, self.app_logger)

    @mock.patch('replugin.funcworker.puppet._parse_Enable')
    def test_dangerous_parse_target_params(self, ppt_Enable):
        """fileops:Enable: Verify that if bad shell chars return it's blocked"""
        for bad_data in ([';'], ['&&'], ['|'], ['$'], ['>'], ['<']):
            ppt_Enable.reset_mock()
            ppt_Enable.return_value = ({}, bad_data)

            params = {
                'command': 'puppet',
                'subcommand': 'Enable'
            }

            ptp = replugin.funcworker.puppet.parse_target_params

            with self.assertRaises(TypeError):
                (_params_result,
                 _method_args) = ptp(params, self.app_logger)

    def test_good_process_result(self):
        """puppet:ProcessResult: Test processing puppet command results"""
        # TODO: Implement the process_result function
        with self.assertRaises(NotImplementedError):
            replugin.funcworker.puppet.process_result(None)

    def test_bad_process_result(self):
        """puppet:ProcessResult: Test processing puppet command results failure"""
        # TODO: Implement the process_result function
        with self.assertRaises(NotImplementedError):
            replugin.funcworker.puppet.process_result(None)
