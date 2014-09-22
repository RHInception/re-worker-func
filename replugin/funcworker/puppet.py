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
Puppet specific func worker
"""

import types
import re
from datetime import datetime as dt
NOW = dt.now()


def parse_target_params(params, app_logger):
    """Parse the parameters provided by the FSM, `params`. Return the
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
    return result


def _parse_Run(params, app_logger):
    """The point of this is to generate two output datum:

* _params - A dictionary, the values of which will be used to
  .update() the original 'params' dict (which came over the message bus)

* _method_args - A list, known as target_params in __init__.py, which
  is *passed to the func <module>.<method> created from
  <_params['command']>.<_params['subcommand']>
    """
    app_logger.info("Parsing puppet:Run")
    # Allowed parameters to the 'run' subcommand
    _run_params = ['server', 'noop', 'tags', 'enable']

    _params = {}
    # Override the default cmd/subcmd to call the general purpose
    # command runner behind-the-scenes
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _params['method_target_host'] = params['hosts'][0]
    # We will generate one arg here, that is the command to run
    # through func. It will be a string.
    _cmd_parts = []
    _method_args = []

    ##################################################################
    # Begin building command string
    ##################################################################

    # enable?
    if params.get('enable', False):
        _cmd_parts.append("puppet agent --enable --color=false")
        _cmd_parts.append("&&")

    # actual command
    _cmd_parts.append("puppet agent --test")

    # noop?
    if params.get('noop', False):
        _cmd_parts.append('--noop')

    # tags?
    if params.get('tags', []):
        _cmd_parts.append('--tags')
        _cmd_parts.extend(params.get('tags'))

    # server?
    if params.get('server', False):
        _cmd_parts.extend(['--server', params.get('server')])

    # Disable color so FUNC doesn't explode
    _cmd_parts.append("--color=false")

    ##################################################################
    # puppet:Run is basically a subclass of command:run. command:run
    # has one parameter, 'cmd'.
    #
    # Once this parser finishes, the value of _method_args is passed
    # to the invoked func method.
    #
    # For the purpose of bookkeeping, we will update the 'parameters'
    # passed in from the FSM to have the required 'cmd' parameter as
    # well. We'll simply set it equal to _method_args[0] (because we
    # only have one argument, that is the puppet command(s) to run.
    #
    # This doesn't have *ANY* material effect on the behavior of the
    # rest of this worker, it simply satisfies a requirement in
    # re-worker which ensures that any passed in parameters meet the
    # specification for the called method.
    _method_args.append(" ".join(_cmd_parts))
    _params['cmd'] = _method_args[0]

    # Join it all together into a string
    app_logger.debug("Parsed playbook parameters: %s" % (
        str((_params, _method_args))))
    return (_params, _method_args)


def _parse_Enable(params, app_logger):
    app_logger.info("Parsing puppet:Enable")
    _params = {}
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = ["puppet agent --enable --color=false"]
    _params['cmd'] = _method_args[0]
    _params['method_target_host'] = params['hosts'][0]
    app_logger.debug("Parsed playbook parameters: %s" % (
        str((_params, _method_args))))
    return (_params, _method_args)


def _parse_Disable(params, app_logger):
    app_logger.info("Parsing puppet:Disable")
    _params = {}
    _params['method_target_host'] = params['hosts'][0]
    _disable_params = ['motd']
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _params['method_target_host'] = params['hosts'][0]
    _cmd_parts = []
    _method_args = []
    motd_msg = "puppet disabled by Release Engine at %s" % dt.now()

    # No motd param set, use the default message
    if params.get('motd', None) is None:
        _cmd_parts.append("""echo "%s" >> /etc/motd""" % motd_msg)
        _cmd_parts.append("&&")
        _params['motd'] = """echo "%s" >> /etc/motd""" % motd_msg

    # motd param set to false -> disable updating motd
    elif params.get('motd', None) is False:
        pass

    # Custom message provided
    elif (isinstance(params.get('motd', None), str) or
          isinstance(params.get('motd', None), unicode)):
        try:
            update_motd = params.get('motd') % dt.now()
        except TypeError:
            # no %s in motd msg to put the date into
            update_motd = params.get('motd')
        _cmd_parts.append("""echo "%s" >> /etc/motd""" % update_motd)
        _cmd_parts.append("&&")

    _cmd_parts.append("puppet agent --disable --color=false")

    ##################################################################
    _method_args.append(" ".join(_cmd_parts))
    _params['cmd'] = _method_args[0]

    app_logger.info("Parsed playbook parameters: %s" % (
        str((_params, _method_args))))
    return (_params, _method_args)


def process_result(result):
    """Process the result of the func command and return something
consumable by the func worker."""
    raise NotImplementedError
