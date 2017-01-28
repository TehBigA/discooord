import poplib

from ...utils import Timer


class EmailChecker(Timer):
    '''WARNING: This uses POP3 and by default deletes the emails it reads!'''

    username = None
    password = None
    server = None
    port = None

    on_mail = None
    delete = None

    def __init__(self, username, password, server, port=110, on_mail=None, delete=True, interval=60):
        super(EmailChecker, self).__init__(interval=interval)

        self.username = username
        self.password = password
        self.server = server
        self.port = port

        if on_mail is not None:
            self.on_mail = on_mail

        self.delete = delete

    def target(self):
        client = poplib.POP3(self.server, self.port)
        client.user(self.username)
        client.pass_(self.password)

        count = client.stat()[0]

        for i in range(count):
            email = client.retr(i + 1)
            data = [l.decode('utf-8') for l in email[1]]

            sep = data.index(u'')

            headers = {}
            body = u''

            # Headers
            last = None
            for line in data[:sep]:
                if line[0] in (u' ', u'\t', u'\r', u'\n') and last is not None:
                    # Folded header continuation
                    headers[last] += line
                else:
                    # Next header
                    name_separator = line.index(u':')

                    name = line[:name_separator]
                    value = line[name_separator + 2:]

                    headers[name] = value

                    last = name

            # Body
            body = u''.join(data[sep + 1:])

            if self.on_mail(headers, body) or self.delete:
                client.dele(i + 1)

        client.quit()

    def on_exception(self):
        '''Sometimes the mail server doesn't respond in time, ignore the produced error and keep running.'''
        return False
