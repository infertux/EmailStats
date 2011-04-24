#!/usr/bin/env python
# -*- coding: utf-8 -*-

import EmailStats
from math import log10

if __name__ == '__main__':
    stats = EmailStats.EmailStats()
    stats.connect('mail.example.net')
    stats.login('you@example.net', bytes('!Y0uRS7r0nGP455@', 'ASCII'))

    print("Mailboxes:", ", ".join(stats.getMailboxes()))
    print(stats.getCount(), "emails in inbox")
    quota = stats.getQuota()
    if not quota:
        print("Quota unavailable", file=sys.stderr)
    else:
        used, total = quota
        print("Quota: ", used, "/", total, " KiB (",
            round(used / total) * 100, "% used)", sep='')

    nElements = 10
    # filter only messages containing '[WORK]' in the subject
    s = stats.getStats(['INBOX', 'Archives'], r'.*\[WORK\].*', nElements)

    print()
    print(s['total'], "messages match")

    # display only most common messages
    print("\nThe ", nElements, " biggest trolls:\n",
          "-" * (int(log10(nElements)) + 21), sep='')

    for msg in s['subjects']:
        subjects = '"' + '"\n  aka "'.join(msg['subjects']) + '"'
        print(subjects, ": ", msg['amount'], " messages (",
            round(float(msg['amount']) / s['total'] * 100), "%)" , sep='')

    print("\nThe ", nElements, " biggest spammers:\n",
          "-" * (int(log10(nElements)) + 23), sep="")

    for msg in s['froms']:
        froms = " aka ".join(msg['froms'])
        print(froms, ": ", msg['amount'], " messages (",
            round(float(msg['amount']) / s['total'] * 100), "%)" , sep='')

    stats.logout()


# you should get an output like this:

"""
Mailboxes: INBOX, Archives, Drafts, INBOX.URGENT, Junk, Sent, Trash
4460 emails in inbox
Quota: 285630/1048576 KiB (27% used)

1648 messages match

The 10 biggest trolls:
----------------------
"[WORK] [Latin] Lorem ipsum dolor sit amet"
  aka "[WORK] consectetur adipiscing elit"
  aka "[WORK] Phasellus non elit odio": 61 messages (4%)
"[WORK] Maecenas sit amet lectus ?": 39 messages (2%)
"[WORK] quis metus feugiat vehicula vel in ante": 38 messages (2%)
"[WORK] Sed vitae erat purus": 36 messages (2%)
"[WORK] Morbi porta nisi sed": 31 messages (2%)
"[WORK] mi feugiat ultrices faucibus"
  aka "[WORK] metus consequat": 28 messages (2%)
"[WORK] Nunc ultricies": 26 messages (2%)
"[WORK] sem vel vulputate rutrum": 25 messages (2%)
"[WORK] quam elit commodo magna": 23 messages (1%)
"[WORK] [URGENT] et vestibulum urna": 23 messages (1%)

The 10 biggest spammers:
------------------------
Russian Bot <dsgfgzececq@z.smjdfks.efjzkmzzz.ru>: 265 messages (16%)
Your Boss <your-boss@yourperfectcompany.com>: 98 messages (6%)
Donec Sit <donec.sit@googlemail.com>: 95 messages (6%)
Donec Mollis <Donec Mollis@gmail.com>: 73 messages (4%)
sapien007 <sapien007@hotmail.com>: 60 messages (4%)
dolor sed venenatis <dsv@your.isp>: 60 messages (4%)
arcu convallis <abcdef@abcdef.com>: 54 messages (3%)
Nagios <nagios@yourb0x.edu>: 53 messages (3%)
Monit <monit@yourb0x.edu>: 50 messages (3%)
AAA <a3@gmail.com>: 47 messages (3%)
"""

