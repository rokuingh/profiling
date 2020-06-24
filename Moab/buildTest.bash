#!/bin/bash
#
# build the test executable
#

set -e

testcase=$1
ESMFMKFILE=$2
SRCDIR=$3
cheyenne=$4

if [[ $cheyenne != "False" ]]; then
  module purge; module load ncarenv/1.3 intel/18.0.5 ncarcompilers/0.5.0 mpt/2.19 netcdf/4.7.1; 
fi

# build the executable locally
cd $SRCDIR/$testcase
ESMFMKFILE=$ESMFMKFILE make distclean &> /dev/null
ESMFMKFILE=$ESMFMKFILE make > make.out 2>&1
