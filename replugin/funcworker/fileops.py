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
File operations specific func worker
"""

import types
import re

from replugin.funcworker import block_bad_chars


def parse_target_params(params, app_logger):
    """
    Parse the parameters provided by the FSM, `params`. Return the
    formatted parameters for the actual func method call.

    The sub-parsers for each possible subcommand are broken into their own
    separate functions. We will try to find a parser for the subcommand,
    evaluate with the provided parameters, and finally return the result.
    """
    try:
        parser_name = "_parse_%s" % str(params['subcommand'])
        parser = globals()[parser_name]
        app_logger.debug("Found parser: %s" % parser_name)
    except KeyError, e:
        # There is no parser for the provided subcommand. Most likely
        # a typo. Either way, there's nothing we can do. Oh well.
        app_logger.error("No parser found for the given subcommand: %s" % (
            params['subcommand']))
        err = ValueError("Unknown subcommand: %s - %s " % (
            params['subcommand'],
            str(e)))
        err.subcommand = params['subcommand']
        raise err

    result = parser(params, app_logger)
    block_bad_chars(result[1])
    return result


def _parse_ChangeOwnership(params, app_logger):
    """
    Provides chown capability.
    """
    app_logger.info("Parsing fileops:ChangeOwnership")
    _params = {}
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = ['chown']
    _params['cmd'] = _method_args[0]
    _params['method_target_host'] = params['hosts'][0]

    try:
        filename = params['path']
        user = params['user']
        group = params['group']
        recursive = params.get('recursive', None)

        if recursive:
            _method_args.append('-R')

        _method_args.append('%s.%s' % (user, group))

        if not isinstance(filename, types.StringTypes):
            raise TypeError('path must be a string')

        _method_args.append(filename)
        _method_args = [' '.join(_method_args)]

        app_logger.debug("Parsed playbook parameters: %s" % (
            str((_params, _method_args))))
        return (_params, _method_args)
    except KeyError, ke:
        raise TypeError('%s must be given as a parameter.' % ke)


def _parse_ChangePermissions(params, app_logger):
    """
    Provides chmod capability.
    """
    app_logger.info("Parsing fileops:ChangePermissions")
    _params = {}
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = ['chmod']
    _params['cmd'] = _method_args[0]
    _params['method_target_host'] = params['hosts'][0]

    try:
        filename = params['path']
        mode = params['mode']
        recursive = params.get('recursive', None)

        if recursive:
            _method_args.append('-R')

        if not isinstance(filename, types.StringTypes):
            raise TypeError('path must be a string')

        _method_args.append(mode)
        _method_args.append(filename)
        _method_args = [' '.join(_method_args)]

        app_logger.debug("Parsed playbook parameters: %s" % (
            str((_params, _method_args))))
        return (_params, _method_args)
    except KeyError, ke:
        raise TypeError('%s must be given as a parameter.' % ke)


def _parse_FindInFiles(params, app_logger):
    """
    Provides basic grep capability.
    """
    app_logger.info("Parsing fileops:FindInFiles")
    _params = {}
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = ['grep --regexp']
    _params['cmd'] = _method_args[0]
    _params['method_target_host'] = params['hosts'][0]

    recursive = params.get('recursive', None)
    case_insensitive = params.get('case_insensitive', None)

    if recursive:
        _method_args.append('-r')
    if case_insensitive:
        _method_args.append('-i')

    try:
        filenames = params['path']
        regexp = '"' + params['regexp'].replace('"', '\\"') + '"'
        _method_args.append(regexp)
        if not isinstance(filenames, types.ListType):
            filenames = [str(filenames)]

        for filename in filenames:
            _method_args.append(filename)
        _method_args = [' '.join(_method_args)]

        app_logger.debug("Parsed playbook parameters: %s" % (
            str((_params, _method_args))))
        return (_params, _method_args)
    except KeyError, ke:
        raise TypeError('%s must be given as a parameter.' % ke)


def _parse_Move(params, app_logger):
    """
    Provides mv capability.
    """
    app_logger.info("Parsing fileops:Move")
    _params = {}
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = ['mv']
    _params['cmd'] = _method_args[0]
    _params['method_target_host'] = params['hosts'][0]

    try:
        filename = params['path']
        to_path = params['to']

        if not isinstance(filename, types.StringTypes):
            raise TypeError('path must be a string')

        _method_args.append(filename)
        _method_args.append(to_path)
        _method_args = [' '.join(_method_args)]

        app_logger.debug("Parsed playbook parameters: %s" % (
            str((_params, _method_args))))
        return (_params, _method_args)
    except KeyError, ke:
        raise TypeError('%s must be given as a parameter.' % ke)


def _parse_Remove(params, app_logger):
    """
    Provides rm archiving capability.
    """
    app_logger.info("Parsing fileops:Remove")
    _params = {}
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = ['rm -f']
    _params['cmd'] = _method_args[0]
    _params['method_target_host'] = params['hosts'][0]

    recursive = params.get('recursive', None)

    if recursive:
        _method_args.append('-r')

    filenames = params.get('path', None)
    if filenames is None:
        raise TypeError('path must be given as a parameter.')

    if not isinstance(filenames, types.ListType):
        filenames = [str(filenames)]

    for filename in filenames:
        _method_args.append(filename)
    _method_args = [' '.join(_method_args)]

    app_logger.debug("Parsed playbook parameters: %s" % (
        str((_params, _method_args))))
    return (_params, _method_args)


def _parse_Touch(params, app_logger):
    """
    Provides touch capability.
    """
    app_logger.info("Parsing fileops:Touch")
    _params = {}
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = ['touch']
    _params['cmd'] = _method_args[0]
    _params['method_target_host'] = params['hosts'][0]

    filenames = params.get('path', None)
    if filenames is None:
        raise TypeError('path must be given as a parameter.')

    if not isinstance(filenames, types.ListType):
        filenames = [str(filenames)]

    for filename in filenames:
        _method_args.append(filename)
    _method_args = [' '.join(_method_args)]

    app_logger.debug("Parsed playbook parameters: %s" % (
        str((_params, _method_args))))
    return (_params, _method_args)


def _parse_Tar(params, app_logger):
    """
    Provides Tar archiving capability.
    """
    app_logger.info("Parsing fileops:Tar")
    _params = {}
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = ['tar -c']
    _params['cmd'] = _method_args[0]
    _params['method_target_host'] = params['hosts'][0]

    try:
        to_path = params['to']
        filenames = params['path']
        compression = params.get('compression', None)
        if compression:
            if compression.lower() == 'gzip':
                _method_args.append('-z')
            elif compression.lower() == 'bzip':
                _method_args.append('-j')
            else:
                app_logger.info(
                    'Unknown compression requested: %s' % compression)
                raise TypeError('Unknown compression given!')

        _method_args.append('-f')
        _method_args.append(to_path)

        if not isinstance(filenames, types.ListType):
            filenames = [str(filenames)]

        for filename in filenames:
            _method_args.append(filename)
        _method_args = [' '.join(_method_args)]

        app_logger.debug("Parsed playbook parameters: %s" % (
            str((_params, _method_args))))
        return (_params, _method_args)
    except KeyError, ke:
        raise TypeError('%s must be given as a parameter.' % ke)


def process_result(result):
    """
    Process the result of the func command and return something
    consumable by the func worker.
    """
    raise NotImplementedError()
