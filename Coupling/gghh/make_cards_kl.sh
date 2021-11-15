outdir=cards
if [ ! -d "$outdir" ]; then
  mkdir $outdir
fi

DIRECTORY=${outdir}/${1}${2}_kl
if [ -d "$DIRECTORY" ]; then
  rm -rf $DIRECTORY
fi
mkdir $DIRECTORY

inputhist=${3}/HHTo4BPlots_Run2_BDT${1}.root
cd $DIRECTORY

#create datacard
if [ $4 == True ]
then
    python ../../../../create_datacard_test.py --inputfile $inputhist --include-ac --add-blinded --carddir ./
else
    python ../../../../create_datacard_test.py --inputfile $inputhist --include-ac --carddir ./
fi
    
    
#combine datacards and produce results
if [ $4 == True ]
then
  echo "blinded fit"
  . ../../ana.sh $2 $3
else
  echo "unblinded fit"
  . ../../ana_unblind.sh $2 $3
fi
cd ../../
