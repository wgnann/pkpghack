#! /bin/bash

echo instalando pacotes...
sudo apt install pkpgcounter poppler-utils

echo baixando o arquivo de teste...
TESTFILE=/tmp/test.pdf
wget -q -O$TESTFILE http://www.ic.unicamp.br/~fkm/lectures/algorithmicgametheory.pdf
echo testando o pkpgcounter...
pkpgcounter $TESTFILE

echo baixando o ghostpcl6...
GHOSTPCL=https://github.com$(wget -q -O- https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/latest | grep "/ArtifexSoftware/ghostpdl-downloads/releases/download/.*ghostpcl.*linux-x86_64.tgz" -o)
wget -q $GHOSTPCL -O ghostpcl.tgz
echo copiando o pcl6...
PCL6=$(tar --wildcards -xvzf ghostpcl.tgz ghostpcl*linux-x86_64/gpcl6*linux-x86_64)
sudo cp $PCL6 /usr/bin/pcl6 

echo copiando os hacks...
for file in pdf.py pcl345.py
do
    if [ ! -f /usr/lib/python2.7/dist-packages/pkpgpdls/$file.bak ]
    then
        sudo cp /usr/lib/python2.7/dist-packages/pkpgpdls/$file /usr/lib/python2.7/dist-packages/pkpgpdls/$file.bak
    fi
    ls /usr/lib/python2.7/dist-packages/pkpgpdls/$file.bak
    sudo cp -i $file /usr/lib/python2.7/dist-packages/pkpgpdls/$file
done

echo testando novamente o pkpgcounter...
pkpgcounter $TESTFILE

echo limpando...
rm -ri $PCL6 ghostpcl.tgz
rmdir ghostpcl*linux-x86_64
