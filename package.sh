# zip the manifest.json and all the code under src/ into a zip file
# Usage: ./package.sh 

mkdir tmp 
cp src/* tmp
cp manifest.json tmp
cp meta.json tmp
cd tmp
zip -r ../tex-cardify.ankiaddon *
cd ..
rm -rf tmp
