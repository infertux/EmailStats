# A small Python 3 library to make statistics of your inbox
# Copyright (C) 2011  Infertux <infertux@infertux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from sys import version_info
if version_info[0] < 3:
    raise EnvironmentError("Must use Python 3 or greater")


import imaplib, re, collections
from email.header import decode_header
from email.parser import HeaderParser


class EmailStats:
    """Just a few statistics with your emails
    This library should be safe to use because it connects in read-only mode
    to the IMAP account.
    """

    def connect(self, host, ssl = True, port = None):
        """Connect to the given host:port in IMAP[S]"""
        if port == None:
            port = 993 if ssl else 143

        self._con = imaplib.IMAP4_SSL(host, port) if ssl \
            else imaplib.IMAP4(host, port)

    def login(self, username, password):
        """Try to login"""
        try:
            status, data = self._con.login(username, password)
        except imaplib.IMAP4.error as e:
            self._con.logout()
            raise

    def getMailboxes(self):
        """Return a list of available mailboxes"""
        status, mailboxes = self._con.list()
        boxes = []
        for mailbox in sorted(mailboxes):
            name = re.findall(r'"([^"]+)"', str(mailbox))[-1]
            boxes.append(name)

        return boxes

    def getCount(self, mailbox = 'INBOX'):
        """Return the count of messages in mailbox"""
        status, count = self._con.select(mailbox, True)
        return int(count[0])

    def getQuota(self, mailbox = 'INBOX'):
        """Return the quota of mailbox
        None if unavailable
        (used, total) otherwise
        """
        # select the right mailbox first (in read-only mode)
        status, dummy = self._con.select(mailbox, True)

        # get quota
        status, quota = self._con.getquota('user')
        quota = re.search('\(STORAGE (\d+) (\d+)\)', str(quota))

        if quota == None:
            return None

        return int(quota.group(1)), int(quota.group(2))

    def getStats(self, mailboxes = ['INBOX'], subjectFilter='', nElements=8):
        """Return a dict containing a lot of information"""
        if not isinstance(mailboxes, list):
            raise TypeError("mailboxes parameter must be a list")

        messages = []
        for mailbox in mailboxes:
            status, count = self._con.select(mailbox, True)

            # get all emails
            status, emails_ids = self._con.search(None, 'ALL')
            # build a comma-separated list
            emails_ids = emails_ids[0].decode().replace(' ', ',')
            # fetch all subjects ('PEEK' avoids to mark email as read)
            status, emails = self._con.fetch(emails_ids,
                '(UID BODY.PEEK[HEADER.FIELDS ' +
                '(MESSAGE-ID FROM SENDER SUBJECT REFERENCES)])')

            # get *only* useful content
            messages.extend([email[1] for email in emails
                if isinstance(email, tuple)])

        msg_ID_subjects = {}
        msg_ID_counter = collections.Counter()
        sender_froms = {}
        sender_counter = collections.Counter()

        for message in messages:
            parser = HeaderParser()
            h = parser.parsestr(message.decode('utf-8', 'replace'))
            # dirty copy because h is read-only
            headers = { 'Subject': h['Subject'],
                        'From': h['From'],
                        'Message-ID': h['Message-ID'],
                        'References': h['References'],
                        'Sender': h['Sender'] }
            del h, parser

            if not headers['From']:
                # skipping uncommunicative message
                continue

            headers['From'] = self._decodeHeader(headers['From'])

            if not headers['Subject']:
                headers['Subject'] = ''

            headers['Subject'] = self._decodeHeader(headers['Subject'])

            # filter only matching subjects
            if not re.match(subjectFilter, headers['Subject']):
                # ignore this message
                continue

            # remove Re and Fwd
            headers['Subject'] = re.sub(r'^(Re: |Fwd: )+', '',
                headers['Subject'], 0, re.IGNORECASE)

            if not headers['Sender']:
                headers['Sender'] = headers['From']

            if headers['References']:
                # expect the first id is the first email of the thread
                thread_id = headers['References'].split()[0]
            else:
                thread_id = headers['Message-ID']

            msg_ID_subjects[thread_id] = msg_ID_subjects.get(thread_id, set())
            msg_ID_subjects[thread_id].add(headers['Subject'])

            msg_ID_counter.update([thread_id])

            sender_froms[headers['Sender']] = \
                sender_froms.get(headers['Sender'], set())
            sender_froms[headers['Sender']].add(headers['From'])

            sender_counter.update([headers['Sender']])

        stats = {}
        stats['total'] = sum(msg_ID_counter.values())

        biggest_msg_IDs = msg_ID_counter.most_common(nElements)
        stats['subjects'] = []
        for msg_ID, amount in biggest_msg_IDs:
            stats['subjects'].append({
                'id': msg_ID,
                'subjects': msg_ID_subjects[msg_ID],
                'amount': amount})

        biggest_senders = sender_counter.most_common(nElements)
        stats['froms'] = []
        for sender, amount in biggest_senders:
            stats['froms'].append({
                'id': sender,
                'froms': sender_froms[sender],
                'amount': amount})

        return stats

    def logout(self):
        self._con.close()
        self._con.logout()


    def _decodeHeader(self, header):
        # awful hack because of a Python bug <http://bugs.python.org/issue1079>
        # probably one of the most horrible hacks I've ever done! :shame:
        # if you have another solution, please send a patch :)
        # this hack is optional but you may get undecoded subjects without it
        i = 1
        while re.search('%' * i, header):
            i += 1
            if i > 100:
                raise OverflowError('WTF?!')

        header = re.sub(r'(=\?)(.*)([^\?]{2}\?=)([^ ])',
            r'\1\2\3 ' + ('%' * i) + ' \4', header)

        # well, let's properly decode this header now...
        decoded_header = decode_header(header)
        header = ''
        for (part,encoding) in decoded_header:
            if isinstance(part, str):
                header += part + ' '
            elif encoding != None:
                header += part.decode(encoding) + ' '
            else:
                header += part.decode() + ' '

        header = header.rstrip(' ')

        # awful hack, the end...
        header = header.replace(' ' + ('%' * i) + ' ', '')

        return header

