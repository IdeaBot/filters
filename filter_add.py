from libs import command
import re

class Command(command.DirectOnlyCommand):
    '''Add a filter to the current channel.

**Usage**
```@Idea add filter <name>```
Where
**`<name>`** is the name of the filter to remove '''
    def collect_args(self, message):
        return re.search(r'(?:\badd)\s*filter\s*(\S+)', message.content, re.I)

    def matches(self, message):
        return self.collect_args(message) is not None

    def action(self, message):
        filter_name = self.collect_args(message).group(1)
        self.public_namespace.db.execute('SELECT channels FROM filters WHERE name=? AND active=1 AND (public=1 OR owner=?)', (filter_name, message.author.id))
        results = self.public_namespace.db.cursor.fetchall()
        if len(results) == 0:
            yield from self.send_message(message.channel, 'Unable to find a filter named `%s`. Either you do not have access to that filter or it does not exist.' % filter_name)
            return

        channels = results[0]['channels']+','+message.channel.id
        self.public_namespace.db.execute('UPDATE filters SET channels=? WHERE name=?', (channels, filter_name))
        self.public_namespace.db.save()
        yield from self.send_message(message.channel, 'Successfully added this channel to `%s`' % filter_name)

    def help(self, *args, **kwargs):
        help_str = super().help(*args, **kwargs)
        # add featured filters to help
        self.public_namespace.db.execute('SELECT name, action FROM filters WHERE featured=1 AND active=1 AND public=1')
        results = self.public_namespace.db.cursor.fetchall()
        if len(results) > 0:
            help_str += '\n\n**__Featured__**\n'
            for row in results:
                help_str += '**' + row['name'] + '** | ' + row['action'].upper() + '\n'
        return help_str
