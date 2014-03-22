#!/bin/sh

P=folders2flickr
V=$(git describe)
exifpymd5=fb99ecc1919494600aa6965ffb41dd60

tempdir=$(mktemp -d)
trap "rm -rf $tempdir" EXIT
outdir=$tempdir/$P-$V
exifpyversion=$(awk -F= '/ExifRead/ {print $3}' requirements.txt)
exifpy=${exifpyversion}.tar.gz
mkdir $outdir

wget -q https://github.com/ianare/exif-py/archive/$exifpy -O $tempdir/$exifpy || exit 1
echo "$exifpymd5  $tempdir/$exifpy" | md5sum -c - || exit 1
tar -C $outdir -xf $tempdir/$exifpy exif-py-$exifpyversion/exifread/ --strip-components=1
tar -C $outdir -xf $tempdir/$exifpy exif-py-$exifpyversion/LICENSE.txt 
git archive  --format=tar HEAD | tar -C $outdir -x

here=$PWD
cd $tempdir
zip -r -o $here/$P-$V.zip $P-$V
cd -
rm -rf $tempdir
