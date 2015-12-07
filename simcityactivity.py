# -*- mode: python; tab-width: 4 -*-
#
# SimCity, Unix Version.  This game was released for the Unix platform
# in or about 1990 and has been modified for inclusion in the One Laptop
# Per Child program.  Copyright (C) 1989 - 2007 Electronic Arts Inc.  If
# you need assistance with this program, you may contact:
#   http://wiki.laptop.org/go/SimCity  or email  simcity@laptop.org.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.  You should have received a
# copy of the GNU General Public License along with this program.  If
# not, see <http://www.gnu.org/licenses/>.
# 
#             ADDITIONAL TERMS per GNU GPL Section 7
# 
# No trademark or publicity rights are granted.  This license does NOT
# give you any right, title or interest in the trademark SimCity or any
# other Electronic Arts trademark.  You may not distribute any
# modification of this program using the trademark SimCity or claim any
# affliation or association with Electronic Arts Inc. or its employees.
# 
# Any propagation or conveyance of this program must include this
# copyright notice and these terms.
# 
# If you convey this program (or any modifications of it) and assume
# contractual liability for the program to recipients of it, you agree
# to indemnify Electronic Arts for any liability that those contractual
# assumptions impose on Electronic Arts.
# 
# You may not misrepresent the origins of this program; modified
# versions of the program must be marked as such and not identified as
# the original program.
# 
# This disclaimer supplements the one included in the General Public
# License.  TO THE FULLEST EXTENT PERMISSIBLE UNDER APPLICABLE LAW, THIS
# PROGRAM IS PROVIDED TO YOU "AS IS," WITH ALL FAULTS, WITHOUT WARRANTY
# OF ANY KIND, AND YOUR USE IS AT YOUR SOLE RISK.  THE ENTIRE RISK OF
# SATISFACTORY QUALITY AND PERFORMANCE RESIDES WITH YOU.  ELECTRONIC ARTS
# DISCLAIMS ANY AND ALL EXPRESS, IMPLIED OR STATUTORY WARRANTIES,
# INCLUDING IMPLIED WARRANTIES OF MERCHANTABILITY, SATISFACTORY QUALITY,
# FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT OF THIRD PARTY
# RIGHTS, AND WARRANTIES (IF ANY) ARISING FROM A COURSE OF DEALING,
# USAGE, OR TRADE PRACTICE.  ELECTRONIC ARTS DOES NOT WARRANT AGAINST
# INTERFERENCE WITH YOUR ENJOYMENT OF THE PROGRAM; THAT THE PROGRAM WILL
# MEET YOUR REQUIREMENTS; THAT OPERATION OF THE PROGRAM WILL BE
# UNINTERRUPTED OR ERROR-FREE, OR THAT THE PROGRAM WILL BE COMPATIBLE
# WITH THIRD PARTY SOFTWARE OR THAT ANY ERRORS IN THE PROGRAM WILL BE
# CORRECTED.  NO ORAL OR WRITTEN ADVICE PROVIDED BY ELECTRONIC ARTS OR
# ANY AUTHORIZED REPRESENTATIVE SHALL CREATE A WARRANTY.  SOME
# JURISDICTIONS DO NOT ALLOW THE EXCLUSION OF OR LIMITATIONS ON IMPLIED
# WARRANTIES OR THE LIMITATIONS ON THE APPLICABLE STATUTORY RIGHTS OF A
# CONSUMER, SO SOME OR ALL OF THE ABOVE EXCLUSIONS AND LIMITATIONS MAY
# NOT APPLY TO YOU.

import os

import time
import subprocess
import thread
import fcntl

from gettext import gettext as _

from gi.repository import Gtk

from sugar3.activity import activity
from sugar3.activity.activity import get_bundle_path
from sugar3 import profile

from sugar3.presence import presenceservice

WITH_PYGAME = True

try:
    import pygame.mixer
    pygame.mixer.init()

except:
    WITH_PYGAME = False


def QuoteTCL(s):
    return s.replace('"', '\\"')


class SimCityActivity(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle)

        self._handle = handle

        self.set_title(_('SimCity Activity'))
        self.connect('destroy', self._destroy_cb)
        #self.connect('focus-in-event', self._focus_in_cb)
        #self.connect('focus-out-event', self._focus_out_cb)

        self._bundle_path = get_bundle_path()
        
        self.load_libs_dir()

        self.socket = Gtk.Socket()
        self.socket.connect("realize", self._start_all_cb)
        self.set_canvas(self.socket)

        self.show_all()

    def load_libs_dir(self):    
        os.environ['LD_LIBRARY_PATH'] = os.path.join(self._bundle_path, "libs")

    def _start_all_cb(self, widget):
        win = str(self.socket.get_id())

        if (win.endswith("L")):  # L of "Long"
            win = win[:-1]

        command = os.path.join(self._bundle_path, 'SimCity')

        args = [
            command,
            #'-R', win, # Set root window to socket window id
            '-t',      # Interactive tty mode, so we can send it commands.
        ]

        self._process = subprocess.Popen(args,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         close_fds=True,
                                         cwd=self._bundle_path,
                                         preexec_fn=lambda: os.chdir(self._bundle_path))

        self._stdout_thread = thread.start_new(self._stdout_thread_function, ())

        uri = self._handle.uri or ''
        self.send_process('SugarStartUp "' + QuoteTCL(uri) + '"\n')

        nick = profile.get_nick_name() or ''
        self.send_process('SugarNickName "' + QuoteTCL(nick) + '"\n')

    def _stdout_thread_function(self, *args, **keys):
        f = self._process.stdout
        fcntl.fcntl(f.fileno(), fcntl.F_SETFD, 0)

        while True:
            line = 'XXX'
            try:
                line = f.readline()

            except Exception, e:
                break

            line = line.strip()
            if not line:
                continue

            words = line.strip().split(' ')
            command = words[0]
            if command == 'PlaySound':
                self.play_sound(words[1])

            else:
                pass

    def play_sound(self, name):
        fileName = os.path.join(self._bundle_path, 'res/sounds', name.lower() + '.wav')

        if WITH_PYGAME:
            sound = pygame.mixer.Sound(fileName)
            sound.play()

        else:
            print "Can't play sound: " + fileName + " " + str(e)

    def send_process(self, message):
        self._process.stdin.write(message)

    def share(self):
        Activity.share(self)
        self.send_process( 'SugarShare\n')

    def quit_process(self):
        self.send_process('SugarQuit\n')
        time.sleep(10)

    def _destroy_cb(self, window):
        self.quit_process()

    def _focus_in_cb(self, window, event):
        self.send_process('SugarActivate\n')

    def _focus_out_cb(self, window, event):
        self.send_process('SugarDeactivate\n')

