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


class FuncWorker(Worker):
    """
    Simple worker which executes remote func calls.
    """

    def process(self, channel, basic_deliver, properties, body, output):
        """
        Executes remote func calls when requested. Only a configured
        calls are allowed!
        """
        # Ack the original message
        self.ack(basic_deliver)
        corr_id = str(properties.correlation_id)
        # Notify we are starting
        self.send(
            properties.reply_to, corr_id, {'status': 'started'}, exchange='')

        # TODO: Put logic stuff here

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
                'FuncWorker successfully executed %s. See logs.' % " ".join(
                    "PUT SOMETHING HELPFUL HERE"),
                'completed',
                corr_id)

        else:
            self.send(
                properties.reply_to,
                corr_id,
                {'status': 'failed'},
                exchange=''
            )
            # Notify on result. Not required but nice to do.
            self.notify(
                'FuncWorker Failed',
                'FuncWorker failed trying to execute %s. See logs.' % " ".join(
                    "PUT SOMETHING HELPFUL HERE"),
                'failed',
                corr_id)



if __name__ == '__main__':
    mq_conf = {
        'server': '127.0.0.1',
        'port': 5672,
        'vhost': '/',
        'user': 'guest',
        'password': 'guest',
    }
    worker = FuncWorker(mq_conf, output_dir='/tmp/logs/')
    worker.run_forever()
