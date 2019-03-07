from libs import command
from libs import dataloader
import re

class Command(command.DirectOnlyCommand):
    '''Remove a filter from the current channel.
If you are the owner of the filter, this also deletes the filter.

**Usage**
```@Idea delete filter <name>```
Where
**`<name>`** is the name of the filter you want to remove

If you own the filter you want to remove, include `-r` in your message.'''
    def collect_args(self, message):
        return re.search(r'(?:remove|delete)\s*filter\s*(\S+)', message.content, re.I)

    def matches(self, message):
        return self.collect_args(message) is not None

    def action(self, message):
        args = self.collect_args(message)
        remove_flag = re.search(r'\B-r\b', message.content) is not None
        self.public_namespace.db.execute('SELECT owner, active, channels FROM filters WHERE name=?', (args.group(1), ))
        rows = self.public_namespace.db.cursor.fetchall()
        if len(rows) == 0:
            yield from self.send_message(message.channel, 'Could not find a filter with name `%s`' % args.group(1))
            return
        if rows[0]['owner'] != message.author.id or (rows[0]['owner'] == message.author.id and remove_flag):
            if message.channel.id in rows[0]['channels']:
                # not owner but channel in filter; remove channel
                new_channels = rows[0]['channels'].replace(message.channel.id, '')
                new_channels = new_channels.replace(',,', ',').strip(',')
                self.public_namespace.db.execute('UPDATE filters SET channels=? WHERE name=?', (new_channels, args.group(1)))
                self.public_namespace.db.save()
                yield from self.send_message(message.channel, 'Successfully removed this channel from `%s`' % args.group(1))
            else:
                yield from self.send_message(message.channel, 'You are not the owner of `%s` and/or this channel is not in the filter' % args.group(1))
            return
        if rows[0]['active'] != 1:
            yield from self.send_message(message.channel, '`%s` has already been removed' % args.group(1))
            return
        # command is valid and allowed; deactivate filter
        self.public_namespace.db.execute('UPDATE filters SET active=0 WHERE name=? AND owner=?', (args.group(1), message.author.id))
        self.public_namespace.db.save()
        yield from self.send_message(message.channel, 'Successfully deleted filter `%s`' % args.group(1))
