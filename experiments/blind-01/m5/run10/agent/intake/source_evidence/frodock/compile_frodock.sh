#!/bin/bash
echo "COMPILING & LINKING FRODOCK-2.0 TOOLS (v1.06)"
export IMOD_FLAGS=""
echo
echo "Entering: src"
cd src

# COMPILING LIBRARIES AND EXECUTABLES
 for i in libtools libpdb libvolume libfrm libbessel libfrodock libfrodockcluster libprotprot libsas frodock frodockgrid frodockonstraint frodockcluster frodockview frodockcheck
 do
  echo "  Entering: $i"
  cd $i
   for j in *
   do
    if test -d $j
    then
     echo "    Entering: $j"
     cd $j
      echo Cleaning $i $j
      make clean
      echo Making $i $j
      make
     cd ..
     echo "    Exiting: $j"
    fi
   done
  cd ..
  echo "  Exiting: $i"
 done

cd ..
echo "Exiting: src"
