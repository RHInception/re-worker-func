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

# def _parse_Run(params, app_logger):
#     """ScheduleDowntime - The API Signature for this command is simple, but
# the func method it calls can vary depending on intended result.

# * HOST Downtime - Calls the func method: nagios.schedule_host_downtime
# * Parameters: str(host), int(minutes)

# * HOST and SERVICE ('ALL') Downtime - Calls the func method:
#   nagios.schedule_host_and_svc_downtime
# * Parameters: str(host), int(minutes)

# * SERVICE Downtime - Calls the func method: nagios.schedule_svc_downtime
# * Parameters: str(host), [service], int(minutes)"""
#     ##################################################################
#     # Dict of parameters to update the FSM-provided 'params' dict with.
#     _params = {}
#     _params['command'] = 'nagios'
#     # List of arguments to pass to the called module method
#     _method_args = []

#     ##################################################################
#     # Hostname the nagios server. This is the target host for the func
#     # command. That is to say, the host which the command is sent to.
#     nagios_url = params['nagios_url']
#     # TODO: Handle multiple 'hosts' at once
#     _method_args.append(params['hosts'][0])
#     # Remember, we run this command on the nagios server:
#     _params['hosts'] = [nagios_url]

#     ##################################################################
#     # Is a service_host set? If yes, then the "target host" is
#     # service_host. Recall: "target_host" is the host being passed to
#     # the nagios module to process alerts/downtime for.
#     if params.get('service_host', '') != '':
#         method_target_host = params['service_host']
#     else:
#         # .. todo:: Handle multiple params at once
#         method_target_host = params['hosts'][0]

#     _params['method_target_host'] = method_target_host

#     # ## *** ###   ### *** ###   ### *** ###   ### *** ###   ### *** ##
#     # Begin parsing the arguments to pass to the method call
#     # ## *** ###   ### *** ###   ### *** ###   ### *** ###   ### *** ##

#     ##################################################################
#     # Figure out if we need to add the 'service' argument as well to
#     # _method_args
#     #
#     # RECALL: ScheduleDowntime calls one of three func module
#     # methods. The arguments passed to ScheduleDowntime determine
#     # which module method is called.
#     #
#     # Did the playbook even bother to define 'service'? Default to
#     # 'HOST' if 'service' is undefined.
#     _service = params.get('service', 'HOST')
#     if isinstance(_service, types.StringTypes):
#         # String
#         # Explicitly setting downtime for a host
#         if re.match(r'^HOST$', _service, re.I):
#             _sub_command = "schedule_host_downtime"

#         # Explicitly setting downtime for a host AND all services on it
#         elif re.match(r'^ALL$', _service, re.I):
#             _sub_command = "schedule_host_and_svc_downtime"

#         else:
#             # If a single string was provided and that string is not
#             # 'HOST' or 'ALL' then only a single service was named. The
#             # func method we're calling requires 'service' as a LIST, so
#             # let's wrap it up in one.
#             _service = [_service]
#             _method_args.append(_service)
#             _sub_command = 'schedule_svc_downtime'
#     else:
#         # No 'else' to see here. If 'service' is a list then we leave
#         # it alone.
#         _method_args.append(_service)
#         _sub_command = 'schedule_svc_downtime'

#     ##################################################################
#     # Minutes to schedule downtime for. Default: 30
#     _minutes = params.get('minutes', 30)
#     if not isinstance(_minutes, types.IntType):
#         if isinstance(_minutes, types.FloatType):
#             _minutes = int(_minutes)
#         else:
#             raise TypeError("Invalid data given for minutes.",
#                             "Expecting int type.",
#                             "Got '%s'." % _minutes)

#     _params['minutes'] = _minutes
#     _method_args.append(_minutes)

#     ##################################################################
#     # OK. We've processed all of the arguments. Lets assemble
#     # everything and hand it back to the primary func worker.
#     _params['subcommand'] = _sub_command

#     ##################################################################
#     # The main func worker expects what it calls "target_hosts" to be
#     # a list. So we return the nagios_url as a list.
#     app_logger.debug("Parsed playbook parameters: %s" % (
#         str((_params, _method_args))))
#     return (_params, _method_args)


def _parse_Run(params, app_logger):
    """The point of this is to generate two output datum:

* _params - A dictionary, the values of which will be used to
  .update() the original 'params' dict (which came over the message bus)

* _method_args - A list, known as target_params in __init__.py, which
  is *passed to the func <module>.<method> created from
  <_params['command']>.<_params['subcommand']>
    """
    # Allowed parameters to the 'run' subcommand
    _run_params = ['server', 'noop', 'tags', 'enable']

    _params = {}
    # Override the default cmd/subcmd to call the general purpose
    # command runner behind-the-scenes
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
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

    # noop?

    # tags?

    # server?

    # Disable color so FUNC doesn't explode
    _cmd_parts.append("--color=false")

    # Join it all together into a string
    app_logger.debug("Parsed playbook parameters: %s" % (
        str((_params, _method_args))))
    return (_params, _method_args)


def _parse_Enable(params, app_logger):
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = []

    app_logger.debug("Parsed playbook parameters: %s" % (
        str((_params, _method_args))))
    return (_params, _method_args)


def _parse_Disable(params, app_logger):
    _disable_params = ['motd']
    _params['command'] = 'command'
    _params['subcommand'] = 'run'
    _method_args = []

    app_logger.debug("Parsed playbook parameters: %s" % (
        str((_params, _method_args))))
    return (_params, _method_args)


def process_result(result):
    """Process the result of the func command and return something
consumable by the func worker."""
    pass
