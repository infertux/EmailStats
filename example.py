#!/usr/bin/env python
# -*- coding: utf-8 -*-

from EmailStats import EmailStats
from math import log10

if __name__ == '__main__':
    stats = EmailStats()
    stats.connect('mail.example.net')
    stats.login('you@example.net', bytes('!Y0uRS7r0nGP455@', 'ASCII'))

    print("Mailboxes:", ", ".join(stats.getMailboxes()))
    print(stats.getCount(), "emails in mailbox")
    quota = stats.getQuota()
    if not quota:
        print("Quota unavailaible!", file=sys.stderr)
    else:
        used, total = quota
        print("Quota: ", used, "/", total, " KiB (",
            round(used / total) * 100, "% used)", sep="")

    nElements = 10
    # filter only messages containing '[work]' in the subject
    s = stats.getStats(['INBOX', 'Archives'], r'.*\[work\].*', nElements)

    print(s['total'], "messages")

    # display only most common messages
    print("\nThe ", nElements, " biggest trolls:\n",
          "-" * (int(log10(nElements)) + 21), sep="")

    for msg in s['subjects']:
        subjects = '"' + '"\n  aka "'.join(msg['subjects']) + '"'
        print(subjects, ': ', msg['amount'], " messages (",
            round(float(msg['amount']) / s['total'] * 100), "%)" , sep="")

    print("\nThe ", nElements, " biggest spammers:\n",
          "-" * (int(log10(nElements)) + 23), sep="")

    for msg in s['froms']:
        froms = ' aka '.join(msg['froms'])
        print(froms, ': ', msg['amount'], " messages (",
            round(float(msg['amount']) / s['total'] * 100), "%)" , sep="")

    stats.logout()

