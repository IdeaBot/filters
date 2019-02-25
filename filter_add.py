from libs import command
from libs import dataloader
import re
import time
import json

class Command(command.DirectOnlyCommand):
    def collect_args(self, message):
        return re.search(r'(?:add|create)\s*filter\s*(\S+)\s+match\s*(\S+)\s+action\s*(\S+)(?:\s+([\S]+))?', message.content, re.I)

    def matches(self, message):
        return self.collect_args(message) is not None

    def action(self, message):
        args = self.collect_args(message)
        self.public_namespace.db.execute('SELECT name FROM filters WHERE name=?', (args.group(1),))
        if len(self.public_namespace.db.cursor.fetchall()) > 0:
            yield from self.send_message(message.channel, 'The name you chose is already in use. Please choose a different one.')
            return
        if args.group(3).lower() not in self.public_namespace.FILTER_ACTIONS:
            yield from self.send_message(message.channel, 'The action you chose is invalid. Please choose a valid action.')
            return
        self.public_namespace.db.execute('INSERT INTO filters (name, owner, server, channel, regex, created, action, param) VALUES (?,?,?,?,?,?,?,?)',
                        (args.group(1), message.author.id, message.server.id, message.channel.id, args.group(2), time.time(), args.group(3), args.group(4)) )
        self.public_namespace.db.save()
        response = 'Successfully created filter `%s`' % args.group(1)
        if re.search(r'-\bv\b', message.content) is not None:
            self.public_namespace.db.execute('SELECT * FROM filters WHERE name=?', (args.group(1), ))
            row = self.public_namespace.db.cursor.fetchone()
            response += '\n```%s```' % json.dumps(dict(zip(row.keys(), row)), indent=2)
        yield from self.send_message(message.channel, response)
