2import SocketServer
import re
import os, stat, os.path, mimetypes, protocols, gopherentry
import handlers, handlers.base
from handlers.dir import DirHandler

def sgn(a):
    """Returns -1 if less than 0, 1 if greater than 0, and 0 if
    equal to zero."""
    if a == 0:
        return 0
    if a < 0:
        return -1
    return 1

def entrycmp(entry1, entry2):
    """This function implements an exact replica of UMN behavior
    GSqsortcmp() behavior."""
    if entry1.getTitle() == None:
        return 1
    if entry2.getTitle() == None:
        return -1

    # Equal numbers or no numbers: sort by title.
    if entry1.getnum() == entry2.getnum():
        return cmp(entry1.getname(), entry2.getname())

    # Same signs: use plain numeric comparison.
    if (sgn(entry1.getnum()) == sgn(entry2.getnum())):
        return cmp(entry1.getnum(), entry2.getnum())

    # Different signs: other comparison.
    if entry1.getnum() > entry2.getnum():
        return -1
    else:
        return 1

class UMNDirHandler(DirHandler):
    """This module strives to be bug-compatible with UMN gopherd."""
    def prepare(self):
        self.linkfiles = []
        DirHandler.prepare(self)
        self.processLinkFiles()
        
    def processLinkFiles(self):
        newfiles = []
        for filename in self.files:
            if filename[0] == '.' and not os.path.isdir(self.fsbase + '/' + filename):
                self.processLinkFile(self.fsbase + '/' + filename)
            else:
                newfiles.append(filename)
        self.files = newfiles

    def processLinkFile(self, filename):
        fd = open(filename, "rt")
        while 1:
            nextstep, entry = self.getLinkItem(fd)
            if entry:
                self.linkfiles.append(entry)
            if nextstep == 'stop':
                break
    
        
    def getLinkItem(self, fd):
        """This is an almost exact clone of UMN's GSfromLink function."""
        entry = GopherEntry(self.entry.selector, self.config)
        nextstep = 'continue'

        done = {'path' : 0, 'type' : 0, 'name' : 0, 'host' : 0, 'port' : 0}
        
        while 1:
            line = fd.readline()
            if not line:
                nextstep = 'stop'
                break
            line = line.strip()

            # Comment.
            if line[0] == '#':
                if done['path']:
                    break
                else:
                    continue

            # Type.
            if line[0:5] == "Type=":
                entry.settype(line[5])
                # FIXME: handle if line[6] is + or ?
                done['type'] = 1
            elif line[0:5] == "Name=":
                entry.setname(line[5:])
                done['name'] = 1
            elif line[0:5] == "Path=":
                # Handle ./: make full path.
                if line[5:7] == './' or line[5:7] == '~/':
                    entry.setselector(self.pathname + "/" + line[7:])
                else:
                    entry.setselector(line[5:])
                done['path'] = 1
            elif line[0:5] == 'Host=':
                if line[5:] != '+':
                    entry.sethost(line[5:])
                done['host'] = 1
            elif line[0:5] == 'Port=':
                if line[5:] != '+':
                    entry.setport(int(line[5:]))
                done['port'] = 1
            elif line[0:5] == 'Numb=':
                entry.setnum(int(line[5:]))
            elif line[0:9] == 'Abstract=' or \
                 line[0:6] == 'Admin=' or \
                 line[0:4] == 'URL=' or \
                 line[0:4] == 'TTL=':
                pass
            else:
                break
            ### FIXME: Handle Abstract, Admin, URL, TTL

        if done['path']:
            return (nextstep, entry)
        return (nextstep, None)
