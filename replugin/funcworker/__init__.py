#!/usr/bin/env python
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

from reworker.worker import Worker

import func.overlord.client as fc

from func.minion.codes import FuncException


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
        """
        Executes remote func calls when requested. Only a configured
        calls are allowed!

        `Params Required`:
            * command: list of hosts to run the func command on.
            * subcommand: What do do with the targeted command.
            * hosts: list of hosts to run the func command on.
            ....
        """
        # Ack the original message
        self.ack(basic_deliver)
        corr_id = str(properties.correlation_id)
        # Notify we are starting
        self.send(
            properties.reply_to, corr_id, {'status': 'started'}, exchange='')

        try:
            try:
                params = body['params']
            except KeyError:
                raise FuncWorkerError(
                    'Params dictionary not passed to FuncWorker.'
                    ' Nothing to do!')
            # First verify it's a command we should be working with
            if params['command'] not in self._config.keys():
                raise FuncWorkerError(
                    'This worker only handles: %s' % self._config.keys())
            command_cfg = self._config[params['command']]

            if params['subcommand'] not in command_cfg.keys():
                raise FuncWorkerError(
                    'Requested subcommand for %s is not supported '
                    'by this worker' % params['command'])

            # Next verify we have what we need (and make our target_params too)
            target_params = {}
            required_params = command_cfg[params['subcommand']]
            for required in required_params:
                if required not in body['params'].keys():
                    raise FuncWorkerError(
                        'Command %s.%s requires the following params: %s. '
                        '%s was missing.' % (
                            params['command'],
                            params['subcommand'],
                            command_cfg[params['subcommand']],
                            required))

                target_params[required] = body['params'][required]

            output.info('Executing func command ...')

            try:
                client = fc.Client('127.0.0.1')
                target_callable = getattr(getattr(
                    client, params['command']), params['subcommand'])
                target_callable(**target_params)
            except FuncException, fex:
                raise FuncWorkerError(str(fex))

            # Notify the final state based on the return code
            if True:
                self.send(
                    properties.reply_to,
                    corr_id,
                    {'status': 'completed'},
                    exchange=''
                )
                # Notify on result. Not required but nice to do.
                self.notify(
                    'FuncWorker Executed Successfully',
                    'FuncWorker successfully executed %s. See logs.' % (
                        "PUT SOMETHING HELPFUL HERE"),
                    'completed',
                    corr_id)
            else:
                raise FuncWorkerError(
                    'FuncWorker failed trying to execute %s. See logs.' % (
                        "PUT SOMETHING HELPFUL HERE"))
        except FuncWorkerError, fwe:
            # If a FuncWorkerError happens send a failure, notify and log
            # the info for review.
            self.send(
                properties.reply_to,
                corr_id,
                {'status': 'failed'},
                exchange=''
            )
            self.notify(
                'FuncWorker Failed',
                str(fwe),
                'failed',
                corr_id)
            output.error(str(fwe))


if __name__ == '__main__':
    mq_conf = {
        'server': '127.0.0.1',
        'port': 5672,
        'vhost': '/',
        'user': 'guest',
        'password': 'guest',
    }
    worker = FuncWorker(
        mq_conf,
        config_file='conf/example.json',
        output_dir='/tmp/logs/')
    worker.run_forever()
