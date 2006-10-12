"""
Enables the "cobbler enchant" command to apply profiles
to remote systems, whether or not they are running koan.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import cexceptions
import os
import os.path
import pexpect
import pxssh
import traceback

class Enchant:

   def __init__(self,config,sysname,password=''):
       """
       Constructor.  If password is None it should rely on SSH key auth.
       """
       self.config = config
       self.settings = self.config.settings()
       self.username = "root"
       self.sysname = sysname
       if sysname is None:
           raise cexception.CobblerException("enchant_failed","no system name specified")
       self.profile = ''
       self.password = password
 
   def call(self,cmd):
       """
       Invoke something over SSH.
       """
       print "ssh -> %s" % cmd
       self.ssh.sendline(cmd)
       self.ssh.prompt()

   def run(self):
       """
       Replace the OS of a remote system.
       """
       koan = os.path.basename(self.settings.koan_path)
       sys  = self.config.systems().find(self.sysname)
       if sys is None:
           raise cexceptions.CobblerException("enchant_failed","system not in cobbler database")
       pro  = self.config.profiles().find(sys.profile)
       self.profile = pro.name
       if pro is None:
           raise cexceptions.CobblerException("enchant_failed","no such profile for system (%s): %s" % (self.sysname, self.profile))
       where_is_koan = os.path.join(self.settings.webdir,os.path.basename(koan))
       if not os.path.exists(where_is_koan):
           raise cexceptions.CobblerException("enchant_failed","koan is missing")

       try:
           ssh = self.ssh = pxssh.pxssh()
           if not ssh.login(self.sysname, self.username, self.password):
               raise cexceptions.CobblerException("enchant_failed","SSH login denied")
           else:
               self.call("wget http://%s/cobbler/%s" % (self.settings.server, koan))
               # nodeps allows installation on Centos 4 with python 2.3
               # RHEL4 won't work due to urlgrabber
               self.call("rpm -Uvh %s --force --nodeps" % koan)
               self.call("koan --replace-self --profile=%s --server=%s" % (self.profile, self.settings.server))
               #self.call("/sbin/reboot")
               return True
       except:
           traceback.print_exc()
           raise cexceptions.CobblerException("enchant_failed","exception")
       return False # shouldn't be here

