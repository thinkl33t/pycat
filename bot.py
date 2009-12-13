#!/usr/bin/python

import asynchat
import asyncore
import logging
import re
import socket
import sys

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")

class Bot(asynchat.async_chat):
    config = {
        'nick': 'adamcik-bot',
        'username': 'adamcik',
        'hostname': socket.getfqdn(),
        'servername': socket.getfqdn(),
        'realname': 'adamcik',
        'channel': '#adamcik-test',
    }

    logger = logging.getLogger()

    def __init__(self, server, port=6667):
        asynchat.async_chat.__init__(self)

        self.server = server
        self.port = port

        self.buffer = ''
        self.handlers = {}

        self.set_terminator("\r\n")

        self.add('PING', self.irc_pong)
        self.add('CONNECT', self.irc_register)

    def run(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.server, self.port))

        asyncore.loop()

    def add(self, command, handler):
        if command not in self.handlers:
            self.handlers[command] = []

        self.handlers[command].append(handler)

    def irc_pong(self, prefix, command, args):
        self.write('PONG', args[0])

    def handle_command(self, prefix, command, args):
        for handler in self.handlers.get(command, []):
            handler(prefix, command, args)

    def handle_connect(self):
        self.logger.info('Connected to server')

        self.handle_command(self.server, 'CONNECT', '')

    def irc_register(self, prefix, command, args):
        self.write('NICK', self.config['nick'])
        self.write('USER', '%(username)s %(hostname)s %(servername)s :%(realname)s' % self.config)


    def parse_line(self, line):
        prefix = ''

        if line.startswith(':'):
            prefix, line = re.split(' +', line[1:],  1)

        if ' :' in line:
            line, trailing = re.split(' +:', line, 1)
            args = re.split(' +', line)
            args.append(trailing)
        else:
            args = re.split(' +', line)

        command = args.pop(0)

        return prefix, command, args

    def collect_incoming_data(self, data):
        self.buffer += data

    def found_terminator(self):
        line, self.buffer = self.buffer, ''

        try:
            line = line.decode('utf-8')
        except UnicodeDecodeError:
            line = line.decode('iso-8859-1')

        self.logger.debug('Recieved: %s', line)

        prefix, command, args = self.parse_line(line)

        self.handle_command(prefix, command, args)

    def write(self, *args):
        line = ' '.join(args)

        self.logger.debug('Sending: %s', line)

        self.push(line + '\r\n')

b = Bot('localhost')

try:
    b.run()
except KeyboardInterrupt:
    b.write('QUIT', 'Bye :)')
    sys.exit(0)
