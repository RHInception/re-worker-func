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
Simple Func worker.
"""

from time import sleep

from reworker.worker import Worker

import func.overlord.client as fc

from func.minion.codes import FuncException
import func.CommonErrors


def expand_globs(globs, app_logger):
    found_hosts = []
    missing_hosts = set()
    for h in globs:
        app_logger.debug("Expanding glob (looking up host): %s" % (
            h))
        try:
            c = fc.Client(h)
            new_hosts = filter(lambda h: h not in found_hosts,
                               c.list_minions())
            found_hosts.extend(new_hosts)
        except func.CommonErrors.Func_Client_Exception as e:
            # Sure would be helpful if this exception told you exactly
            # WHICH names bombed... buuuuut what can you do?
            unmatched = e.value.split("\"")[1]
            missing_hosts.add(unmatched)
    return (found_hosts, list(missing_hosts))


class FuncWorkerError(Exception):
    """
    Base exception class for FuncWorker errors.
    """
    pass


class FuncWorker(Worker):
    """
    Simple worker which executes remote func calls.
    """

    def process(self, channel, basic_deliver, properties, body, output):
        """Executes remote func calls when requested. Only configured
        calls are allowed!

        `Params Required`:
            * command: name of the func module to run.
            * subcommand: the module sub-command to run.
            * hosts: list of hosts to run the func command on.
            ....

        `Optional Params`:
           * tries: the amount of times executing and getting success
                    from check scripts
           * check_scripts: list of check scripts to execute which
                            verify success
        """
        # Ack the original message
        self.ack(basic_deliver)
        corr_id = str(properties.correlation_id)
        # Notify we are starting
        self.send(
            properties.reply_to, corr_id, {'status': 'started'}, exchange='')

        try:
            try:
                params = body['parameters']
            except KeyError:
                raise FuncWorkerError(
                    'Params dictionary not passed to FuncWorker.'
                    ' Nothing to do!')
            # First verify it's a command we should be working with
            if params['command'] not in self._config.keys():
                raise FuncWorkerError(
                    'This worker only handles: %s' % self._config.keys())

            command_cfg = self._config[params['command']]

            # Next verify there is a subcommand
            if params['subcommand'] not in command_cfg.keys():
                raise FuncWorkerError(
                    'Requested subcommand for %s is not supported '
                    'by this worker' % params['command'])

            # Then check we have hosts to use
            if 'hosts' not in params.keys() or type(params['hosts']) != list:
                raise FuncWorkerError(
                    'This worker requires hosts to be a list of hosts.')
            # Get tries/check_scripts or set defaults
            _tries = int(params.get('tries', 1))
            _check_scripts = params.get('check_scripts', [])

           # Now verify we have what we need (and make our target_params too)
            target_hosts = None
            try:
                # Special attention for those extra-special func modules...
                module_handler = __import__("replugin.funcworker.%s" %
                                            params['command'],
                                            globals(),
                                            locals())
                (target_hosts,
                 _target_params) = module_handler.parse_target_params(params)
                target_params = _target_params.values()
                params.update(_target_params)
            except ImportError:
                # This module requires no special handling.
                pass
            except ValueError, e:
                # The handler was imported, but there is no parser for
                # the given sub-command. Or in other words, this func
                # worker doesn't have the requested subcommand. Sorry,
                # bud.
                raise FuncWorkerError(
                    'Requested subcommand for %s is not supported '
                    '(no parameter parser could be found)' % e.subcommand)
            finally:
                # TODO: Refactor this into a generalized parameter
                # parser like the unique parsers (above)
                if not target_hosts:
                    target_params = []
                    required_params = command_cfg[params['subcommand']]
                    for required in required_params:
                        if required not in params.keys():
                            raise FuncWorkerError(
                                'Command %s.%s requires the following params: %s. '
                                '%s was missing.' % (
                                    params['command'],
                                    params['subcommand'],
                                    command_cfg[params['subcommand']],
                                    required))
                        else:
                            target_params.append(params[required])

            try:
                output.info('Executing func command ...')
                # if hosts should be static then override whatever
                # we were sent
                if self._config.get('static_hosts', None):
                    target_hosts = self._config['static_hosts']
                    if len(params['hosts']):
                        self.app_logger.warning(
                            'Hosts param was not empty but static_hosts '
                            'was set. Using static_hosts from config.')
                    # Override params['hosts'] with the static_hosts list
                    params['hosts'] = [self._config['static_hosts']]
                else:
                    target_hosts = ";".join(params['hosts'])

                (found, missing) = expand_globs(
                    params['hosts'], self.app_logger)

                self.app_logger.debug("Found hosts: %s" % (
                    found))
                if missing:
                    self.app_logger.warning("Missing hosts: %s" % (
                        missing))

                if len(missing) > 0:
                    raise FuncWorkerError(
                        'Hosts not discoverable: %s' % (str(missing)))

                self.app_logger.info('Executing %s.%s(%s) on %s' % (
                    params['command'], params['subcommand'],
                    target_params, target_hosts))

                # TODO: what if we're calling multiple hosts at once?
                #
                # In the future, we basically need to loop over
                # target_hosts -- submitting each job and recording
                # the job_id -- then loop over the job ID's until each
                # job_status is JOB_ID_FINISHED (or failed)
                client = fc.Client(target_hosts, async=True)
                # Func syntax can be kind of weird, as all modules
                # ("COMMAND") appear as attributes of the `client`
                # object ..
                target_callable = getattr(
                    # First get the client.COMMAND attribute
                    getattr(client, params['command']),
                    # Next get the client.COMMAND.SUBCOMMAND method
                    params['subcommand'])
                target_callable_repr = "%s.%s" % (
                    params['command'],
                    params['subcommand'])
                for attempt_count in range(_tries):
                    self.app_logger.info("In the for loop (over _tries)")
                    output.debug(
                        'Invoking func method: "%s" with args: "%s"' % (
                            str(target_callable_repr),
                            str(target_params)))
                    # Call the fc.Client.COMMAND.SUBCOMMAND
                    # method with the collected parameters
                    job_id = target_callable(*target_params)
                    self.app_logger.debug("Ran job, id is: %s. "
                                          "Polling for results now" % job_id)
                    (status, results) = (None, None)
                    while status != func.jobthing.JOB_ID_FINISHED:
                        (status, results) = client.job_status(job_id)
                        sleep(1)

                    # TODO: what if we're calling multiple hosts at once?
                    #
                    # For async jobs, func will return a dictionary for
                    # the result. Each key in the dict is a hostname, the
                    # value is a list of [return code, stdout, stderr]
                    results = results[params['hosts'][0]]
                    self.app_logger.debug("Raw results: %s" % str(results))

                    # success set to False if anything returns non 0
                    success = True
                    # called is a nice repr of the command
                    called = '%s.%s(*%s)' % (
                        params['command'], params['subcommand'], target_params)
                    output.debug("Raw response: %s" % (
                        str(results)))
                    # results is a list
                    # item 0 = return code
                    # item 1 = stdout
                    # item 2 = stderr
                    if results[0] != 0:
                        success = False
                        output.info('%s returned %s for command %s' % (
                            target_hosts, results[0], called))

                    if success and len(_check_scripts):
                        # Execute all check scripts.
                        current_script_count = 0
                        check_scripts_passed = False
                        for check_script in _check_scripts:
                            output.info('Executing check_script %s.' % (
                                check_script))
                            check_result = client.command.run(check_script)
                            output.info(
                                '%s returned %s for check_script '
                                '%s on attempt %s' % (
                                    target_hosts, check_result[0],
                                    check_script, attempt_count))

                            # check script isn't happy, try again
                            if check_result[0] != 0:
                                output.info(
                                    'Waiting a few seconds and trying again.')
                                # Sleep for a short period before trying again
                                success = False
                                sleep(2)
                                break
                            # We get here if it returned a 0 ..
                            elif current_script_count == len(_check_scripts):
                                # since it's the last script
                                # and they all passed
                                check_scripts_passed = True

                        # If all the check scripts passed then break the loop
                        if check_scripts_passed:
                            output.info('All check scripts passed!')
                            break
                    elif success:
                        # Nothing to test with ...
                        break
            except FuncException, fex:
                raise FuncWorkerError(str(fex))

            # Notify the final state based on the return code
            if success:
                self.app_logger.info('Success for %s.%s(%s) on %s' % (
                    params['command'], params['subcommand'],
                    target_params, target_hosts))
                self.send(
                    properties.reply_to,
                    corr_id,
                    {'status': 'completed', 'data': results},
                    exchange=''
                )
                # Notify on result. Not required but nice to do.
                self.notify(
                    'FuncWorker Executed Successfully',
                    'FuncWorker successfully executed %s. See logs.' % (
                        called),
                    'completed',
                    corr_id)
            else:
                raise FuncWorkerError(
                    'FuncWorker failed trying to execute %s. See logs.' % (
                        called))
        except FuncWorkerError, fwe:
            # If a FuncWorkerError happens send a failure, notify and log
            # the info for review.
            self.app_logger.error('Failure: %s' % fwe)

            self.send(
                properties.reply_to,
                corr_id,
                {'status': 'failed', 'data': str(fwe)},
                exchange=''
            )
            self.notify(
                'FuncWorker Failed',
                str(fwe),
                'failed',
                corr_id)
            output.error(str(fwe))


def main():  # pragma: no cover
    from reworker.worker import runner
    runner(FuncWorker)


if __name__ == '__main__':  # pragma: no cover
    main()
