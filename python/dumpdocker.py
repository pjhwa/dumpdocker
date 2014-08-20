#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
Created on 2014. 8. 19.

@author: earthsea
'''

from os.path import realpath,isfile
from optparse import OptionParser
from time import localtime
from socket import gethostname
from subprocess import Popen,PIPE
import sys,tarfile

def isthere(cmd,must):
    try :
        ret = Popen("which %s"%cmd,stdout=PIPE,stderr=open("/dev/null"))
        
        return realpath(ret.PIPE.read())
    except IOError as Ierr :
        sys.stderr.write("%s not found : "%cmd+str(Ierr)+"\n")
        if must :
            sys.exit(2)

def pkgthere(cmd):
    try :
        ret = Popen("%s"%cmd,stdout=PIPE,stderr=open("/dev/null"))
        return realpath(ret.PIPE.read())
    except IOError as Ierr :
        sys.stderr.write("%s not found : "%cmd+str(Ierr)+"\n")
    
def findLib(whereldd,cmd):
    try :
        ret = Popen("%s %s"%(whereldd,cmd),stdout=PIPE,stderr=open("/dev/null"))
        sharedList = []
        for line in ret.PIPE.read() :
            if line.find("/") :
                if line.find("=>") :
                    sharedList.append(realpath(line.split("=>")[1]))
                else :
                    sharedList.append(realpath(line))
        return sharedList
    except IOError as Ierr :
        sys.stderr.write("%s not found : "%cmd+str(Ierr)+"\n")
    
if __name__ == '__main__':

    now = localtime()
    DATE = now.tm_year+now.tm_mon+now.tm_mday+now.tm_hour+now.tm_min
    uname = gethostname()
    
    # option 처리 부분
    use_desc ="%prog [-h] -c corefile exec_binary "
    parser = OptionParser(usage=use_desc)
    parser.add_option("-c",help="core file",dest="corefile")
    (options, args) = parser.parse_args()
    corefile = options.corefile
    execfile = args[0]

    if not (len(args) == 1 and corefile) :
        parser.print_help()
        sys.exit(1)
    
    if not isfile(execfile) :
        sys.stderr.write("%s : please input correct executable binary as exec_binary\n" %execfile)
        parser.print_help()
        sys.exit(2)
    
    if not isfile(corefile) :
        sys.stderr.write("%s : please input correct corefile as corefile\n" %options.corefile)
        parser.print_help()
        sys.exit(2)        
    
    musthave_cmdList = ["gdb","ldd","xargs","tar","strace"]
    whereCmd = {}
    for cmd in musthave_cmdList :
        whereCmd[cmd] = isthere(cmd,1)

    retgdb = Popen("%s %s %s -x gdb.cmd"%(whereCmd["gdb"],execfile,corefile),stdout=PIPE,stderr=open("/dev/null")).PIPE.read()
    sharedlibs =  [ realpath(line) for line in retgdb if line.find(" /") ]
        
    util_cmdList = ["bash","ls","cp","grep","cat","diff","tail","head","vi","bc" ]
    for cmd in util_cmdList :
        whereCmd[cmd] = isthere(cmd,0)
        sharedlibs.extend(findLib(whereCmd["ldd"],whereCmd[cmd]))
        
    pkg_cmdList = ["dpkg","rpm"]
    for cmd in pkg_cmdList :
        whereCmd[cmd] = isthere(cmd,1)
        if cmd == "dpkg" :
            dpkg_ret = pkgthere("%s -L gdb"%whereCmd[cmd])
            for line in dpkg_ret :
                sharedlibs.append(line)
        elif cmd == "rpm" :
            rpm_ret = pkgthere("%s -qvl gdb"%whereCmd[cmd])
            for line in rpm_ret :
                sharedlibs.append(line.split()[9])
    if not (dpkg_ret or rpm_ret) :
        print("Couldn't find gdb package.")
        sys.exit(2)
        
    
    for line in pkgthere("%s gdb -h"%whereCmd['strace']) :
        if line.find('^open(\"/)') :
            if line.find('no such file') != -1 and line.find('\tmp') != -1 and line.find('\proc') != -1 and line.find('\dev') != -1 :
                sharedlibs.append(line.split('"')[1])
     
    myset = set(sharedlibs)
    tf = tarfile.open("%s.%s.%s.tar.gz"%(uname,execfile,DATE),"w|gz")
    for line in myset :
        tf.add(line)
    
    tf.close()
    # ret = Popen("xargs tar cvf %s.%s.%s.tar"%(uname,execfile,DATE),stdin=myset)  
    
    pass
