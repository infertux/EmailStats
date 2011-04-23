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
from math import log10


class EmailStats:
    """Just a few statistics with your emails (IMAP only)"""

    def connect(self, host, ssl = True, port = None):
        if port == None:
            port = 993 if ssl else 143

        self._con = imaplib.IMAP4_SSL(host, port) if ssl else imaplib.IMAP4(host, port)

    def login(self, username, password):
        try:
            status, data = self._con.login(username, password)
        except imaplib.IMAP4.error as e:
            self._con.logout()
            raise

    def printMailboxes(self):
        status, mailboxes = self._con.list()
        boxes = []
        for mailbox in sorted(mailboxes):
            name = re.findall(r'"([^"]+)"', str(mailbox))[-1]
            boxes.append(name)

        print("Mailboxes:", ", ".join(boxes))

    def printQuota(self, mailbox = 'INBOX'):
        # Select the right mailbox first (in read-only mode)
        status, count = self._con.select(mailbox, True)
        count = int(count[0])
        print(count, ' emails in mailbox "', mailbox, '":', sep="")

        # Get quota
        status, quota = self._con.getquota('user')
        quota = re.search('\(STORAGE (\d+) (\d+)\)', str(quota))
        if quota == None:
            print("Quota unavailaible!", file=sys.stderr)
        else:
            print("Quota: ", quota.group(1), "/", quota.group(2), "KB (",
            round(int(quota.group(1)) / int(quota.group(2)) * 100), "% used)",
            sep="")

    def printStats(self, mailboxes = ['INBOX'], subjectFilter='', minAmount=8):
        if not isinstance(mailboxes, list):
            raise TypeError("mailboxes parameter must be a list")

        messages = []
        for mailbox in mailboxes:
            status, count = self._con.select(mailbox, True)

            # Get all emails
            status, emails_ids = self._con.search(None, 'ALL')
            # Build a comma-separed list
            emails_ids = emails_ids[0].decode().replace(' ', ',')
            # Fetch all subjects ('PEEK' avoids to mark email as read)
            status, emails = self._con.fetch(emails_ids,
                '(UID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])')

            # Get *only* useful content
            messages.extend([email[1] for email in emails
                if isinstance(email, tuple)])

        # Strip and parse headers
        parsed_subjects = []
        parsed_senders = []
        for message in messages:
            #print(message)
            headers = message.decode('utf-8', 'replace').rstrip("\r\n")
            headers = re.compile("\r\n([a-zA-Z0-9_-]+):"). \
                split("\r\n" + headers)[1:]
            #print(headers)
            # Headers are optional so we init them empty
            sender = subject = ""
            for i in range(0, len(headers), 2):
                header, value = headers[i], headers[i+1].strip()
                #print(header.upper())
                if header.upper() == 'FROM':
                    sender = value
                elif header.upper() == 'SUBJECT':
                    subject = value
                else:
                    raise ValueError("Unknown header: " + header)

            # remove "R{e,E}: " to count the initial message in the thread
            subject = self._decodeHeader(
                subject.replace('Re: ', '').replace('RE: ', ''))
            # Filter only matching subjects
            if not re.match(subjectFilter, subject):
                #print("Ignored:", subject)
                continue

            #print("Matched:", subject)
            parsed_subjects.append(subject)

            sender = self._decodeHeader(sender)
            parsed_senders.append(sender)

        subjects = parsed_subjects
        senders = parsed_senders

        if subjectFilter != "":
            print("Filter:", subjectFilter)

        print(len(subjects), "messages match")

        # Display only most common messages
        print("\nThe ", minAmount, " biggest trolls:\n",
              "-" * (int(log10(minAmount)) + 21), sep="")
        biggestSubjects = collections.Counter(subjects).most_common(minAmount)
        for subject, amount in biggestSubjects:
            print(subject, ': ', amount, " messages (",
            round(float(amount)/len(subjects) * 100), "%)" , sep="")

        print("\nThe ", minAmount, " biggest spammers:\n",
              "-" * (int(log10(minAmount)) + 23), sep="")
        biggestSenders = collections.Counter(senders).most_common(minAmount)
        for sender, amount in biggestSenders:
            print(sender, ': ', amount, " messages (",
            round(float(amount)/len(senders) * 100), "%)" , sep="")

    def logout(self):
        self._con.close()
        self._con.logout()


    def _decodeHeader(self, header):
        header = header.split(': ', 1)[-1]
        decoded_header = decode_header(header)
        header = ""
        for (part,encoding) in decoded_header:
            if isinstance(part, str):
                header += part + " "
            elif encoding != None:
                header += part.decode(encoding) + " "
            else:
                header += part.decode() + " "

        return header.rstrip(" ")


