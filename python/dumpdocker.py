#!/usr/bin/python27
# -*- coding:utf-8 -*-

'''
Created on 2014. 8. 19.

@author: earthsea
'''
from os.path import isfile,isdir,realpath,basename
from optparse import OptionParser
from time import localtime
from socket import gethostname
from subprocess import Popen,PIPE
import sys,tarfile

def isthere(cmd,must):
    try :
        ret = Popen(["which",cmd],stdout=PIPE,stderr=open("/dev/null"))
        realCmd = realpath(ret.stdout.readline().strip('\n'))
        if not isdir(realCmd) :
            return realCmd
    except IOError as Ierr :
        sys.stderr.write("%s not found : "%cmd+str(Ierr)+"\n")
        if must :
            sys.exit(2)

def pkgthere(cmd):
    try :
        libList = []
        ret = Popen(cmd,stdout=PIPE,stderr=open("/dev/null"))
        for retline in ret.stdout.readlines() :
            libList.append(retline.strip('\t').strip('\n'))
        return libList
    except IOError as Ierr :
        sys.stderr.write("%s not found : "%cmd+str(Ierr)+"\n")
    
def findLib(whereldd,cmd):
    try :
        sharedList = []
        ret = Popen([whereldd,cmd],stdout=PIPE,stderr=open("/dev/null"))
        for retline in ret.stdout.readlines() :
            line = retline.strip('\t').strip('\n')
            if line.find("/") != -1 :
                sharedList.append(realpath(line.split(' ')[-2]))
        return sharedList
    except IOError as Ierr :
        sys.stderr.write("%s not found : "%cmd+str(Ierr)+"\n")
    
if __name__ == '__main__':

    now = localtime()
    DATE = str(now.tm_year)+str(now.tm_mon)+str(now.tm_mday)+str(now.tm_hour)+str(now.tm_min)
    uname = gethostname()
    
    # option 처리 부분
    use_desc ="%prog [-h] -c corefile exec_binary "
    parser = OptionParser(usage=use_desc)
    parser.add_option("-c",help="core file",dest="corefile")
    (options, args) = parser.parse_args()
    corefile = options.corefile

    if not (len(args) == 1 and corefile) :
        parser.print_help()
        sys.exit(1)

    execfile = args[0]
    
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
        
    retgdb = Popen([whereCmd['gdb'],execfile,corefile,'-x','gdb.cmd'],stdout=PIPE,stderr=open("/dev/null")).stdout.readlines() 
   
    sharedlibs =  [ realpath(line.strip('\n').split(' ')[-1]) for line in retgdb if line.find(" /") != -1 and line.startswith('0x') ]
        
    util_cmdList = ["bash","ls","cp","grep","cat","diff","tail","head","vi","bc" ]
    for cmd in util_cmdList :
        whereCmd[cmd] = isthere(cmd,0)
        sharedlibs.extend(findLib(whereCmd['ldd'],whereCmd[cmd]))
        
    pkg_cmdList = ["dpkg","rpm"]
    for cmd in pkg_cmdList :
        whereCmd[cmd] = isthere(cmd,1)
        if whereCmd[cmd] :
            if cmd == "dpkg" :
                pkgList = pkgthere([whereCmd[cmd],'-L','gdb'])
                for line in pkgList :
                    sharedlibs.append(realpath(line))
            elif cmd == "rpm" :
                pkgList = pkgthere([whereCmd[cmd],'-qvl','gdb'])
                for line in pkgList :
                    sharedlibs.append(realpath(line.split()[8]))
    if not pkgList :
        print("Couldn't find gdb package.")
        sys.exit(2)
        
    retstrace = Popen([whereCmd['strace'],'gdb','-h'],stdout=open('/dev/null'),stderr=PIPE).stderr.readlines()
    
    for line in retstrace :
        if line.startswith('open("/') :
            retline = line.strip('\n')
            if (retline.find(' ENOENT ') == -1  and retline.find(' ENOTDIR ') == -1 and retline.find('/tmp/') == -1 and retline.find('/proc/') == -1 and retline.find('/dev/') == -1) :
                sharedlibs.append(realpath(retline.split('"')[1]))
     
    myset = set(sharedlibs)

    tf = tarfile.open("%s.%s.%s.tar"%(uname,basename(execfile),DATE),"w")
    for line in myset :
        if isfile(line) :
            tf.add(line)
    
    tf.close()
    
    pass
