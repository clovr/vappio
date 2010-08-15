
then
    name="clovr"
fi
cp $2 $3
perl -pi -e 's/\;NAME\;/$name/g' $3
perl -pi -e 's/\;IMG_FILE\;/$1/g' $3
