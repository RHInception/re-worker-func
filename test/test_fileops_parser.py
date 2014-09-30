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
Unittests for the special fileops parser
"""

import mock
import replugin.funcworker.fileops as fileops

from . import TestCase


class TestFileOpsParser(TestCase):

    def setUp(self):
        self.app_logger = mock.MagicMock('logging.Logger').__call__()

    def test_change_ownership(self):
        """fileops:ChangeOwnership with params parses correctly"""
        expected = ['chown user.group /tmp/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'path': '/tmp/file',
            'user': 'user',
            'group': 'group'
        }
        (update, cmd) = fileops._parse_ChangeOwnership(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_change_ownership_with_recursive(self):
        """fileops:ChangeOwnership with recursive parses correctly"""
        expected = ['chown -r user.group /tmp/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'path': '/tmp/file',
            'user': 'user',
            'group': 'group',
            'recursive': True,
        }
        (update, cmd) = fileops._parse_ChangeOwnership(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_change_ownership_error_conditions(self):
        """fileops:ChangeOwnership verify error conditions"""

        # path as a list
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'to': '/tmp/file',
            'user': 'user',
            'group': 'group',
            'path': ['/a/path/to/file'],
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangeOwnership(params, self.app_logger)

        # missing "user"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'to': '/tmp/file',
            'group': 'group',
            'path': '/a/path/to/file',
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangeOwnership(params, self.app_logger)

        # missing "group"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'to': '/tmp/file',
            'user': 'user',
            'path': '/a/path/to/file',
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangeOwnership(params, self.app_logger)

        # missing path
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'to': '/tmp/file',
            'user': 'user',
            'group': 'group',
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangeOwnership(params, self.app_logger)

    def test_change_permissions(self):
        """fileops:ChangePermissions with params parses correctly"""
        expected = ['chmod 0644 /tmp/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangePermissions',
            'path': '/tmp/file',
            'mode': '0644'
        }
        (update, cmd) = fileops._parse_ChangePermissions(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_change_permissions_with_recursive(self):
        """fileops:ChangePermissions with recursive parses correctly"""
        expected = ['chmod -R 0644 /tmp/dir']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangePermissions',
            'path': '/tmp/dir',
            'mode': '0644',
            'recursive': True
        }
        (update, cmd) = fileops._parse_ChangePermissions(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_change_permissions_error_conditions(self):
        """fileops:ChangePermissions verify error conditions"""

        # Missing "path"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangePermissions',
            'mode': '0644',
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangePermissions(params, self.app_logger)

        # Missing "mode"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangePermissions',
            'path': '/a/path/to/file',
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangeOwnership(params, self.app_logger)

    def test_find_in_files(self):
        """fileops:FindInFiles with params parses correctly"""
        expected = ['grep --regexp "test" /tmp/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'path': '/tmp/file',
            'regexp': 'test'
        }
        (update, cmd) = fileops._parse_FindInFiles(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_find_in_files_multiple(self):
        """fileops:FindInFiles with multiple paths parses correctly"""
        expected = ['grep --regexp "test" /tmp/file /tmp/dir/']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'path': ['/tmp/file', '/tmp/dir/'],
            'regexp': 'test'
        }
        (update, cmd) = fileops._parse_FindInFiles(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_find_in_files_with_recursive(self):
        """fileops:FindInFiles with recursive parses correctly"""
        expected = ['grep --regexp -r "test" /tmp/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'path': '/tmp/file',
            'regexp': 'test',
            'recursive': True,
        }
        (update, cmd) = fileops._parse_FindInFiles(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_find_in_files_with_case_insensitive(self):
        """fileops:FindInFiles with case insensitive parses correctly"""
        expected = ['grep --regexp -i "test" /tmp/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'path': '/tmp/file',
            'regexp': 'test',
            'case_insensitive': True,
        }
        (update, cmd) = fileops._parse_FindInFiles(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_find_in_files_error_conditions(self):
        """fileops:FindInFiles verify error conditions"""

        # missing "path"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'regexp': 'test',
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangeOwnership(params, self.app_logger)

        # missing "regexp"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'ChangeOwnership',
            'path': '/tmp/file',
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangeOwnership(params, self.app_logger)

    def test_mv(self):
        """fileops:Move with params parses correctly"""
        expected = ['mv /a/path/to/file /tmp/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Touch',
            'path': '/a/path/to/file',
            'to': '/tmp/file'
        }
        (update, cmd) = fileops._parse_Move(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_move_error_conditions(self):
        """fileops:Move verify error conditions"""

        # path as a list
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Move',
            'to': '/tmp/file',
            'path': ['/a/path/to/file'],
        }

        with self.assertRaises(TypeError):
            fileops._parse_Move(params, self.app_logger)

        # missing "to"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Move',
            'path': '/a/path/to/file',
        }

        with self.assertRaises(TypeError):
            fileops._parse_Move(params, self.app_logger)

        # missing "path"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Move',
            'to': '/tmp/file',
        }

        with self.assertRaises(TypeError):
            fileops._parse_Move(params, self.app_logger)

    def test_remove(self):
        """fileops:Remove with params parses correctly"""
        expected = ['rm -f /tmp/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Remove',
            'path': '/tmp/file'
        }
        (update, cmd) = fileops._parse_Remove(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_remove_multiple(self):
        """fileops:Remove with multiple paths parses correctly"""
        expected = ['rm -f /a/path/to/file /and/this']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Touch',
            'path': ['/a/path/to/file', '/and/this']
        }
        (update, cmd) = fileops._parse_Remove(params, self.app_logger)
        self.assertEqual(cmd, expected)


    def test_remove_with_recursive(self):
        """fileops:Remove with recursive parses correctly"""
        expected = ['rm -f -r /tmp/dir/']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Remove',
            'path': '/tmp/dir/',
            'recursive': True,
        }
        (update, cmd) = fileops._parse_Remove(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_remove_error_conditions(self):
        """fileops:Remove verify error conditions"""

        # missing "path"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Remove',
        }

        with self.assertRaises(TypeError):
            fileops._parse_ChangeOwnership(params, self.app_logger)

    def test_touch_single(self):
        """fileops:Touch with no params parses correctly"""
        expected = ['touch /a/path/to/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Touch',
            'path': '/a/path/to/file'
        }
        (update, cmd) = fileops._parse_Touch(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_touch_multiple(self):
        """fileops:Touch with no params parses correctly"""
        expected = ['touch /a/path/to/file /and/this']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Touch',
            'path': ['/a/path/to/file', '/and/this']
        }
        (update, cmd) = fileops._parse_Touch(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_tar_single(self):
        """fileops:Tar with one location parses correctly"""
        expected = ['tar -c -f file.tar /a/path/to/file']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Tar',
            'to': 'file.tar',
            'path': '/a/path/to/file'
        }
        (update, cmd) = fileops._parse_Tar(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_tar_multiple(self):
        """fileops:Tar verify tar with multiple locations"""
        expected = ['tar -c -f -z file.tar.gz /a/path/to/file /and/this']
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Touch',
            'to': 'file.tar.gz',
            'compression': 'gzip',
            'path': ['/a/path/to/file', '/and/this']
        }
        (update, cmd) = fileops._parse_Tar(params, self.app_logger)
        self.assertEqual(cmd, expected)

    def test_tar_error_conditions(self):
        """fileops:Tar verify error conditions"""
        # bad compression
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Touch',
            'to': 'file.tar.gz',
            'compression': 'failure',
            'path': ['/a/path/to/file', '/and/this']
        }

        with self.assertRaises(TypeError):
            fileops._parse_Tar(params, self.app_logger)
            
        # missing "to"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Touch',
            'compression': 'gzip',
            'path': ['/a/path/to/file', '/and/this']
        }

        with self.assertRaises(TypeError):
            fileops._parse_Tar(params, self.app_logger)

        # missing "path"
        params = {
            'hosts': ['testhost.example.com'],
            'command': 'fileops',
            'subcommand': 'Touch',
            'to': 'file.tar.gz',
            'compression': 'gzip'
        }

        with self.assertRaises(TypeError):
            fileops._parse_Tar(params, self.app_logger)

    @mock.patch('replugin.funcworker.fileops._parse_Touch')
    def test_good_parse_target_params(self, fileops_Touch):
        """fileops:Touch: Test looking up a special parser passes"""
        fileops_Touch.return_value = ({}, [])

        params = {
            'command': 'fileops',
            'subcommand': 'Touch'
        }
        (_params_result, _method_args) = fileops.parse_target_params(
             params, self.app_logger)
        self.app_logger.debug.assert_called_once_with("Found parser: _parse_Touch")
        self.app_logger.reset_mock()

    @mock.patch('replugin.funcworker.fileops._parse_Touch')
    def test_dangerous_parse_target_params(self, fileops_Touch):
        """fileops:Touch: Verify that if bad shell chars return it's blocked"""
        for bad_data in ([';'], ['&&'], ['|'], ['$'], ['>'], ['<']):
            fileops_Touch.reset_mock()
            fileops_Touch.return_value = ({}, bad_data)

            params = {
                'command': 'fileops',
                'subcommand': 'Touch'
            }

            with self.assertRaises(TypeError):
                (_params_result, _method_args) = fileops.parse_target_params(
                     params, self.app_logger)

    @mock.patch('replugin.funcworker.fileops._parse_Touch')
    def test_bad_parse_target_params(self, fileops_enable):
        """fileops:NotTouch: Invalid subcommands raise while looking for parser"""
        fileops_enable.return_value = ({}, [])

        params = {
            'command': 'fileops',
            'subcommand': 'NotTouch'
        }

        with self.assertRaises(ValueError):
            (_params_result, _method_args) = fileops.parse_target_params(
                params, self.app_logger)

    def test_good_process_result(self):
        """fileops:ProcessResult: Test processing fileops command results"""
        # TODO: Implement the process_result function
        with self.assertRaises(NotImplementedError):
            fileops.process_result(None)

    def test_bad_process_result(self):
        """fileops:ProcessResult: Test processing fileops command results failure"""
        # TODO: Implement the process_result function
        with self.assertRaises(NotImplementedError):
            fileops.process_result(None)
