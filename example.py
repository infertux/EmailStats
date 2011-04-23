#!/usr/bin/env python
# -*- coding: utf-8 -*-

from EmailStats import EmailStats

if __name__ == '__main__':
    stats = EmailStats()
    stats.connect('mail.example.net')
    stats.login('you@example.net', bytes('!Y0uRS7r0nGP455@', 'ASCII'))
    stats.printMailboxes()
    stats.printQuota()
    stats.printStats(['INBOX', 'Archives'], r'.*\[work\].*', 10)
    print()
    stats.printStats()

    stats.logout()

