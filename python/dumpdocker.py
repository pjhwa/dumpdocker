
#!/usr/bin/python
#
#
# dumpdocker
# - creates docker image based on tar file for analysis of crash dump 
# 
# Requirements:
# - gdb,ldd,tar,strace
#
# Usage:
# dumpdocker [-h] -c core_file exec_bin 
#
# Author: ChongHwa Lee <earthsea@gmail.com>
# Created on Mon Aug  18 11:23:32 KST 2014
# Last updated at Tue Aug  26 14:35:29 KST 2014
#
#
# -*- coding:utf-8 -*-

from os.path import isfile,islink,realpath,basename
from optparse import OptionParser
from time import localtime,strftime
from socket import gethostname
from subprocess import Popen,PIPE
import sys,tarfile

def exeComm(cmd,std):
    try :
        retline = []
        cmdList = cmd.split()
        if std == 1 :
            ret = Popen(cmdList,stdout=PIPE,stderr=open("/dev/null")).stdout
        elif std == 2 :
            ret = Popen(cmdList,stderr=PIPE,stdout=open("/dev/null")).stderr
        for x in ret.readlines() :
            retline.append(x.strip('\t').strip('\n'))
        return retline
    except IOError as Ierr :
        sys.stderr.write("%s not found : "%cmd+str(Ierr)+"\n")
        
def isthere(cmd):
    path = ''
    ret = exeComm('which %s'%cmd,1)
    for line in ret :
        if isfile(line) :
            path = realpath(line)        
    return path

def makeSharedLibs(path):
    retline = []
    if isfile(path) :
        retline.append(realpath(path))
    if islink(path) :
        retline.append(path)    
    return retline
     
if __name__ == '__main__':

    DATE = strftime('%Y%m%d%H%M',localtime())
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
    
    # 명령어 위치정보 dictionary
    whereCmd = {}
    # SharedLib list
    sharedlibs = []
    
    # 반드시 필요한 명령어 위치 산출. 없으면 종료.
    musthave_cmdList = ["gdb","ldd","tar","strace"]
    
    for cmd in musthave_cmdList :
        whereCmd[cmd] = isthere(cmd)
    if len(whereCmd) != len(musthave_cmdList) :
        sys.stderr.write("Please Check gdb,ldd,xargs,tar,strace Command")
        sys.exit(2)
        
    # gdb 라이브러리 산출
    retgdb = exeComm('%s %s %s -x gdb.cmd'%(whereCmd['gdb'],execfile,corefile),1)
    for line in retgdb :
        if line.find(" /") != -1 and line.startswith('0x') :
            gdbRaw = line.split()[-1]
            sharedlibs.extend(makeSharedLibs(gdbRaw))    
    
    # 일반 명령어 라이브러리와 바이너리      
    util_cmdList = ["bash","ls","cp","grep","cat","diff","tail","head","vi","bc" ]
    for cmd in util_cmdList :
        whereCmd[cmd] = isthere(cmd)
        sharedlibs.append(whereCmd[cmd])
        retldd = exeComm('%s %s'%(whereCmd['ldd'],whereCmd[cmd]),1)
        for line in retldd :
            if line.find(" /") != -1 :
                lddRaw = realpath(line.split()[-2])
                sharedlibs.extend(makeSharedLibs(lddRaw))
        
    pkg_cmdList = ["dpkg","rpm"]
    for cmd in pkg_cmdList :
        whereCmd[cmd] = isthere(cmd)
        if whereCmd[cmd] :
            if cmd == "dpkg" :
                retpkg = exeComm('%s -L gdb'%whereCmd[cmd],1)
                for line in retpkg :
                    sharedlibs.extend(makeSharedLibs(line))
            elif cmd == "rpm" :
                retpkg =  exeComm('%s -qvl gdb'%whereCmd[cmd],1)
                for line in retpkg :
                    lineRaw = line.split()[8]
                    sharedlibs.extend(makeSharedLibs(lineRaw))                 
    if not retpkg :
        sys.stderr.write("Couldn't find dpkg or RPM package.")
        sys.exit(2)

    # strace 처리 부분
    retstrace = exeComm('%s gdb -h'%whereCmd['strace'],2)
    for line in retstrace :
        if line.startswith('open("/') :
            retline = line.strip('\n')
            if (retline.find(' ENOENT ') == -1  and retline.find(' ENOTDIR ') == -1 and retline.find('/tmp/') == -1 and retline.find('/proc/') == -1 and retline.find('/dev/') == -1) :
                straceRaw = retline.split('"')[1]
                sharedlibs.extend(makeSharedLibs(straceRaw))
     
    myset = set(sharedlibs)

    tf = tarfile.open("%s.%s.%s.tar.gz"%(uname,basename(execfile),DATE),"w|gz")
    for line in myset :
        tf.add(line)
    tf.close()
    
    pass
