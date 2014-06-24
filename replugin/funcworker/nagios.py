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
Nagios specific func worker
"""

import collections
import types
import re


def parse_target_params(params):
    """Parse the parameters provided by the FSM, `params`. Return the
formatted parameters for the actual func method call.

The sub-parsers for each possible subcommand are broken into their own
separate functions. We will try to find a parser for the subcommand,
evaluate with the provided parameters, and finally return the result.

.. todo:: Handle missing parameters
    """
    try:
        parser = globals()[str(params['subcommand'])]
    except KeyError:
        # There is no parser for the provided subcommand. Most likely
        # a typo. Either way, there's nothing we can do. Oh well.
        err = ValueError("Unknown subcommand: %s" % params['subcommand'])
        err.subcommand = params['subcommand']
        raise err

    return parser(params)


def _parse_ScheduleDowntime(params):
    """ScheduleDowntime - The API Signature for this command is simple, but
the func method it calls can vary depending on intended result.

* HOST Downtime - Calls the func method: nagios.schedule_host_downtime
* Parameters: str(host), int(minutes)

* HOST and SERVICE ('ALL') Downtime - Calls the func method:
  nagios.schedule_host_and_svc_downtime
* Parameters: str(host), int(minutes)

* SERVICE Downtime - Calls the func method: nagios.schedule_svc_downtime
* Parameters: str(host), [service], int(minutes)"""
    ##################################################################
    # Dict of parameters to update the FSM-provided 'params' dict with.
    _params = collections.OrderedDict()
    _params['command'] = 'nagios'

    ##################################################################
    # Hostname the nagios server. This is the target host for the func
    # command. That is to say, the host which the command is sent to.
    nagios_url = params['nagios_url']

    ##################################################################
    # Is a service_host set? If yes, then the "target host" is
    # service_host. Recall: "target_host" is the host being passed to
    # the nagios module to process alerts/downtime for.
    if params.get('service_host', '') != '':
        method_target_host = params['service_host']
    else:
        #.. todo:: Handle multiple params at once
        method_target_host = params['hosts'][0]

    _params['method_target_host'] = method_target_host

    ##################################################################
    # Minutes to schedule downtime for. Default: 30
    _minutes = params.get('minutes', 30)
    if not isinstance(_minutes, types.IntType):
        if isinstance(_minutes, types.FloatType):
            _minutes = int(_minutes)
        else:
            raise TypeError("Invalid data given for minutes.",
                            "Expecting int type.",
                            "Got '%s'." % _minutes)

    _params['minutes'] = _minutes

    ##################################################################
    # RECALL: ScheduleDowntime calls one of three func module
    # methods. The arguments passed to ScheduleDowntime determine
    # which module method is called.
    #
    # Did the playbook even bother to define 'service'? Default to
    # 'HOST' if 'service' is undefined.
    _service = params.get('service', 'HOST')

    # Explicitly setting downtime for a host
    if re.match(r'^HOST$', _service, re.I):
        _sub_command = "schedule_host_downtime"

    # Explicitly setting downtime for a host AND all services on it
    elif re.match(r'^ALL$', _service, re.I):
        _sub_command = "schedule_host_and_svc_downtime"

    # Set downtime for the provided item(s) in 'service'.
    else:
        # If a single string was provided and that string is not
        # 'HOST' or 'ALL' then only a single service was named. The
        # func method we're calling requires 'service' as a LIST, so
        # let's wrap it up in one.
        if isinstance(_service, types.StringTypes):
            _service = [_service]
        # No 'else' to see here. If 'service' is a list then we leave
        # it alone.

        _params['service'] = _service
        _sub_command = 'schedule_svc_downtime'

    ##################################################################
    # OK. We've processed all of the arguments. Lets assemble
    # everything and hand it back to the primary func worker.
    _params['subcommand'] = _sub_command

    ##################################################################
    # The main func worker expects what it calls "target_hosts" to be
    # a list. So we return the nagios_url as a list.
    return ([nagios_url], _params)


def process_result(result):
    """Process the result of the func command and return something
consumable by the func worker."""
    pass
