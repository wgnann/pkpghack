# pkpghack
Trata-se de um hack do [pkpgcounter](https://github.com/barracks510/pkpgcounter) que corrige porcamente o problema 

# Instalação assistida
  ./install.sh

# Instalação manual no Debian:
 1. `apt install pkpgcounter poppler-utils`;
 2. baixar o [arquivo de teste](http://www.ic.unicamp.br/~fkm/lectures/algorithmicgametheory.pdf);
 3. testá-lo: `pkpgcounter algorithmicgametheory.pdf` e `pdfinfo algorithmicgametheory.pdf`. O `pkpgcounter` deve acusar 0 páginas;
 4. baixar [Ghostscript-PCL](https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/latest);
 5. extrair o conteúdo e copiar o `gpcl6*` para `/usr/bin/pcl6`. Marcá-lo como executável, se necessário;
 6. copiar `pdf.py` e o `pcl345.py` para `/usr/lib/python2.7/dist-packages/pkpgpdls`. Fazer backup dos originais se julgar conveniente;
 7. testar novamente o `pkpgcounter`.

*OBS*: O pacote [pkpgcounter](http://ftp.us.debian.org/debian/pool/main/p/pkpgcounter/pkpgcounter_3.50-8_all.deb) pode ser obtido [aqui](http://ftp.us.debian.org/debian/pool/main/p/pkpgcounter/pkpgcounter_3.50-8_all.deb).
