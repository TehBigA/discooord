from __future__ import print_function

from collections import defaultdict
from random import randint
import re
import sqlite3
import urllib

from .client import Client
from .permissions import READ_MESSAGES, SEND_MESSAGES
from .enums import EVENT_GUILD_MEMBER_REMOVE, EVENT_MESSAGE_CREATE, EVENT_MESSAGE_REACTION_ADD, EVENT_MESSAGE_REACTION_REMOVE  # , EVENT_VOICE_STATE_UPDATE
from .utils import MENTION_REGEX, EMOJI_REGEX, MENTION_TYPE_USER, MENTION_TYPE_NICKNAME, FiniteTimer, Timer, is_unicode

from .extras.command import CommandManager, Command
from .extras.examples.infix import infix
from .extras.examples.email import EmailChecker

# https://discordapp.com/oauth2/authorize?client_id=212805913013256192&scope=bot&permissions=3072

TOKEN = 'MjEyODA1OTEzMDEzMjU2MTky.CoxOhw.aKa_nQkdin778UMprSye8fKSf-U'
PERMISSIONS = READ_MESSAGES + SEND_MESSAGES


client = Client(token=TOKEN, log_gateway_messages=False)
database = sqlite3.connect('discooord.db', check_same_thread=False)  # Make thread safe
database.row_factory = sqlite3.Row


@client.event(EVENT_GUILD_MEMBER_REMOVE)
def member_left(client, data):
    print('{} has left the guild.'.format(data.user.username))


@client.event(EVENT_MESSAGE_CREATE)
def good_shit(client, message):
    if message.content[0] == '/':
        split = message.content.split()
        if split[0] == '/goodshit':
            msg = u'\U0001f44c\U0001f440\U0001f44c\U0001f440\U0001f44c\U0001f440\U0001f44c\U0001f440\U0001f44c\U0001f440 {0} {1} {0} {1}\U0001f44c {2} \u2714 {3} {0}\U0001f44c\U0001f44c{1} right\U0001f44c\U0001f44cthere\U0001f44c\U0001f44c\U0001f44c right\u2714there \u2714\u2714if i do \u01bda\u04af so my self \U0001f4af i say so \U0001f4af {2} what im talking about right there right there (chorus: \u02b3\u1da6\u1d4d\u02b0\u1d57 \u1d57\u02b0\u1d49\u02b3\u1d49) mMMMM\u13b7\u041c\U0001f4af \U0001f44c\U0001f44c \U0001f44c\u041dO0\u041e\u0b20OOOOO\u041e\u0b20\u0b20Oooo\u1d52\u1d52\u1d52\u1d52\u1d52\u1d52\u1d52\u1d52\u1d52\U0001f44c \U0001f44c\U0001f44c \U0001f44c \U0001f4af \U0001f44c \U0001f440 \U0001f440 \U0001f440 \U0001f44c\U0001f44c{0} {1}'
            msg = msg.format(
                split[1] if len(split) >= 2 else 'good',
                split[2] if len(split) >= 3 else 'shit',
                split[3] if len(split) >= 4 else 'thats',
                split[4] if len(split) >= 5 else 'some',
                message.author.id
            )

            client.messages.put(message.channel_id, msg)
            client.messages.delete(message.channel_id, message.id)


'''VOICE_STATE_CHANNEL = None
VOICE_STATE_LAST_CHANNEL = {}


@client.event(EVENT_GUILD_CREATE)
def voice_state_init(client, guild):
    global VOICE_STATE_CHANNEL

    if guild.name != '|G4P|':
        return

    for channel in guild.channels:
        if channel.type == 'text' and channel.name == 'voicelogs':
            VOICE_STATE_CHANNEL = channel.id


@client.event(EVENT_VOICE_STATE_UPDATE)
def voice_state(client, state):
    global VOICE_STATE_CHANNEL

    if VOICE_STATE_CHANNEL is None:
        return

    last = VOICE_STATE_LAST_CHANNEL.get(state.user_id, None)
    new = state.channel_id

    if new != last:
        client.messages.put(VOICE_STATE_CHANNEL, '<@!{}> moved to <#{}>'.format(state.user_id, new))
        VOICE_STATE_LAST_CHANNEL[state.user_id] = state.channel_id'''


manager = CommandManager(client, help=[
    u'\nI can also do math! Just send a message with an equal sign followed by an equation such as `=1+1`. Type `=?` to get more information.'
])

DICE_ROLL_REGEX = re.compile(r'^(\d+) ?d ?(\d+)(?: ?([+-]) ?(\d+))?$')


@manager.register
class Roll(Command):
    description = 'Roll dice just like in the real world, but with less randomness (ie. 1d20+4).'

    def target(self, payload, raw, *args):
        m = DICE_ROLL_REGEX.match(raw)

        if m is None:
            self.client.messages.put(payload.channel_id, "<@!{}> You want me to roll what?".format(payload.author.id))
            return

        count = int(m.group(1))
        sides = int(m.group(2))
        modifier_sign = m.group(3)
        modifier_magnitude = m.group(4)

        if sides <= 0 or sides > 100:
            self.client.messages.put(payload.channel_id, "<@!{}>... I'm not rolling that size of a die. :expressionless:".format(payload.author.id))
            return

        if count <= 0 or count > 100:
            self.client.messages.put(payload.channel_id, "<@!{}>... I'm not rolling that many dice. :expressionless:".format(payload.author.id))
            return

        results = []
        for x in xrange(count):
            results.append(randint(1, sides))

        final = sum(results)
        if modifier_sign and modifier_magnitude:
            modifier_magnitude = int(modifier_magnitude)

            if modifier_sign == '+':
                final = final + modifier_magnitude
            elif modifier_sign == '-':
                final = final - modifier_magnitude

        if len(results) > 1:
            last = results.pop()
            self.client.messages.put(payload.channel_id, '<@!{}> I rolled *{}* and *{}*{}  to get ***{}***.'.format(
                payload.author.id,
                ', '.join([str(r) for r in results]),
                last,
                '' if not modifier_magnitude else ' *{} {}*'.format('plus' if modifier_sign == '+' else 'minus', modifier_magnitude),
                final
            ))
        else:
            self.client.messages.put(payload.channel_id, '<@!{}> I rolled *{}*{}  to get ***{}***.'.format(
                payload.author.id,
                results[0],
                '' if not modifier_magnitude else ' *{} {}*'.format('plus' if modifier_sign == '+' else 'minus', modifier_magnitude),
                final
            ))


@manager.register
class Exit(Command):
    cleanup = True
    hidden = True

    def target(self, payload, raw, *args):
        if payload.author.id != '133076281716768768':
            self.client.messages.put(payload.channel_id, 'No.')
            return

        #self.client.messages.put(payload.channel_id, 'Goodbye <@{}>.'.format(payload.author.id))
        self.client.shutdown()


@manager.register
class Eval(Command):
    hidden = True

    def target(self, payload, raw, *args):
        if payload.author.id != '133076281716768768':
            self.client.messages.put(payload.channel_id, '<@{}>: ```Fuck off.```'.format(payload.author.id))
            return

        try:
            results = eval(raw, {}, {'client': client, 'database': database})
            self.client.messages.put(payload.channel_id, u'<@{}>: ```{}```'.format(payload.author.id, results))
        except Exception as e:
            self.client.messages.put(payload.channel_id, u'<@{}> ERROR: ```{}```'.format(payload.author.id, e))


database.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        user_id VARCHAR(32) NOT NULL,
        rating VARCHAR(32) NOT NULL,
        count INT(11),
        UNIQUE (user_id, rating)
    )
''')


@client.event(EVENT_MESSAGE_REACTION_ADD)
def add_rating(client, reaction):
    message = client.messages.get(reaction.channel_id, reaction.message_id)
    if reaction.user_id == message.author.id:
        return

    rating = reaction.emoji.name
    if message.author.id == '133678730336796672' and rating == 'smarked':
        return

    database.execute(u'INSERT OR IGNORE INTO ratings VALUES (?, ?, 0)', (message.author.id, rating))
    database.execute(u'UPDATE ratings SET count = count + 1 WHERE user_id = ? AND rating = ?', (message.author.id, rating))


# 2016/11/13 - 5:11pm EST
@client.event(EVENT_MESSAGE_REACTION_REMOVE)
def remove_rating(client, reaction):
    message = client.messages.get(reaction.channel_id, reaction.message_id)
    if reaction.user_id == message.author.id:
        return

    rating = reaction.emoji.name
    if message.author.id == '133678730336796672' and rating == 'smarked':
        return

    database.execute(u'INSERT OR IGNORE INTO ratings VALUES (?, ?, 0)', (message.author.id, rating))
    database.execute(u'UPDATE ratings SET count = MAX(0, count - 1) WHERE user_id = ? AND rating = ?', (message.author.id, rating))


@manager.register
class Rate(Command):
    description = 'Rate people just like on Facepunch!'

    def target(self, payload, raw, *args):
        channel = client.cache.channels[payload.channel_id]

        guild = None
        if not channel.is_private:
            guild = client.cache.guilds[channel.guild_id]
            emojis = {e.name: e.id for e in guild.emojis}
        else:
            emojis = {}

        count = len(args)

        if count < 1:
            return
        elif args[0] != 'top':
            mention = MENTION_REGEX.match(args[0])

            mention_id = None
            mention_type = None

            if mention:
                (mention_type, mention_id) = mention.groups()

                if mention_type not in (MENTION_TYPE_USER, MENTION_TYPE_NICKNAME):
                    return
            else:
                # Check if a user has this name
                for id, user in client.cache.users.iteritems():
                    if user.username.lower() == args[0].lower():
                        mention_id = user.id
                        break

                # Check the nicknames
                if guild is not None:
                    guild_members = client.cache.guild_memberships[guild.id]
                    for id, member in guild_members.iteritems():
                        if member.nick and member.nick.lower() == args[0].lower():
                            mention_id = member.user.id
                            break

                if not mention_id:
                    return

        if count < 2:
            data = database.execute(u'SELECT rating, count FROM ratings WHERE user_id = ? ORDER BY count DESC', (mention_id,)).fetchall()

            ratings = []
            for row in data:
                rating = None
                if is_unicode(row['rating']):
                    rating = u'{rating} x{count}'.format(**row)
                elif row['rating'] in emojis:
                    rating = u'<:{rating}:{emoji_id}> x{count}'.format(emoji_id=emojis[row['rating']], **row)

                if rating:
                    ratings.append(rating)

            client.messages.put(payload.channel_id, u"{}'s ratings are:\n  {}".format(
                client.cache.users[mention_id].username,
                u', '.join(ratings)
            ))
        elif args[0] == 'top':
            if args[1] == 'unique':
                data = database.execute(u'''
                    SELECT
                        DISTINCT r.rating,
                        (SELECT rr.user_id FROM ratings rr WHERE rr.rating = r.rating ORDER BY rr.`count` DESC LIMIT 1) user_id,
                        MAX(r.`count`) `count`
                    FROM ratings r
                    GROUP BY r.rating
                    ORDER BY MAX(r.count) DESC
                ''')

                user_data = defaultdict(lambda: {'user_id': None, 'total_unique': 0, 'ratings': {}})
                for row in data:
                    ud = user_data[row['user_id']]
                    ud['user_id'] = row['user_id']
                    ud['total_unique'] += 1
                    ud['ratings'][row['rating']] = row['count']

                users_ratings = []
                for user_id, ud in sorted(user_data.iteritems(), key=lambda x: x[1]['total_unique'], reverse=True):
                    ratings = []
                    for r, c in sorted(ud['ratings'].iteritems(), key=lambda x: x[1], reverse=True):
                        rating = None
                        if is_unicode(r):
                            rating = u'{} x{}'.format(r, c)
                        elif r in emojis:
                            rating = u'<:{}:{}> x{}'.format(r, emojis[r], c)

                        if rating:
                            ratings.append(rating)

                    if ratings:
                        users_ratings.append((user_id, u', '.join(ratings)))

                client.messages.put(payload.channel_id, u'Top unique ratings:\n{}'.format(
                    u'\n'.join([u'{} with {}'.format(client.cache.users[user_id].username, ratings) for user_id, ratings in users_ratings])
                ))
            elif args[1] == 'overall':
                data = database.execute(u'''
                    SELECT
                        user_id,
                        SUM(`count`) total
                    FROM ratings
                    GROUP BY user_id
                    ORDER BY count DESC
                ''')

                client.messages.put(payload.channel_id, u'Top unique ratings:\n{}'.format(
                    u'\n'.join([u'{} with {}'.format(client.cache.users[row['user_id']].username, row['total']) for row in data])
                ))
            else:
                s = args[1]
                if is_unicode(s):
                    # Unicode emoji
                    rating = s
                else:
                    # Custom emoji
                    match = EMOJI_REGEX.match(s)
                    if match:
                        rating = match.group(1)

                if rating:
                    row = database.execute(u'SELECT user_id, rating, count FROM ratings WHERE rating = ? ORDER BY count DESC LIMIT 5', (rating,)).fetchone()
                    if row:
                        rating = None
                        if is_unicode(row['rating']):
                            rating = u'{rating}'.format(**row)
                        elif row['rating'] in emojis:
                            rating = u'<:{rating}:{emoji_id}>'.format(emoji_id=emojis[row['rating']], **row)

                        if rating:
                            client.messages.put(payload.channel_id, u"{} with {} {}s!".format(
                                client.cache.users[row['user_id']].username,
                                row['count'],
                                rating
                            ))
        elif payload.author.id != mention_id:
            for s in args[1:]:
                rating = None

                if len(s) == 2 and is_unicode(s):
                    # Unicode emoji
                    rating = s
                else:
                    # Custom emoji
                    match = EMOJI_REGEX.match(s)
                    if match:
                        rating = match.group(1)

                if not rating:
                    continue
                elif mention_id == '133678730336796672' and rating == 'smarked':
                    return

                database.execute(u'INSERT OR IGNORE INTO ratings VALUES (?, ?, 0)', (mention_id, rating))
                database.execute(u'UPDATE ratings SET count = count + 1 WHERE user_id = ? AND rating = ?', (mention_id, rating))

        database.commit()


from cleverbot import Cleverbot
cb = Cleverbot()


@client.event(EVENT_MESSAGE_CREATE)
def cleverbot(client, message):
    if message.author.id == client.identity.id:
        return

    mention = '<@{}> '.format(client.identity.id)
    if message.content.startswith(mention):
        raw = message.content[len(mention):].encode('ascii', 'ignore')
        response = cb.ask(raw)

        if response:
            client.messages.put(message.channel_id, '<@{}> {}'.format(message.author.id, response))


client.register_event_listener(EVENT_MESSAGE_CREATE, infix)


def on_report(headers, body):
    headers[u'X-Report-Type'] = headers[u'X-Report-Type'].title()
    headers[u'X-Description'] = urllib.unquote_plus(headers[u'X-Description'])

    template = u':mega: <@&230225829072863234> ***{{X-Report-Type}}*** from *{{X-Reporter}}*{}\n```{{X-Description}}```'

    if u'X-Offender' in headers:
        message = template.format(u' about *{X-Offender}*:')
    else:
        message = template.format(u':')

    client.messages.put('212643087959195649', message.format(**headers))

report_checker = EmailChecker('vorty@g4p.org', 'le80IpMIiw', 'mail.g4p.org', on_mail=on_report, interval=60, delete=True)
report_checker.start()


import schedule


def restart_warning():
    client.messages.put('212643087959195649', '<@&230225829072863234> :clock1: Restart required in 10 minutes!')


def restart_now():
    client.messages.put('212643087959195649', '<@&230225829072863234> :clock1: Restart required NOW!')

# TODO: Timezone
schedule.every().thursday.at('00:50').do(restart_warning)
schedule.every().sunday.at('00:50').do(restart_warning)

schedule.every().thursday.at('01:00').do(restart_now)
schedule.every().sunday.at('01:00').do(restart_now)


schedule_timer = Timer(target=schedule.run_pending)
schedule_timer.start()


with client:
    client.run()


report_checker.stop()
database.commit()
