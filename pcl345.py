
# -*- coding: ISO-8859-15 -*-
#
# pkpgcounter : a generic Page Description Language parser
#
# (c) 2003, 2004, 2005, 2006, 2007 Jerome Alet <alet@librelogiciel.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# $Id: pcl345.py 374 2007-12-09 14:26:15Z jerome $
#

"""This modules implements a page counter for PCL3/4/5 documents."""

import sys
import os
import mmap
from struct import unpack

import pdlparser
import pjl

NUL = chr(0x00)
LINEFEED = chr(0x0a)
FORMFEED = chr(0x0c)
ESCAPE = chr(0x1b)
ASCIILIMIT = chr(0x80)

class Parser(pdlparser.PDLParser) :
    """A parser for PCL3, PCL4, PCL5 documents."""
    totiffcommands = [ 'pcl6 -sDEVICE=pdfwrite -r"%(dpi)i" -dPARANOIDSAFER -dNOPAUSE -dBATCH -dQUIET -sOutputFile=- "%(infname)s" | gs -sDEVICE=tiff24nc -dPARANOIDSAFER -dNOPAUSE -dBATCH -dQUIET -r%(dpi)i -sOutputFile="%(outfname)s" -', 
                       'pcl6 -sDEVICE=pswrite -r"%(dpi)i" -dPARANOIDSAFER -dNOPAUSE -dBATCH -dQUIET -sOutputFile=- "%(infname)s" | gs -sDEVICE=tiff24nc -dPARANOIDSAFER -dNOPAUSE -dBATCH -dQUIET -r%(dpi)i -sOutputFile="%(outfname)s" -',
                     ]
    required = [ "pcl6", "gs" ]
    format = "PCL3/4/5"
    mediasizes = {  # ESC&l####A
                    0 : "Default",
                    1 : "Executive",
                    2 : "Letter",
                    3 : "Legal",
                    6 : "Ledger", 
                    25 : "A5",
                    26 : "A4",
                    27 : "A3",
                    45 : "JB5",
                    46 : "JB4",
                    71 : "HagakiPostcard",
                    72 : "OufukuHagakiPostcard",
                    80 : "MonarchEnvelope",
                    81 : "COM10Envelope",
                    90 : "DLEnvelope",
                    91 : "C5Envelope",
                    100 : "B5Envelope",
                    101 : "Custom",
                 }   
                 
    mediasources = { # ESC&l####H
                     0 : "Default",
                     1 : "Main",
                     2 : "Manual",
                     3 : "ManualEnvelope",
                     4 : "Alternate",
                     5 : "OptionalLarge",
                     6 : "EnvelopeFeeder",
                     7 : "Auto",
                     8 : "Tray1",
                   }
                   
    orientations = { # ESC&l####O
                     0 : "Portrait",
                     1 : "Landscape",
                     2 : "ReversePortrait",
                     3 : "ReverseLandscape",
                   }
                   
    mediatypes = { # ESC&l####M
                     0 : "Plain",
                     1 : "Bond",
                     2 : "Special",
                     3 : "Glossy",
                     4 : "Transparent",
                   }
        
    def isValid(self) :    
        """Returns True if data is PCL3/4/5, else False."""
        try :
            pos = 0
            while self.firstblock[pos] == chr(0) :
                pos += 1
        except IndexError :        
            return False
        else :    
            firstblock = self.firstblock[pos:]
            if firstblock.startswith("\033E\033") or \
               firstblock.startswith("\033%1BBPIN;") or \
               ((pos == 11000) and firstblock.startswith("\033")) or \
               (firstblock.startswith("\033*rbC") and (not self.lastblock[-3:] == "\f\033@")) or \
               firstblock.startswith("\033*rB\033") or \
               firstblock.startswith("\033%8\033") or \
               (firstblock.find("\033%-12345X") != -1) or \
               (firstblock.find("@PJL ENTER LANGUAGE=PCL\012\015\033") != -1) or \
               (firstblock.startswith(chr(0xcd)+chr(0xca)) and (firstblock.find("\033E\033") != -1)) :
                return True
            else :    
                return False
        
    def setPageDict(self, attribute, value) :
        """Initializes a page dictionnary."""
        dic = self.pages.setdefault(self.pagecount, { "linescount" : 1,
                                                      "copies" : 1, 
                                                      "mediasource" : "Main", 
                                                      "mediasize" : "Default", 
                                                      "mediatype" : "Plain", 
                                                      "orientation" : "Portrait", 
                                                      "escaped" : "", 
                                                      "duplex": 0 })
        dic[attribute] = value
        
    def readByte(self) :    
        """Reads a byte from the input stream."""
        tag = ord(self.minfile[self.pos])
        self.pos += 1
        return tag
        
    def endPage(self) :    
        """Handle the FF marker."""
        #self.logdebug("FORMFEED %i at %08x" % (self.pagecount, self.pos-1))
        if not self.hpgl2 :
            # Increments page count only if we are not inside an HPGL2 block
            self.pagecount += 1
        
    def escPercent(self) :    
        """Handles the ESC% sequence."""
        if self.minfile[self.pos : self.pos+7] == r"-12345X" :
            #self.logdebug("Generic ESCAPE sequence at %08x" % self.pos)
            self.pos += 7
            buffer = []
            quotes = 0
            char = chr(self.readByte())
            while ((char < ASCIILIMIT) or (quotes % 2)) and (char not in (FORMFEED, ESCAPE, NUL)) :  
                buffer.append(char)
                if char == '"' :
                    quotes += 1
                char = chr(self.readByte())
            self.setPageDict("escaped", "".join(buffer))
            #self.logdebug("ESCAPED : %s" % "".join(buffer))
            self.pos -= 1   # Adjust position
        else :    
            while 1 :
                (value, end) = self.getInteger()
                if end == 'B' :
                    self.enterHPGL2()
                    while self.minfile[self.pos] != ESCAPE :
                        self.pos += 1
                    self.pos -= 1    
                    return 
                elif end == 'A' :    
                    self.exitHPGL2()
                    return
                elif end is None :    
                    return
        
    def enterHPGL2(self) :    
        """Enters HPGL2 mode."""
        #self.logdebug("ENTERHPGL2 %08x" % self.pos)
        self.hpgl2 = True
        
    def exitHPGL2(self) :    
        """Exits HPGL2 mode."""
        #self.logdebug("EXITHPGL2 %08x" % self.pos)
        self.hpgl2 = False
        
    def handleTag(self, tagtable) :    
        """Handles tags."""
        tagtable[self.readByte()]()
        
    def escape(self) :    
        """Handles the ESC character."""
        #self.logdebug("ESCAPE")
        self.handleTag(self.esctags)
        
    def escAmp(self) :    
        """Handles the ESC& sequence."""
        #self.logdebug("AMP")
        self.handleTag(self.escamptags)
        
    def escStar(self) :    
        """Handles the ESC* sequence."""
        #self.logdebug("STAR")
        self.handleTag(self.escstartags)
        
    def escLeftPar(self) :    
        """Handles the ESC( sequence."""
        #self.logdebug("LEFTPAR")
        self.handleTag(self.escleftpartags)
        
    def escRightPar(self) :    
        """Handles the ESC( sequence."""
        #self.logdebug("RIGHTPAR")
        self.handleTag(self.escrightpartags)
        
    def escE(self) :    
        """Handles the ESCE sequence."""
        #self.logdebug("RESET")
        self.resets += 1
        
    def escAmpl(self) :    
        """Handles the ESC&l sequence."""
        while 1 :
            (value, end) = self.getInteger()
            if value is None :
                return
            if end in ('h', 'H') :
                mediasource = self.mediasources.get(value, str(value))
                self.mediasourcesvalues.append(mediasource)
                self.setPageDict("mediasource", mediasource)
                #self.logdebug("MEDIASOURCE %s" % mediasource)
            elif end in ('a', 'A') :
                mediasize = self.mediasizes.get(value, str(value))
                self.mediasizesvalues.append(mediasize)
                self.setPageDict("mediasize", mediasize)
                #self.logdebug("MEDIASIZE %s" % mediasize)
            elif end in ('o', 'O') :
                orientation = self.orientations.get(value, str(value))
                self.orientationsvalues.append(orientation)
                self.setPageDict("orientation", orientation)
                #self.logdebug("ORIENTATION %s" % orientation)
            elif end in ('m', 'M') :
                mediatype = self.mediatypes.get(value, str(value))
                self.mediatypesvalues.append(mediatype)
                self.setPageDict("mediatype", mediatype)
                #self.logdebug("MEDIATYPE %s" % mediatype)
            elif end == 'X' :
                self.copies.append(value)
                self.setPageDict("copies", value)
                #self.logdebug("COPIES %i" % value)
            elif end == 'F' :    
                self.linesperpagevalues.append(value)
                self.linesperpage = value
                #self.logdebug("LINES PER PAGE : %i" % self.linesperpage)
            #else :
            #    self.logdebug("Unexpected end <%s> and value <%s>" % (end, value))
                
    def escAmpa(self) :    
        """Handles the ESC&a sequence."""
        while 1 :
            (value, end) = self.getInteger()
            if value is None :
                return
            if end == 'G' :    
                #self.logdebug("BACKSIDES %i" % value)
                self.backsides.append(value)
                self.setPageDict("duplex", value)
                
    def escAmpp(self) :    
        """Handles the ESC&p sequence."""
        while 1 :
            (value, end) = self.getInteger()
            if value is None :
                return
            if end == 'X' :    
                self.pos += value
                #self.logdebug("SKIPTO %08x" % self.pos)
                
    def escStarb(self) :    
        """Handles the ESC*b sequence."""
        while 1 :
            (value, end) = self.getInteger()
            if (end is None) and (value is None) :
                return
            if end in ('V', 'W', 'v', 'w') :    
                self.pos += (value or 0)
                #self.logdebug("SKIPTO %08x" % self.pos)
                
    def escStarr(self) :    
        """Handles the ESC*r sequence."""
        while 1 :
            (value, end) = self.getInteger()
            if value is None :
                if end is None :
                    return
                elif end in ('B', 'C') :        
                    #self.logdebug("EndGFX")
                    if self.startgfx :
                        self.endgfx.append(1)
                    else :    
                        #self.logdebug("EndGFX found before StartGFX, ignored.")
                        pass
            if end == 'A' and (0 <= value <= 3) :
                #self.logdebug("StartGFX %i" % value)
                self.startgfx.append(value)
                
    def escStaroptAmpu(self) :    
        """Handles the ESC*o ESC*p ESC*t and ESC&u sequences."""
        while 1 :
            (value, end) = self.getInteger()
            if value is None :
                return
        
    def escSkipSomethingW(self) :    
        """Handles the ESC???###W sequences."""
        while 1 :
            (value, end) = self.getInteger()
            if value is None :
                return
            if end == 'W' :    
                self.pos += value
                #self.logdebug("SKIPTO %08x" % self.pos)
                
    def newLine(self) :            
        """Handles new lines markers."""
        if not self.hpgl2 :
            dic = self.pages.get(self.pagecount, None)
            if dic is None :
                self.setPageDict("linescount", 1)                              
                dic = self.pages.get(self.pagecount)
            nblines = dic["linescount"]    
            self.setPageDict("linescount", nblines + 1)                              
            if (self.linesperpage is not None) \
               and (dic["linescount"] > self.linesperpage) :
                self.pagecount += 1
        
    def getInteger(self) :    
        """Returns an integer value and the end character."""
        sign = 1
        value = None
        while 1 :
            char = chr(self.readByte())
            if char in (NUL, ESCAPE, FORMFEED, ASCIILIMIT) :
                self.pos -= 1 # Adjust position
                return (None, None)
            if char == '-' :
                sign = -1
            elif not char.isdigit() :
                if value is not None :
                    return (sign*value, char)
                else :
                    return (value, char)
            else :    
                value = ((value or 0) * 10) + int(char)    
        
    def skipByte(self) :    
        """Skips a byte."""
        #self.logdebug("SKIPBYTE %08x ===> %02x" % (self.pos, ord(self.minfile[self.pos])))
        self.pos += 1
        
    def handleImageRunner(self) :    
        """Handles Canon ImageRunner tags."""
        tag = self.readByte()
        if tag == ord(self.imagerunnermarker1[-1]) :
            oldpos = self.pos-2
            codop = self.minfile[self.pos:self.pos+2]
            length = unpack(">H", self.minfile[self.pos+6:self.pos+8])[0]
            self.pos += 18
            if codop != self.imagerunnermarker2 :
                self.pos += length
            self.logdebug("IMAGERUNNERTAG SKIP %i AT %08x" % (self.pos-oldpos, self.pos))
        else :
            self.pos -= 1 # Adjust position
                
    def getJobSize(self) :
        import subprocess

        pdfinfo = ['/usr/bin/pdfinfo', '-']
        pcl6    = ['/usr/bin/pcl6', '-sDEVICE=pdfwrite', '-dBATCH', '-dNOPAUSE', '-sOutputFile=-', self.infile.name]
        
        pipe = subprocess.Popen(pcl6, stdout=subprocess.PIPE)
        output = subprocess.check_output(pdfinfo, stdin=pipe.stdout)
        pipe.wait()

        for line in output.splitlines():
            if "Pages" in line:
                pages = line.split(':', 1)[1].strip()
        
        return int(pages)

