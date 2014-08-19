#
# dumpdocker
# - creates docker image based on tar file for analysis of crash dump 
# 
# Requirements:
# - gdb
#
# Usage:
# dumpdocker [-h] exec_bin core_file
#

import os.path,sys
from optparse import OptionParser

import time, socket, subprocess

def exec_linux(command):
    ret = subprocess.call("%s"%command,shell=True,stderr=open("/dev/null"),stdout=subprocess.PIPE)
    return ret
    
if __name__ == '__main__':
    
    # option 처리 부분
    use_desc ="%prog [-h] -e binary -c corefile "
    parser = OptionParser(usage=use_desc)
    parser.add_option("-e",help="crashed executable Binary",dest="binfile")
    parser.add_option("-c",help="core file",dest="corefile")
    
    (opts, args) = parser.parse_args()
    
    if os.path 
    
    
    
    exec_bin = sys.argv[1]
    core_file = sys.argv[2]
        
    if os.path.isfile(sys.argv[1]) :
        sys.stderr.write("%s : please input correct executable binary as exec_bin\n" %sys.argv[0])
        raise SystemExit[2]    
    
    
    now = time.localtime()
    DATE = now.tm_year+now.tm_mon+now.tm_mday+now.tm_hour+now.tm_min
    uname = socket.gethostname()
    
    ret = subprocess.call("gdb script",shell=True,stderr=open("/dev/null"))
    
    try : # 파일오픈 성공여부 확인
        with open('/tmp/d.gdb.tmp','rt') as readFile :
            sharedlibs =  [ os.path.realpath(line) for line in readFile if line.find("/") ]
    except IOError as err : # 파일오픈 실패시 에러 출력후 종료
        sys.stderr.write('File Error : ' + str(err))
            
    basic_cmds=["bash","ls","cp","grep","cat","diff","tail","head","vi","bc","gdb"]
    
    for cmd in basic_cmds :
        pathCmd = subprocess.Popen("which %s"%cmd,shell=True,stdout=subprocess.PIPE)
        fullPathCommand = pathCmd.stdout.read()
        result = subprocess.Popen("ldd %s"%fullPathCommand,shell=True,stdout=subprocess.PIPE)
        resultLdd = result.stdout.read()
        for line in resultLdd :
            if line.find("/") :
                if line.find("=>") :
                    sharedlibs.append(line.split("=>")[1])
                else
                    sharedlibs.append(line)
        
    dpkg_bin = subprocess.Popen("which dpkg",shell=True,stdout=subprocess.PIPE).stdout.read()
    rpm_bin = subprocess.Popen("which rpm",shell=True,stdout=subprocess.PIPE).stdout.read()
    
    if dpkg_bin :
        gdb_pkg_list = exec_linux("%s -L gdb"%dpkg_bin)
    else
        print("Couldn't find gdb package.")
    if rpm_bin :
        gdb_pkg_list = exec_linux("%s -qvl gdb"%rpm_bin).stdout.read()
    else
        print("Couldn't find gdb package.")
        
    for pkg_list in gdb_pkg_list :
        if os.path.isfile(pkg_list) :
            sharedlibs.append(pkg_list)
    
    gdb_text = subprocess.Popen("strace gdb -h",stderr=subprocess.PIPE).stderr.read()
    for line in gdb_text :
        if not (line.find("^open(\)") or line.find("no such file") or line.find("\tmp") or line.find("\proc") or line.find("\dev")) :
            shareslibs.append(line.split('"')[1])
             
    myset = set(shareslibs)
    
    ret = subprocess.Popen("xargs tar cvf %s.%s.%s.tar"%(uname,exec_bin,DATE),shell=True,stdin=myset) 

    
    pass