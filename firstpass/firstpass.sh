#!/bin/bash
# 
# firstpass.sh v1.1
# - generates first pass dump analysis report  
#  
# Requirements: 
# - gdb 
# 
# Usage: 
# In the dumpdocker environment
# cd /dump
# /tmp/dumpdocker/firstpass.sh 
# 
# Author: Younghun Chung <younghun.chung@gmail.com> 
# Created on Mon Sep 14 23:10:11 KST 2014 
# Last updated at Tue Sep 15 17:16:31 KST 2014 
# set -x 

# =============================================================================
# First pass report file name and version
# =============================================================================
REPORT="./fpreport.out"
VERSION="version 1.1"

# =============================================================================
# Temporary directory and gdb macro file name
# =============================================================================
TEMP_DIR="./temp"
GDBMACRO="/tmp/dumpdocker/gdbinit.mac"

# =============================================================================
# Clean-up previous reports and making the report directory
# =============================================================================
rm $REPORT
rm -rf "$TEMP_DIR"
mkdir "$TEMP_DIR"

# =============================================================================
# Report title
# =============================================================================
TIMESTAMP=$(date)
EXEC_FILE=$(grep file $GDBMACRO | grep -v "core-file" | awk '{print $2}')
CORE_FILE=$(grep core-file $GDBMACRO | awk '{print $2}')

printf "%70s\n"   "===============================" >> $REPORT
printf "%70s\n"   "First Pass Dump Analysis Report" >> $REPORT
printf "%70s\n"   "===============================" >> $REPORT
printf "%70s\n" "$VERSION"                          >> $REPORT
printf "$TIMESTAMP\n\n"                             >> $REPORT
printf "Exec file name : %s\n"   "$EXEC_FILE"       >> $REPORT
printf "Core file name : %s\n\n" "$CORE_FILE"       >> $REPORT

printf "Table of contents\n"                       >> $REPORT
printf "=================\n"                       >> $REPORT
printf " 1. General information\n"                 >> $REPORT
printf " 2. Environment variables\n"               >> $REPORT
printf " 3. Stacktrace\n"                          >> $REPORT
printf " 4. The failed frame\n"                    >> $REPORT
printf " 5. The information of the failed frame\n" >> $REPORT
printf " 6. Source code information\n"             >> $REPORT
printf " 7. Assembly code\n"                       >> $REPORT
printf " 8. Register information\n"                >> $REPORT
printf " 9. Virtual address space\n"               >> $REPORT
printf "10. Thread information\n"                  >> $REPORT
printf "11. Shared library information\n"          >> $REPORT
printf "12. Full stacktrace\n\n"                   >> $REPORT

# =============================================================================
# Run basic analysis
# =============================================================================
COMMAND="$TEMP_DIR/gdbcom1.txt"
echo "
set logging file $TEMP_DIR/info.out
set logging on
source $GDBMACRO
set logging off

set logging file $TEMP_DIR/bt.out
set logging on
bt
set logging off

set logging file $TEMP_DIR/bt_full.out
set logging on
bt full
set logging off

set logging file $TEMP_DIR/thread.out
set logging on
info thread
set logging off

set logging file $TEMP_DIR/files.out
set logging on
info files
set logging off

set logging file $TEMP_DIR/shared.out
set logging on
info shared
set logging off

thread 1
set logging file $TEMP_DIR/thread-1.bt.out
set logging on
bt -1
set logging off

quit " > $COMMAND

gdb -batch -x $COMMAND


# =============================================================================
# General information
# =============================================================================
echo "1. General information"                     >> $REPORT
echo "======================"                     >> $REPORT
grep "Core was generated" $TEMP_DIR/info.out      >> $REPORT
grep "Program terminated with" $TEMP_DIR/info.out >> $REPORT
echo ""                                           >> $REPORT

# =============================================================================
# Environment variables
# =============================================================================
COMMAND="$TEMP_DIR/gdbcom2.txt"
MAIN_FUNC_FRAME=$(cat $TEMP_DIR/thread-1.bt.out | awk '{print $1}' | cut -d"#" -f2)

echo "
source $GDBMACRO
thread 1
frame $MAIN_FUNC_FRAME
set logging file $TEMP_DIR/thread-1.frame.out
set logging on
info frame $MAIN_FUNC_FRAME
set logging off
quit " > $COMMAND

gdb -batch -x $COMMAND 

COMMAND="$TEMP_DIR/gdbcom3.txt"

# Finding RBP to extract environment variable
LISTREG=$(grep rbp $TEMP_DIR/thread-1.frame.out)
NUMREGS=$(echo "$LISTREG" | grep -o "," | wc -l)
(( NUMREGS=NUMREGS+1 ))
IFS=',' read -a arr_register <<< "${LISTREG}"

for (( i=0; i<$NUMREGS; i++ ))
do
   echo ${arr_register[i]} | grep rbp | awk '{print $3}' >> $TEMP_DIR/rbp.out
done

RBP=$(cat $TEMP_DIR/rbp.out)

echo "
source $GDBMACRO
thread 1
frame $MAIN_FUNC_FRAME
set logging file $TEMP_DIR/rbp_dump.out
set logging on
x /40gx $RBP
set logging off
quit " > $COMMAND

gdb -batch -x $COMMAND

cat $TEMP_DIR/rbp_dump.out |
while read LINE
do
   ADDR1=$(echo $LINE | cut -d":" -f1)
   ADDR2=$(echo $LINE | awk '{print $2}')
   U_ADDR1=$(echo $ADDR1 | tr '[:lower:]' '[:upper:]' | cut -d"X" -f2)
   U_ADDR2=$(echo $ADDR2 | tr '[:lower:]' '[:upper:]' | cut -d"X" -f2)

   OFFSET=$(echo 'ibase=16;obase=A;'$U_ADDR2'-'$U_ADDR1 | bc)
   echo $OFFSET
   if [[ $OFFSET -eq 8 ]]
   then
      echo "$ADDR1" > $TEMP_DIR/env_base.out
		break
   fi
done

ENVBASE=$(cat $TEMP_DIR/env_base.out)

COMMAND="$TEMP_DIR/gdbcom4.txt"

echo "
source $GDBMACRO
thread 1
frame $MAIN_FUNC_FRAME
x /gx $ENVBASE+0x18
set logging file $TEMP_DIR/temp.out
set logging on
x /1000s \$__
set logging off
quit " > $COMMAND

gdb -batch -x $COMMAND

echo "2. Environment variables" >> $REPORT
echo "========================" >> $REPORT
grep -v "out of bounds" $TEMP_DIR/temp.out | grep -v "\"\"" | awk '{print $2}' | cut -d"\"" -f2>> $REPORT
echo "" >> $REPORT

# =============================================================================
# Printing stacktrace
# =============================================================================
echo "3. Stacktrace"    >> $REPORT
echo "============="    >> $REPORT
cat $TEMP_DIR/bt.out    >> $REPORT
echo ""                 >> $REPORT

# =============================================================================
# Checking crashed frame
# =============================================================================
COMMAND="$TEMP_DIR/gdbcom5.txt"

SIGNAL=$(grep "Program terminated with signal" $TEMP_DIR/info.out | awk '{print $5}' | cut -d"," -f1)
if [[ $SIGNAL -eq 6 ]]   # SIGABRT
then
	echo "NOTE:"                                                                >> $REPORT
	echo "##################################################################"   >> $REPORT
	echo "The process called abort().                          "                >> $REPORT
	echo "You should focus on the frame before calling abort()."                >> $REPORT
	echo "And it is good to check the application's log file.  "                >> $REPORT
	echo "##################################################################"   >> $REPORT

	CHECK=$(grep assert_fail $TEMP_DIR/bt.out | wc -l)
	if [[ $CHECK -eq 1 ]]
	then
  		FRAME=$(grep assert_fail $TEMP_DIR/bt.out | awk '{print $1}' | cut -d"#" -f2)
	   (( CRASH_FRAME=FRAME+1 ))
	else
  		FRAME=$(grep "in abort" $TEMP_DIR/bt.out | awk '{print $1}' | cut -d"#" -f2)
	   (( CRASH_FRAME=FRAME+1 ))
	fi
elif [[ $SIGNAL -eq 11 ]]
then
	echo "NOTE:"                                                              >> $REPORT
	echo "##################################################################" >> $REPORT
	echo "The process failed due to segmentation fault."                      >> $REPORT
	echo "It usually ocurrs because of invalid address de-reference."         >> $REPORT
	echo "##################################################################" >> $REPORT
	CRASH_FRAME=0
elif [[ $SIGNAL -eq 10 ]] || [[ $SIGNAL -eq 7 ]]
then
	echo "NOTE:"                                                              >> $REPORT
	echo "##################################################################" >> $REPORT
	echo "The process failed due to bus error."                               >> $REPORT
	echo "It usually ocurrs because of accessing non-aligned address."        >> $REPORT
	echo "##################################################################" >> $REPORT
	CRASH_FRAME=0
elif [[ $SIGNAL -eq 3 ]]
then
	echo "NOTE:"                                                              >> $REPORT
	echo "##################################################################" >> $REPORT
	echo "The process looks failed by user sending SIGQUIT to the process."   >> $REPORT
	echo "##################################################################" >> $REPORT
	CRASH_FRAME=0
elif [[ $SIGNAL -eq 4 ]]
then
	echo "NOTE:"                                                              >> $REPORT
	echo "##################################################################" >> $REPORT
	echo "The process failed due to illegal instruction."                     >> $REPORT
	echo "It jumped to bad instruction due to invalid instruction pointer."   >> $REPORT
	echo "Looks like hardware (specifically CPU) defect. "                    >> $REPORT
	echo "##################################################################" >> $REPORT
	CRASH_FRAME=0
elif [[ $SIGNAL -eq 8 ]]
then
	echo "NOTE:"                                                              >> $REPORT
	echo "##################################################################" >> $REPORT
	echo "The process failed due to floating point exception."                >> $REPORT
	echo "Looks like hardware (specifically CPU) defect. "                    >> $REPORT
	echo "##################################################################" >> $REPORT
	CRASH_FRAME=0
else
	echo "NOTE:"                                                              >> $REPORT
	echo "##################################################################" >> $REPORT
	echo "The process failed due to unknown reason."                          >> $REPORT
	echo "Please check from the first frame crashed.     "                    >> $REPORT
	echo "##################################################################" >> $REPORT
	CRASH_FRAME=0
fi

CRASH_IP=$(grep ^#$CRASH_FRAME $TEMP_DIR/bt.out | awk '{print $2}')

echo "
source $GDBMACRO
set logging file $TEMP_DIR/crashframe_source.out
set logging on
echo \n
echo 4. The failed frame #$CRASH_FRAME\n
echo ======================\n
frame $CRASH_FRAME
echo \n
echo 5. The information of the failed frame #$CRASH_FRAME\n
echo =========================================\n
info frame $CRASH_FRAME
echo \n
echo 6. Source code information\n
echo ==========================\n
info source
echo \n
info line
echo \n
list
echo \n
set logging off 
set logging file $TEMP_DIR/asmcode.out
set logging on
echo 7. Assembly code\n
echo ================\n
x /30i $CRASH_IP-0x30
echo \n
echo Failed Instruction
x /i $CRASH_IP
echo \n
set logging off
set logging file $TEMP_DIR/register.out
set logging on
echo 8. Register information\n
echo =======================\n
info reg
echo \n
set logging off
quit " > $COMMAND	

gdb -batch -x $COMMAND

# =============================================================================
# Checking local source directory
# =============================================================================
NOCURSRC=$(grep "No current source" $TEMP_DIR/crashframe_source.out | wc -l)
if [[ $NOCURSRC -eq 1 ]] # Current frame has no source code information
then
	echo "NOTE:"                                                                 >> $TEMP_DIR/crashframe_source.out
	echo "##################################################################"   >> $TEMP_DIR/crashframe_source.out
	echo "The crashed frame has no source code information."                    >> $TEMP_DIR/crashframe_source.out
	echo "##################################################################"   >> $TEMP_DIR/crashframe_source.out
	echo ""                                                                     >> $TEMP_DIR/crashframe_source.out
else
	SRCDIR=$(grep "Located in" $TEMP_DIR/crashframe_source.out | wc -l)
	if [[ $SRCDIR -eq 0 ]] # Source directory is not specified
	then
		SRCFILE=$(grep "Current source" $TEMP_DIR/crashframe_source.out | awk '{print $5}')
		SRCDIR=$(dirname $SRCFILE)
		echo "NOTE:"                                                                >> $TEMP_DIR/crashframe_source.out
		echo "##################################################################"   >> $TEMP_DIR/crashframe_source.out
		echo "Please add the following line to the $GDBMACRO file"                  >> $TEMP_DIR/crashframe_source.out
		if [[ $SRCDIR=="\." ]]
		then
			echo "	directory <your source directory>"                          >> $TEMP_DIR/crashframe_source.out
		else
			echo "	set substitute-path $SRCDIR <your source directory>"        >> $TEMP_DIR/crashframe_source.out
		fi	
		echo "to list the crashed source code."                                     >> $TEMP_DIR/crashframe_source.out
		echo "##################################################################"   >> $TEMP_DIR/crashframe_source.out
		echo ""                                                                     >> $TEMP_DIR/crashframe_source.out
	fi
fi

# =============================================================================
# Checking assembly code, if the process failed due to SIGSEGV, SIGBUG
# =============================================================================
if [[ $SIGNAL -eq 11 ]] || [[ $SIGNAL -eq 10 ]] || [[ $SIGNAL -eq 7 ]]
then
	FAILED_INSTRUCTION=$(grep "^Failed Instruction" $TEMP_DIR/asmcode.out | cut -d ":" -f2)
	ASMCOM=$(echo $FAILED_INSTRUCTION | awk '{print $1}')
	if [[ $ASMCOM=="mov" ]]
	then
		OPERANDS=$(echo $FAILED_INSTRUCTION | awk '{print $2}')
		SRC_OP=$(echo "$OPERANDS" | cut -d "," -f1 | cut -c 3-5)
		DES_OP=$(echo "$OPERANDS" | cut -d "," -f2 | cut -c 2-4)
		echo "NOTE:"                                                                >> $TEMP_DIR/asmcode.out
		echo "##################################################################"   >> $TEMP_DIR/asmcode.out
		echo "It tried to load from the memory, the address saved in $SRC_OP    "   >> $TEMP_DIR/asmcode.out
		echo "and copy to the register, $DES_OP. It failed because the content  "   >> $TEMP_DIR/asmcode.out
		echo "in $SRC_OP register is not a valid address.                       "   >> $TEMP_DIR/asmcode.out
		echo "If you need to check assembly code, trace the $SRC_OP not $DES_OP."   >> $TEMP_DIR/asmcode.out
		echo "##################################################################"   >> $TEMP_DIR/asmcode.out
		echo "" >> $TEMP_DIR/asmcode.out
	fi
	# add another assembly command case here
fi

cat $TEMP_DIR/crashframe_source.out >> $REPORT
cat $TEMP_DIR/asmcode.out           >> $REPORT
cat $TEMP_DIR/register.out          >> $REPORT

# =============================================================================
# Virtual address space
# =============================================================================
TOTALSIZE=0
echo "Checking virtual address space"
echo "=============================="

echo "9. Virtual address space"          >> $REPORT
echo "========================"          >> $REPORT
cat $TEMP_DIR/files.out | grep "load" > $TEMP_DIR/files2.out
cat $TEMP_DIR/files2.out |
while read LINE
do
	ADDR_START=$(echo $LINE | awk '{print $1}' | cut -d"x" -f2)
	ADDR_END=$(echo $LINE | awk '{print $3}' | cut -d"x" -f2)
	NAME=$(echo $LINE | awk '{print $5}')
	U_ADDR_START=$(echo $ADDR_START | tr '[:lower:]' '[:upper:]')
	U_ADDR_END=$(echo $ADDR_END   | tr '[:lower:]' '[:upper:]')
	SIZE=$(echo 'ibase=16;obase=A;'$U_ADDR_END'-'$U_ADDR_START | bc)
	TOTALSIZE=$(echo 'ibase=A;obase=A;'$TOTALSIZE'+'$SIZE | bc)
	printf "%s - %s is %8s : %14s bytes\n" "0x$ADDR_START" "0x$ADDR_END" "$NAME" "$SIZE" >> $REPORT
	printf "*"
	echo "$TOTALSIZE" > $TEMP_DIR/totalsize.out
done
printf " Done.\n"
printf "==========================================================================\n" >> $REPORT
TOTALSIZE=$(cat $TEMP_DIR/totalsize.out)
TOTALMB=$(echo 'ibase=A;obase=A;'$TOTALSIZE'/1024/1024' | bc)
printf "%51s : %14s bytes\n" "TOTAL" "$TOTALSIZE" >> $REPORT
if [[ $TOTALMB -ne 0 ]]
then
	printf "%68s MB\n" "$TOTALMB" >> $REPORT
fi

echo "" >> $REPORT

# =============================================================================
# Thread information 
# =============================================================================
echo "Checking thread information" 
echo "==========================="
NUMTHREAD=$(grep LWP $TEMP_DIR/thread.out | wc -l)
echo "10. Thread information"            >> $REPORT
echo "======================"            >> $REPORT
cat $TEMP_DIR/thread.out             >> $REPORT
echo ""                              >> $REPORT
echo "Number of threads: $NUMTHREAD" >> $REPORT
echo ""                              >> $REPORT

# =============================================================================
# Shared library information 
# =============================================================================
echo "Checking shared libraies" 
echo "========================"
echo "11. Shared library information" >> $REPORT
echo "==============================" >> $REPORT
cat $TEMP_DIR/shared.out          >> $REPORT
echo ""                           >> $REPORT

# =============================================================================
# Full stacktrace
# =============================================================================
echo "Checking full stacktrace"
echo "========================"
echo "12. Full stacktrace"    >> $REPORT
echo "==================="    >> $REPORT
cat $TEMP_DIR/bt_full.out >> $REPORT
echo ""                   >> $REPORT
