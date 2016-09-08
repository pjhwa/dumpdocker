# dumpdocker

dumpdocker creates docker image for analysis of crash dump and generates the first pass dump analysis report from the docker image.

### Requirements
gdb (latest version), strace

### Usage

Run dumpdocker from the crashed server:

```
# dumpdocker /path/executable /path/core_file
```

You must specify the absolute path of executable file. 

After this, it creates a tar file containing the executables and the shared libraries. And then you can send this tar file and the core file to your dump analysis system. Copy the "core_file" to /dump directory of the dump analysis system.

Run the following commands on the dump analysis system:

```
# cat hostname.executable.YYYYMMDDHHMM.tar | docker import - <image_name>
# docker run -i -v /dump:/dump -t <image_name> /bin/bash

bash-X.X# cd /dump
bash-X.X# /opt/dumpdocker/firstpass.sh
```

You can review the firstpass report before moving core file to the dump analysis system. The firstpass report, fpreport.out file will be located in /opt/dumpdocker/ directory.

### Samples

There is a sample source code in the samples directory. You can test dumpdocker or check the first pass report from the sample.

```
# cd samples
# make
cc -std=c99 -g -o sampleSegv sampleSegv.c
# ulimit -c unlimited
# ./sampleSegv 111
Segmentation fault (core dumped)
# mkdir /dump
# cp core.* /dump
# sudo ../dumpdocker $PWD/sampleSegv ./core.19389
dumpdocker 1.4.1
Gathering the shared libraries and files related with /home/pjhwa/dumpdocker/samples/sampleSegv.
Including the basic commands for dump analysis.
Generating the files related with firstpass.sh.
which: no dmidecode in (/usr/bin:/bin)
Archiving the files into samplehost.sampleSegv.201509151404.tar file.
Removing the temporary files.
Done.
# cat samplehost.sampleSegv.201509151404.tar | docker import - samplehost
# docker run -i -v /dump:/dump -t samplehost /bin/bash

bash-X.X# cd /dump
bash-X.X# /opt/dumpdocker/firstpass.sh
```
