# Installing BER, praze, cdbfasta   Task 135
wget -P /tmp https://sourceforge.net/projects/ber/files/ber/ber-20051118/ber-20051118.tgz/download
mkdir -p /usr/local/bioinf/BER
tar -C /usr/local/bioinf/BER -xvzf /tmp/ber-20051118.tgz

wget -P /tmp https://sourceforge.net/projects/ber/files/ber/ber-20051118/praze-20051118.tgz/download
mkdir -p /tmp/praze
tar -C /tmp/praze -xvzf /tmp/praze-20051118.tgz
cd /tmp/praze
make
cp praze /usr/local/bin/

wget -P /tmp ftp://occams.dfci.harvard.edu/pub/bio/tgi/software/tgicl/tgi_cpp_library.tar.gz
wget -P /tmp ftp://occams.dfci.harvard.edu/pub/bio/tgi/software/cdbfasta/cdbfasta.tar.gz
tar -C /tmp -xvzf /tmp/cdbfasta.tar.gz
tar -C /tmp/cdbfasta -xvzf /tmp/tgi_cpp_library.tar.gz
cd /tmp/cdbfasta
perl -pi -e 's/^TGICLASSDIR := .*/TGICLASSDIR := \.\/tgi_cl/' Makefile
make
cp /tmp/cdbfasta/cdbfasta /usr/local/bin/
cp /tmp/cdbfasta/cdbyank /usr/local/bin/
