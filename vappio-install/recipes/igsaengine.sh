# Installing BER, praze, cdbfasta   Task 135
wget -O /tmp/ber-20051118.tgz -P /tmp http://sourceforge.net/projects/ber/files/ber/ber-20051118/ber-20051118.tgz/download
mkdir -p /usr/local/bioinf/BER
tar -C /usr/local/bioinf/BER -xvzf /tmp/ber-20051118.tgz

wget -O /tmp/praze-20051118.tgz -P /tmp http://sourceforge.net/projects/ber/files/ber/ber-20051118/praze-20051118.tgz/download
mkdir -p /tmp/praze
tar -C /tmp/praze -xvzf /tmp/praze-20051118.tgz
cd /tmp/praze
make
cp praze /usr/local/bin/

#wget -P /tmp ftp://occams.dfci.harvard.edu/pub/bio/tgi/software/tgicl/tgi_cpp_library.tar.gz
wget -P /tmp "https://downloads.sourceforge.net/project/cdbfasta/tgi_cpp_library.tar.gz?r=http%3A%2F%2Fen.sourceforge.jp%2Fprojects%2Fsfnet_cdbfasta%2Fdownloads%2Ftgi_cpp_library.tar.gz%2F&ts=1403294073&use_mirror=iweb"
#wget -P /tmp ftp://occams.dfci.harvard.edu/pub/bio/tgi/software/cdbfasta/cdbfasta.tar.gz
wget -P /tmp "https://downloads.sourceforge.net/project/cdbfasta/cdbfasta.tar.gz?r=http%3A%2F%2Fen.sourceforge.jp%2Fprojects%2Fsfnet_cdbfasta%2Fdownloads%2Fcdbfasta.tar.gz%2F&ts=1403294300&use_mirror=iweb"
tar -C /tmp -xvzf /tmp/cdbfasta.tar.gz
tar -C /tmp/cdbfasta -xvzf /tmp/tgi_cpp_library.tar.gz
cd /tmp/cdbfasta
perl -pi -e 's/^TGICLASSDIR := .*/TGICLASSDIR := \.\/tgi_cl/' Makefile
make
cp /tmp/cdbfasta/cdbfasta /usr/local/bin/
cp /tmp/cdbfasta/cdbyank /usr/local/bin/

cpanm --sudo Math::Round
