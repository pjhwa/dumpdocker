dumpdocker
==========

creates docker images for analysis of crash dump and generates the first pass dump analysis report from the docker image.


Usage
=====

Run dumpdocker from the crashed server:

# dumpdocker /path/executable /path/core_file

After this, it creates a tar file containing the executables and the shared libraries. And then you can send this tar file and the core file to your dump analysis system. Copy the "core_file" to /dump directory of the dump analysis system.

Run the following commands on the dump analysis system:

# cat hostname.executable.YYYYMMDDHHMM.tar | docker import - <image_name>
# docker run -i -v /dump:/dump -t <image_name> /bin/bash

bash-X.X# cd /dump
bash-X.X# gdb /path/executable ./core_file

