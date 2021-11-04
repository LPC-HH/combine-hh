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
echo python ../../../../create_datacard_test.py --inputfile $inputhist --include-ac --add-blinded $4 --carddir ./
python ../../../../create_datacard_test.py --inputfile $inputhist --include-ac --add-blinded $4 --carddir ./

#combine datacards and produce results
if [ $5 == True ]
then
  echo "blinded fit"
  . ../../ana.sh $2 $3
else
  echo "blinded fit"
  . ../../ana_unblind.sh $2 $3
fi
cd ../../
