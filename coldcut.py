#!/usr/local/bin/python -*- Mode: Python; tab-width: 4 -*-

'''coldcut v 0.2 - a bulk scanner for certain ESMTP Features

coldcut reads hostnames (or better IP addresses) from stdin.  It tries
to connect the hosts on port 25, issue an EHLO command and then a
QUIT. Im a certain ESMTP feature is present at the host it outputs its
IP.

By using the excellent medusa framework coldcut is able to scan
several hounderd hosts at once - if your OS can handle this.

For further enlightment on ESMTP see RFC 1869 (SMTP Service Extensions).

python coldcut.py < List

--drt http://un.bewaff.net/ out of the c0re'''

version = '$Id: coldcut.py,v 1.1 2001/07/07 12:35:21 drt Exp $'

# search for this ESMTP Feature
searchextension = '8BITMIME'

# the name we use for identifying ourselfs in EHLO
myheloname = 'tlstest.koeln.ccc.de'

# max time we wait for a sucessfull data gathering process
timeout = 30

# number of concurrent querys this might be limited by your OS
# Win 95: 55, Linux 2.0: 245, Linux 2.2: 1000
# FreeBSD, NT: 1000; can be tweaked for more.
concurrency = 245

import sys
import socket
import time
import select
import asyncore
import asynchat

def monitor():
    '''open new connenctions until we reach concurrency'''

    while len(asyncore.socket_map) < concurrency:
        line = sys.stdin.readline()
        if line[-1:] == '\n':
            line = line [:-1]
        if line != '':
            s = smtpscan(line)
        else:
            break

    # work_in_progress/reaper.py
    # 'bring out your dead, <CLANG!>... bring out your dead!'
    now = int(time.time())
    for x in asyncore.socket_map.keys():
        s =  asyncore.socket_map[x]
        if hasattr(s, 'timestamp'):
            if (now - s.timestamp) > timeout:
                print >>sys.stdout, 'reaping connection to', s.host
                s.close()

def loop():
    '''loop over our sockets and monitor connections'''

    if hasattr (select, 'poll') and hasattr (asyncore, 'poll3'):
        poll_fun = asyncore.poll3
    else:
        poll_fun = asyncore.poll

    while asyncore.socket_map:
        monitor()
        poll_fun(30.0, asyncore.socket_map)
        
                    
class smtpscan (asynchat.async_chat):
    '''class implementing the actual scan'''
    
    def __init__ (self, address):
        '''constuctor - opens connection'''
        asynchat.async_chat.__init__ (self)
        self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
        self.set_terminator ('\r\n')
        self.buffer = ''
        self.host = address
        self.timestamp = int(time.time())
        try:
            self.connect((address, 25))
        except:
            self.handle_error()
            self.close()


    def handle_connect(self):
        '''we have successfull connected'''

        # ... and ignore this fact
        pass
               

    def handle_error(self):
        '''print out error information to stderr'''
        
        print >>sys.stderr, self.host, sys.exc_info()[1]

    
    def collect_incoming_data (self, data):
        '''collect data which was recived on the socket'''
        
        self.buffer = self.buffer + data
      
    def found_terminator (self):
        '''we have read a whole line and devcide what do do next'''

        data = self.buffer
        self.buffer = ''
        # Check for various States in the Server
        if data[:4] == '220 ':
            # We are asked vor EHLO
            self.push('EHLO %s\r\n' % (myheloname))
        elif data[:3] == '250' and data[4:].upper() == searchextension:
            # there is EHLO response withe th feature we are looking for. 
            (host, port) = self.getpeername()
            print host
        elif data[4] == '-':
            # continuation lines are ignored
            pass
        else:
            self.push('QUIT\r\n')


    def handle_close (self):
        '''when the connection is closed use monitor() to start new connections'''
        
        self.close()
        monitor()
               

# "main"

# use monitor() to fire up the number of connections we want
monitor()
# handle all the connection stuff
loop()


