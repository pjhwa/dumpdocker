#!/usr/bin/python27
# -*- coding:utf-8 -*-

'''
Created on 2014. 8. 19.

@author: earthsea
'''
from os.path import isfile,realpath,basename
from optparse import OptionParser
from time import localtime,strftime
from socket import gethostname
from subprocess import Popen,PIPE
import sys,tarfile

'''            
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

def findLib(whereldd,cmd):
    path = []
    ret = exeComm('%s %s'%(whereldd,cmd),1)
    for line in ret :
        if line.find(" /") != -1 :
            pathRaw = realpath(line.split()[-2])
            if isfile(pathRaw) :
                path.append(pathRaw)
    return path


'''
def exeComm(cmd,std):
    try :
        retline = []
        cmdList = cmd.split()
        if std == 1 :
            ret = Popen(cmdList,stdout=PIPE,stderr=open("/dev/null")).stout
        elif std == 2 :
            ret = Popen(cmdList,stderr=PIPE,stdout=open("/dev/null")).sterr
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
    musthave_cmdList = ["gdb","ldd","xargs","tar","strace"]
    
    for cmd in musthave_cmdList :
        whereCmd[cmd] = isthere(cmd)
    if len(whereCmd) != len(musthave_cmdList) :
        sys.stderr.write("Please Check gdb,ldd,xargs,tar,strace Command")
        sys.exit(2)
        
    # gdb 라이브러리 산출
    retgdb = exeComm('%s %s %s -x gdb.cmd'%(whereCmd['gdb'],execfile,corefile),1)
    for line in retgdb :
        if line.find(" /") != -1 and line.startswith('0x') :
            gdbRaw = realpath(line.split()[-1])
            if isfile(gdbRaw) :
                sharedlibs.append(gdbRaw)
    
    # 일반 명령어 라이브러리와 바이너리      
    util_cmdList = ["bash","ls","cp","grep","cat","diff","tail","head","vi","bc" ]
    for cmd in util_cmdList :
        whereCmd[cmd] = isthere(cmd)
        sharedlibs.append(whereCmd[cmd])
        retldd = exeComm('%s %s'%(whereCmd['ldd'],whereCmd[cmd]),1)
        for line in retldd :
            if line.find(" /") != -1 :
                lddRaw = realpath(line.split()[-2])
                if isfile(lddRaw) :
                    sharedlibs.append(lddRaw)
        #sharedlibs.extend(findLib(whereCmd['ldd'],whereCmd[cmd]))
        
    pkg_cmdList = ["dpkg","rpm"]
    for cmd in pkg_cmdList :
        whereCmd[cmd] = isthere(cmd)
        if whereCmd[cmd] :
            if cmd == "dpkg" :
                retpkg = exeComm('%s -L gdb'%whereCmd[cmd],1)
                #pkgList = pkgthere([whereCmd[cmd],'-L','gdb'])
                for line in retpkg :
                    if isfile(line) :
                        sharedlibs.append(realpath(line))
            elif cmd == "rpm" :
                retpkg =  exeComm('%s -qvl gdb'%whereCmd[cmd],1)
                for line in retpkg :
                    lineRaw = line.split()[8]
                    if isfile(lineRaw) :
                        sharedlibs.append(lineRaw)                  
    if not retpkg :
        sys.stderr.write("Couldn't find dpkg or RPM package.")
        sys.exit(2)

    # strace 처리 부분
    #retstrace = Popen([whereCmd['strace'],'gdb','-h'],stdout=open('/dev/null'),stderr=PIPE).stderr.readlines()
    retstrace = exeComm('%s gdb -h'%whereCmd['strace'],2)
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
