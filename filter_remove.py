from libs import command
from libs import dataloader
import re

class Command(command.DirectOnlyCommand):
    def collect_args(self, message):
        return re.search(r'(?:remove|delete)\s*filter\s*(\S+)', message.content, re.I)

    def matches(self, message):
        return self.collect_args(message) is not None

    def action(self, message):
        args = self.collect_args(message)
        self.public_namespace.db.execute('SELECT owner, active FROM filters WHERE name=?', (args.group(1), ))
        rows = self.public_namespace.db.cursor.fetchall()
        if len(rows) == 0:
            yield from self.send_message(message.channel, 'Could not find a filter with name `%s`' % args.group(1))
            return
        if rows[0]['owner'] != message.author.id:
            yield from self.send_message(message.channel, 'You are not the owner of `%s`' % args.group(1))
            return
        if rows[0]['active'] != 1:
            yield from self.send_message(message.channel, '`%s` has already been removed' % args.group(1))
            return
        # command is valid and allowed; deactivate filter
        self.public_namespace.db.execute('UPDATE filters SET active=0 WHERE name=? AND owner=?', (args.group(1), message.author.id))
        self.public_namespace.db.save()
        yield from self.send_message(message.channel, 'Successfully removed filter `%s`' % args.group(1))
