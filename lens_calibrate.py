#!/usr/bin/python3

#######################################################################
#
# A script to calibrate camera lenes for lensfun
#
# Copyright (c) 2012-2016 Torsten Bronger <bronger@physik.rwth-aachen.de>
# Copyright (c) 2018-2019 Andreas Schneider <asn@cryptomilk.org>
#
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
#######################################################################
#
# Requires: python3-exiv2
# Requires: python3-numpy
# Requires: python3-scipy
# Requires: python3-PyPDF2
#
# Requires: darktable (darktable-cli)
# Requires: hugin-tools (tca_correct)
# Requires: ImageMagick (convert)
# Requires: gnuplot
#

import os
import argparse
import configparser
import codecs
import re
import math
import numpy as np
import struct
import subprocess
import shutil
import tarfile
from subprocess import DEVNULL
from scipy.optimize.minpack import leastsq

from pyexiv2.metadata import ImageMetadata
from pyexiv2.exif import ExifTag

from PyPDF2 import PdfFileMerger

# Sidecar for loading into hugin
# Applies a neutral basecurve and enables sharpening
DARKTABLE_DISTORTION_SIDECAR = '''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0-Exiv2">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
    xmlns:darktable="http://darktable.sf.net/"
   xmp:Rating="1"
   xmpMM:DerivedFrom="DISTORTION.ARW"
   darktable:xmp_version="2"
   darktable:raw_params="0"
   darktable:auto_presets_applied="1"
   darktable:history_end="3">
   <darktable:mask_id>
    <rdf:Seq/>
   </darktable:mask_id>
   <darktable:mask_type>
    <rdf:Seq/>
   </darktable:mask_type>
   <darktable:mask_name>
    <rdf:Seq/>
   </darktable:mask_name>
   <darktable:mask_version>
    <rdf:Seq/>
   </darktable:mask_version>
   <darktable:mask>
    <rdf:Seq/>
   </darktable:mask>
   <darktable:mask_nb>
    <rdf:Seq/>
   </darktable:mask_nb>
   <darktable:mask_src>
    <rdf:Seq/>
   </darktable:mask_src>
   <darktable:history>
    <rdf:Seq>
     <rdf:li
      darktable:operation="sharpen"
      darktable:enabled="1"
      darktable:modversion="1"
      darktable:params="000000400000003f0000003f"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="flip"
      darktable:enabled="1"
      darktable:modversion="2"
      darktable:params="ffffffff"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="basecurve"
      darktable:enabled="1"
      darktable:modversion="5"
      darktable:params="gz09eJxjYIAAruuLrbmuK1vPmilpN2vmTLuzZ87YGRsb2zMwONgbGxcD6QYoHgVDCbAhsZkwZCFxCgBDtg6p"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
    </rdf:Seq>
   </darktable:history>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
'''

# Sidecar for TCA corrections
# Disables the basecurve and sharpening and sets input to Linear Rec2020 RGB
DARKTABLE_TCA_SIDECAR = '''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0-Exiv2">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
    xmlns:darktable="http://darktable.sf.net/"
   xmp:Rating="1"
   xmpMM:DerivedFrom="TCA.ARW"
   darktable:xmp_version="2"
   darktable:raw_params="0"
   darktable:auto_presets_applied="1"
   darktable:history_end="4">
   <darktable:mask_id>
    <rdf:Seq/>
   </darktable:mask_id>
   <darktable:mask_type>
    <rdf:Seq/>
   </darktable:mask_type>
   <darktable:mask_name>
    <rdf:Seq/>
   </darktable:mask_name>
   <darktable:mask_version>
    <rdf:Seq/>
   </darktable:mask_version>
   <darktable:mask>
    <rdf:Seq/>
   </darktable:mask>
   <darktable:mask_nb>
    <rdf:Seq/>
   </darktable:mask_nb>
   <darktable:mask_src>
    <rdf:Seq/>
   </darktable:mask_src>
   <darktable:history>
    <rdf:Seq>
     <rdf:li
      darktable:operation="flip"
      darktable:enabled="1"
      darktable:modversion="2"
      darktable:params="ffffffff"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="basecurve"
      darktable:enabled="0"
      darktable:modversion="5"
      darktable:params="gz09eJxjYICAL3eYbKcsErU1fXPdVmRLpl1B+T07pyon+6WC0fb9R6rtGRgaoHgUDCXAhsRmwpCFxCkAdoEQ3Q=="
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="sharpen"
      darktable:enabled="0"
      darktable:modversion="1"
      darktable:params="000000400000003f0000003f"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="colorin"
      darktable:enabled="1"
      darktable:modversion="4"
      darktable:params="gz10eJxjYaA/AAACRAAF"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="colorout"
      darktable:enabled="1"
      darktable:modversion="4"
      darktable:params="gz10eJxjYaAfAAACHAAF"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
    </rdf:Seq>
   </darktable:history>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
'''

# Sidecar for vignetting corrections
# Disables the basecurve and sharpening and sets input to Linear Rec2020 RGB
DARKTABLE_VIGNETTING_SIDECAR = '''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0-Exiv2">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
    xmlns:darktable="http://darktable.sf.net/"
   xmp:Rating="1"
   xmpMM:DerivedFrom="TCA.ARW"
   darktable:xmp_version="2"
   darktable:raw_params="0"
   darktable:auto_presets_applied="1"
   darktable:history_end="4">
   <darktable:mask_id>
    <rdf:Seq/>
   </darktable:mask_id>
   <darktable:mask_type>
    <rdf:Seq/>
   </darktable:mask_type>
   <darktable:mask_name>
    <rdf:Seq/>
   </darktable:mask_name>
   <darktable:mask_version>
    <rdf:Seq/>
   </darktable:mask_version>
   <darktable:mask>
    <rdf:Seq/>
   </darktable:mask>
   <darktable:mask_nb>
    <rdf:Seq/>
   </darktable:mask_nb>
   <darktable:mask_src>
    <rdf:Seq/>
   </darktable:mask_src>
   <darktable:history>
    <rdf:Seq>
     <rdf:li
      darktable:operation="flip"
      darktable:enabled="1"
      darktable:modversion="2"
      darktable:params="ffffffff"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="basecurve"
      darktable:enabled="0"
      darktable:modversion="5"
      darktable:params="gz09eJxjYICAL3eYbKcsErU1fXPdVmRLpl1B+T07pyon+6WC0fb9R6rtGRgaoHgUDCXAhsRmwpCFxCkAdoEQ3Q=="
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="sharpen"
      darktable:enabled="0"
      darktable:modversion="1"
      darktable:params="000000400000003f0000003f"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="colorin"
      darktable:enabled="1"
      darktable:modversion="4"
      darktable:params="gz10eJxjYaA/AAACRAAF"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
     <rdf:li
      darktable:operation="colorout"
      darktable:enabled="1"
      darktable:modversion="4"
      darktable:params="gz10eJxjYaAfAAACHAAF"
      darktable:multi_name=""
      darktable:multi_priority="0"
      darktable:blendop_version="7"
      darktable:blendop_params="gz12eJxjYGBgkGAAgRNODESDBnsIHll8ANNSGQM="/>
    </rdf:Seq>
   </darktable:history>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
'''

def is_raw_file(filename):
    raw_file_extensions = [
            ".3FR", ".ARI", ".ARW", ".BAY", ".CRW", ".CR2", ".CAP", ".DCS",
            ".DCR", ".DNG", ".DRF", ".EIP", ".ERF", ".FFF", ".IIQ", ".K25",
            ".KDC", ".MEF", ".MOS", ".MRW", ".NEF", ".NRW", ".OBM", ".ORF",
            ".PEF", ".PTX", ".PXN", ".R3D", ".RAF", ".RAW", ".RWL", ".RW2",
            ".RWZ", ".SR2", ".SRF", ".SRW", ".X3F", ".JPG", ".JPEG", ".TIF",
            ".TIFF",
        ]
    file_ext = os.path.splitext(filename)[1]

    return file_ext.upper() in raw_file_extensions

def has_exif_tag(data, tag):
    return tag in data

def image_read_exif(filename):
    data = ImageMetadata(filename)

    # This reads the metadata and closes the file
    data.read()

    lens_model = None
    tag = 'Exif.Photo.LensModel'
    if has_exif_tag(data, tag):
        lens_model = data[tag].value
    else:
        tag = 'Exif.NikonLd3.LensIDNumber'
        if has_exif_tag(data, tag):
            lens_model = data[tag].human_value

        tag = 'Exif.Panasonic.LensType'
        if has_exif_tag(data, tag):
            lens_model = data[tag].value

        tag = 'Exif.Sony1.LensID'
        if has_exif_tag(data, tag):
            lens_model = data[tag].human_value

        tag = 'Exif.Minolta.LensID'
        if has_exif_tag(data, tag):
            lens_model = data[tag].human_value

    if lens_model is None:
       lens_model = 'Standard'

    tag = 'Exif.Photo.FocalLength'
    if has_exif_tag(data, tag):
        focal_length = float(data[tag].value)
    else:
        print("%s doesn't have Exif.Photo.FocalLength set. " % (filename) +
              "Please fix it manually.")

    tag = 'Exif.Photo.FNumber'
    if has_exif_tag(data, tag):
        aperture = float(data[tag].value)
    else:
        print("%s doesn't have Exif.Photo.FNumber set. " % (filename) +
              "Please fix it manually.")

    return { "lens_model" : lens_model,
             "focal_length" : focal_length,
             "aperture" : aperture }

def write_sidecar_file(sidecar_file, content):
    if not os.path.isfile(sidecar_file):
        try:
            with open(sidecar_file, 'w') as f:
                f.write(content)
        except OSError:
            return False

    return True

# convert raw file to 16bit tiff
def convert_raw_for_distortion(input_file, sidecar_file, output_file=None):
    if output_file is None:
        output_file = ("%s.tif" % os.path.splitext(input_file)[0])

    if not os.path.exists(output_file):
        print("Converting %s to %s ..." % (input_file, output_file), end='', flush=True)

        cmd = [
                "darktable-cli",
                input_file,
                sidecar_file,
                output_file,
                "--core",
                "--conf", "plugins/lighttable/export/iccintent=0", # perceptual
                "--conf", "plugins/lighttable/export/iccprofile=sRGB",
                "--conf", "plugins/lighttable/export/style=none",
                "--conf", "plugins/imageio/format/tiff/bpp=16",
                "--conf", "plugins/imageio/format/tiff/compress=5"
            ]
        try:
            subprocess.check_call(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise
        except OSError:
            print("Could not find darktable-cli")
            return None

        print(" DONE", flush=True)

    return output_file

def convert_raw_for_tca(input_file, sidecar_file, output_file=None):
    if output_file is None:
        output_file = ("%s.ppm" % os.path.splitext(input_file)[0])

    if not os.path.exists(output_file):
        cmd = [
                "darktable-cli",
                input_file,
                sidecar_file,
                output_file,
                "--core",
                "--conf", "plugins/lighttable/export/iccprofile=image",
                "--conf", "plugins/lighttable/export/style=none",
            ]
        try:
            subprocess.check_call(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise
        except OSError:
            print("Could not find darktable-cli")

    return output_file

def convert_raw_for_vignetting(input_file, sidecar_file, output_file=None):
    if output_file is None:
        output_file = ("%s.ppm" % os.path.splitext(input_file)[0])

    if not os.path.exists(output_file):
        # TODO: Ask for clarification for such a small image size for vignetting!
        # Is this some normalization?
        cmd = [
                "darktable-cli",
                input_file,
                sidecar_file,
                output_file,
                "--width", "250",
                "--core",
                "--conf", "plugins/lighttable/export/iccprofile=image",
                "--conf", "plugins/lighttable/export/style=none",
            ]
        try:
            subprocess.check_call(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise
        except OSError:
            print("Could not find darktable-cli")

    return output_file

def convert_ppm_for_vignetting(input_file):
    output_file = ("%s.pgm" % os.path.splitext(input_file)[0])

    # Convert the ppm file to a pgm (grayscale) file
    if not os.path.exists(output_file):
        cmd = [ "convert",
                "-colorspace",
                "RGB",
                input_file,
                "-set",
                "colorspace",
                "RGB",
                output_file ]
        try:
            subprocess.check_call(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise
        except OSError:
            print("Could not find convert")

    return output_file

def plot_pdf(plot_file):
    try:
        gnuplot = shutil.which("gnuplot")
    except shutil.Error:
        return False

    cmd = [ gnuplot, plot_file ]
    try:
        subprocess.check_call(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        raise
    except OSError:
        print("Could not find gnuplot")
        return False

    return True

def merge_final_pdf(final_pdf, pdf_dir):
    pdf_merger = PdfFileMerger()

    pdf_files = []

    for path, directories, files in os.walk(pdf_dir):
        for filename in files:
            if os.path.splitext(filename)[1] != '.pdf':
                continue

            pdf_files.append(filename)

    if len(pdf_files) == 0:
        return

    pdf_files.sort()

    for pdf in pdf_files:
        pdf_merger.append(os.path.join(pdf_dir, pdf))

    pdf_merger.write(final_pdf)
    pdf_merger.close()

def create_lenses_config(lenses_exif_group):
    config = configparser.ConfigParser()
    for lenses in lenses_exif_group:
        config[lenses] = {
                'maker' : '[unknown]',
                'mount' : '[unknown]',
                'cropfactor' : '1.0',
                'aspect_ratio' : '3:2',
                'type' : 'normal'
                }
        for exif_data in lenses_exif_group[lenses]:
            distortion = ("distortion(%.1fmm)" % exif_data['focal_length'])
            config[lenses][distortion] = '0.0, 0.0, 0.0'
    with open('lenses.conf', 'w') as configfile:
        config.write(configfile)

    print("A template has been created for distortion corrections as lenses.conf.")
    print("Please fill this file with proper information. The most important")
    print("values are:")
    print("")
    print("maker:        is the manufacturer or the lens, e.g. 'FE 16-35mm F2.8 GM'")
    print("mount:        is the name of the mount system, e.g. 'Sony E'")
    print("cropfactor:   is the crop factor of the camera as a float, e.g. '1.0' for")
    print("              full frame")
    print("aspect_ratio: is the aspect_ratio, e.g. '3:2'")
    print("type:         is the type of the lens, e.g. 'normal' for rectilinear")
    print("              lenses. Other possible values are: stereographic, equisolid,")
    print("              stereographic, panoramic or fisheye.")
    print("")
    print("You can find details for distortion calculations here:")
    print("")
    print("https://pixls.us/articles/create-lens-calibration-data-for-lensfun/")

    return

def parse_lenses_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)

    lenses = {}

    for section in config.sections():
        lenses[section] = {}
        lenses[section]['distortion'] = {}
        lenses[section]['tca'] = {}
        lenses[section]['vignetting'] = {}

        for key in config[section]:
            if key.startswith('distortion'):
                focal_length = key[11:len(key) - 3]
                lenses[section]['distortion'][focal_length] = config[section][key]
            else:
                lenses[section][key] = config[section][key]

    return lenses

def tca_correct(input_file, original_file, exif_data, complex_tca=False):
    basename = os.path.splitext(input_file)[0]
    output_file = ("%s.tca" % basename)
    gp_filename = ("%s.gp" % basename)
    pdf_filename = ("%s.pdf" % basename)

    if not os.path.exists(output_file):
        print("Running TCA corrections for %s ..." % (input_file), end='', flush=True)

        tca_complexity = 'v'
        if complex_tca:
            tca_complexity = 'bv'
        cmd = [ "tca_correct", "-o", tca_complexity, input_file ]
        try:
            output = subprocess.check_output(cmd, stderr=DEVNULL)
        except subprocess.CalledProcessError:
            raise
        except OSError:
            print("Could not find tca_correct")
            return None

        tca_data = re.match(r"-r [.0]+:(?P<br>[-.0-9]+):[.0]+:(?P<vr>[-.0-9]+) -b [.0]+:(?P<bb>[-.0-9]+):[.0]+:(?P<vb>[-.0-9]+)",
                            output.decode('ascii')).groupdict()

        tca_config = configparser.ConfigParser()
        tca_config[exif_data['lens_model']] = {
                'focal_length' : exif_data['focal_length'],
                'complex_tca' : complex_tca,
                'tca' : output.decode('ascii'),
                'br' : tca_data['br'],
                'vr' : tca_data['vr'],
                'bb' : tca_data['bb'],
                'vb' : tca_data['vb'],
                }
        with open(output_file, "w") as tcafile:
            tca_config.write(tcafile)

        if complex_tca:
            with codecs.open(gp_filename, "w", encoding="utf-8") as c:
                c.write('set term pdf\n')
                c.write('set print "%s"\n' % (input_file))
                c.write('set output "%s"\n' % (pdf_filename))
                c.write('set fit logfile "/dev/null"\n')
                c.write('set grid\n')
                c.write('set title "%s, %0.1f mm, f/%0.1f\\n%s" noenhanced\n' %
                        (exif_data['lens_model'],
                         exif_data['focal_length'],
                         exif_data['aperture'],
                         original_file))
                c.write('plot [0:1.8] %s * x**2 + %s title "red", %s * x**2 + %s title "blue"\n' %
                        (tca_data['br'], tca_data["vr"], tca_data["bb"], tca_data["vb"]))

            plot_pdf(gp_filename)

        print(" DONE", flush=True)

def load_pgm(filename):
    header = None
    width = None
    height = None
    maxval = None

    with open(filename, 'rb') as f:
        buf = f.read()
    try:
        header, width, height, maxval = re.search(
            b"(^P5\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n]\s)*)", buf).groups()
    except AttributeError:
        raise ValueError("Not a NetPGM file: '%s'" % filename)

    f.close()

    width = int(width)
    height = int(height)
    maxval = int(maxval)

    if maxval == 255:
        dt = np.dtype(np.uint8)
    elif maxval == 65535:
        dt = np.dtype(np.uint16)
    elif maxval == 4294967295:
        dt = np.dtype(np.float)
    else:
        raise ValueError("Not a NetPGM file: '%s'" % filename)
    dt = dt.newbyteorder('B')

    shape = np.frombuffer(buf,
                          dtype = dt,
                          count = width * height,
                          offset = len(header))

    return width, height, shape.reshape((height, width))

def fit_function(radius, A, k1, k2, k3):
    return A * (1 + k1 * radius**2 + k2 * radius**4 + k3 * radius**6)

def calculate_vignetting(input_file, original_file, exif_data, distance):
    basename = os.path.splitext(input_file)[0]
    all_points_filename = ("%s.all_points.dat" % basename)
    bins_filename = ("%s.bins.dat" % basename)
    pdf_filename = ("%s.pdf" % basename)
    gp_filename = ("%s.gp" % basename)
    vig_filename = ("%s.vig" % basename)

    if os.path.exists(vig_filename):
        return

    print("Generating vignetting data for %s ... " % input_file, end='', flush=True)

    # This loads the pgm file and we get the image data and an one dimensional array
    # image_data = [1009, 1036, 1071, 1106, 1140, 1169, 1202, 1239, ...]
    width, height, image_data = load_pgm(input_file)

    # Get the half diagonal of the image
    half_diagonal = math.hypot(width // 2, height // 2)
    maximal_radius = 1

    # Only remember pixel intensities which are in the given radius
    radii, intensities = [], []
    for y in range(image_data.shape[0]):
        for x in range(image_data.shape[1]):
            radius = math.hypot(x - width // 2, y - height // 2) / half_diagonal
            if radius <= maximal_radius:
                radii.append(radius)
                intensities.append(image_data[y,x])

    with open(all_points_filename, 'w') as f:
        for radius, intensity in zip(radii, intensities):
            f.write("%f %d\n" % (radius, intensity))

    number_of_bins = 16
    bins = [[] for i in range(number_of_bins)]
    for radius, intensity in zip(radii, intensities):
        # The zeroth and the last bin are only half bins which means that their
        # means are skewed.  But this is okay: For the zeroth, the curve is
        # supposed to be horizontal anyway, and for the last, it underestimates
        # the vignetting at the rim which is a good thing (too much of
        # correction is bad).
        bin_index = int(round(radius / maximal_radius * (number_of_bins - 1)))
        bins[bin_index].append(intensity)
    radii = [i / (number_of_bins - 1) * maximal_radius for i in range(number_of_bins)]
    intensities = [np.median(bin) for bin in bins]

    with open(bins_filename, 'w') as f:
        for radius, intensity in zip(radii, intensities):
            f.write("%f %d\n" % (radius, intensity))

    radii, intensities = np.array(radii), np.array(intensities)

    A, k1, k2, k3 = leastsq(lambda p, x, y: y - fit_function(x, *p), [30000, -0.3, 0, 0], args=(radii, intensities))[0]

    vig_config = configparser.ConfigParser()
    vig_config[exif_data['lens_model']] = {
                'focal_length' : exif_data['focal_length'],
                'aperture' : exif_data['aperture'],
                'distance' : distance,
                'A' : ('%.7f' % A),
                'k1' : ('%.7f' % k1),
                'k2' : ('%.7f' % k2),
                'k3' : ('%.7f' % k3),
                }
    with open(vig_filename, "w") as vigfile:
        vig_config.write(vigfile)

    if distance == float("inf"):
        distance = "∞"

    with codecs.open(gp_filename, "w", encoding="utf-8") as c:
        c.write('set term pdf\n')
        c.write('set print "%s"\n' % (input_file))
        c.write('set output "%s"\n' % (pdf_filename))
        c.write('set fit logfile "/dev/null"\n')
        c.write('set grid\n')
        c.write('set title "%s, %0.1f mm, f/%0.1f, %s m\\n%s" noenhanced\n' %
                (exif_data['lens_model'],
                 exif_data['focal_length'],
                 exif_data['aperture'],
                 distance,
                 original_file))
        c.write('plot "%s" with dots title "samples", ' %
                all_points_filename)
        c.write('"%s" with linespoints lw 4 title "average", ' %
                bins_filename)
        c.write('%f * (1 + (%f) * x**2 + (%f) * x**4 + (%f) * x**6) title "fit"\n' %
                (A, k1, k2, k3))

    plot_pdf(gp_filename)

    print(" DONE\n", flush=True)

def init():
    # Create directory structure
    dirlist = ['distortion', 'tca', 'vignetting']

    for d in dirlist:
        if os.path.isfile(d):
            print("ERROR: '%s' is a file, can't create directory!" % d)
            return
        elif not os.path.isdir(d):
            os.mkdir(d)

    print("The following directory structure has been created in the "
          "local directory\n\n"
          "1. distortion - Put RAW file created for distortion in here\n"
          "2. tca        - Put chromatic abbrevation RAW files in here\n"
          "3. vignetting - Put RAW files to calculate vignetting in here\n")

def create_distortion_correction(export_path, path, filename, sidecar_file):
    input_file = os.path.join(path, filename)
    output_file = os.path.join(path, "exported", ("%s.tif" % os.path.splitext(filename)[0]))

    # Convert RAW files to TIF for hugin
    output_file = convert_raw_for_distortion(input_file, sidecar_file, output_file)

    return True

def run_distortion():
    lenses_config_exists = os.path.isfile('lenses.conf')
    lenses_exif_group = {}

    print('Running distortion corrections ...')

    if not os.path.isdir("distortion"):
        print("No distortion directory, you have to run init first!")
        return

    export_path = os.path.join("distortion", "exported")
    if not os.path.isdir(export_path):
        os.mkdir(export_path)

    sidecar_file = os.path.join(export_path, "distortion.xmp")
    if not write_sidecar_file(sidecar_file, DARKTABLE_DISTORTION_SIDECAR):
        print("Failed to write sidecar_file: %s" % sidecar_file)
        return

    for path, directories, files in os.walk('distortion'):
        for filename in files:
            if path != "distortion":
                continue
            if not is_raw_file(filename):
                continue

            input_file = os.path.join(path, filename)

            exif_data = image_read_exif(input_file)
            if exif_data is not None:
                if exif_data['lens_model'] not in lenses_exif_group:
                    lenses_exif_group[exif_data['lens_model']] = []
                lenses_exif_group[exif_data['lens_model']].append(exif_data)

                # Add focal length to file name for easier identification
                if exif_data['focal_length'] > 1.0:
                    output_file = os.path.join(path, "exported", ("%s_%dmm.tif" % (os.path.splitext(filename)[0], exif_data['focal_length'])))

            create_distortion_correction(export_path, path, filename, sidecar_file)

    if not lenses_config_exists:
        sorted_lenses_exif_group = {}
        for lenses in sorted(lenses_exif_group):
            # TODO: Remove duplicates?
            sorted_lenses_exif_group[lenses] = sorted(lenses_exif_group[lenses], key=lambda exif : exif['focal_length'])

        create_lenses_config(sorted_lenses_exif_group)

def run_tca(complex_tca):
    if not os.path.isdir("tca"):
        print("No tca directory, you have to run init first!")
        return

    export_path = os.path.join("tca", "exported")
    if not os.path.isdir(export_path):
        os.mkdir(export_path)

    sidecar_file = os.path.join(export_path, "tca.xmp")
    if not write_sidecar_file(sidecar_file, DARKTABLE_TCA_SIDECAR):
        print("Failed to write sidecar_file: %s" % sidecar_file)
        return

    for path, directories, files in os.walk('tca'):
        for filename in files:
            if path != "tca":
                continue
            if not is_raw_file(filename):
                continue

            # Convert RAW files to tiff for tca_correct
            input_file = os.path.join(path, filename)

            exif_data = image_read_exif(input_file)

            output_file = os.path.join(path, "exported", ("%s.ppm" % os.path.splitext(filename)[0]))
            output_file = convert_raw_for_tca(input_file, sidecar_file, output_file)

            tca_correct(output_file, input_file, exif_data, complex_tca)

            if complex_tca:
                merge_final_pdf("tca.pdf", "tca/exported")

def run_vignetting():
    if not os.path.isdir("vignetting"):
        print("No vingetting directory, you have to run init first!")
        return

    export_path = os.path.join("vignetting", "exported")
    if not os.path.isdir(export_path):
        os.mkdir(export_path)

    sidecar_file = os.path.join(export_path, "vignetting.xmp")
    if not write_sidecar_file(sidecar_file, DARKTABLE_DISTORTION_SIDECAR):
        print("Failed to write sidecar_file: %s" % sidecar_file)
        return

    for path, directories, files in os.walk('vignetting'):
        for filename in files:
            distance = float("inf")

            if not is_raw_file(filename):
                continue

            # Ignore the export path
            if path == export_path:
                continue

            if path != "vignetting":
                d = os.path.basename(path)
                try:
                    distance = float(d)
                except:
                    continue

            # Convert RAW files to NetPGM
            input_file = os.path.join(path, filename)

            # Read EXIF data
            exif_data = image_read_exif(input_file)

            # Convert the RAW file to ppm
            output_file = os.path.join(export_path, ("%s.ppm" % os.path.splitext(filename)[0]))
            preview_file = os.path.join(export_path, ("%s.jpg" % os.path.splitext(filename)[0]))

            print("Processing %s ... " % (input_file), flush=True)

            output_file = convert_raw_for_vignetting(input_file, sidecar_file, output_file)

            # Create vignetting PGM files (grayscale)
            pgm_file = convert_ppm_for_vignetting(output_file)

            # Calculate vignetting data
            calculate_vignetting(pgm_file, input_file, exif_data, distance)

            merge_final_pdf("vignetting.pdf", "vignetting/exported")

            # Create preview jpg
            convert_raw_for_vignetting(input_file, sidecar_file, preview_file)

def run_generate_xml():
    print("Generating lensfun.xml")

    lenses_config_exists = os.path.isfile('lenses.conf')

    if not lenses_config_exists:
        print("lenses.conf doesn't exist, run distortion first")
        return

    # We need maker, model, mount, crop_factor etc.
    lenses = parse_lenses_config('lenses.conf')

    # Scan tca files and add to lenses
    for path, directories, files in os.walk('tca/exported'):
        for filename in files:
            if os.path.splitext(filename)[1] != '.tca':
                continue

            config = configparser.ConfigParser()
            config.read(os.path.join(path, filename))

            for lens_model in config.sections():
                focal_length = config[lens_model]['focal_length']
                if not focal_length in lenses[lens_model]['tca']:
                    lenses[lens_model]['tca'][focal_length] = {}

                for key in config[lens_model]:
                    if key != 'focal_length':
                        lenses[lens_model]['tca'][focal_length][key] = config[lens_model][key]

    # Scan vig files and add to lenses
    for path, directories, files in os.walk('vignetting/exported'):
        for filename in files:
            if os.path.splitext(filename)[1] != '.vig':
                continue

            config = configparser.ConfigParser()
            config.read(os.path.join(path, filename))

            for lens_model in config.sections():
                focal_length = config[lens_model]['focal_length']
                if not focal_length in lenses[lens_model]['vignetting']:
                    lenses[lens_model]['vignetting'][focal_length] = {}

                aperture = config[lens_model]['aperture']
                if not aperture in lenses[lens_model]['vignetting'][focal_length]:
                    lenses[lens_model]['vignetting'][focal_length][aperture] = {}

                distance = config[lens_model]['distance']
                if not distance in lenses[lens_model]['vignetting'][focal_length][aperture]:
                    lenses[lens_model]['vignetting'][focal_length][aperture][distance] = {}

                for key in config[lens_model]:
                    if key != 'focal_length' and key != 'aperture' and key != 'distance':
                        lenses[lens_model]['vignetting'][focal_length][aperture][distance][key] = config[lens_model][key]

    # write lenses to xml
    with open('lensfun.xml', 'w') as f:
        f.write('<lensdatabase>\n')
        for lens_model in lenses:
            f.write('    <lens>\n')
            f.write('        <maker>%s</maker>\n' % lenses[lens_model]['maker'])
            f.write('        <model>%s</model>\n' % lens_model)
            f.write('        <mount>%s</mount>\n' % lenses[lens_model]['mount'])
            f.write('        <cropfactor>%s</cropfactor>\n' % lenses[lens_model]['cropfactor'])
            if lenses[lens_model]['type'] != 'normal':
                f.write('        <type>%s</type>\n' % lenses[lens_model]['type'])

            # Add calibration data
            f.write('        <calibration>\n')

            # Add distortion entries
            focal_lengths = lenses[lens_model]['distortion'].keys()
            for focal_length in sorted(focal_lengths, key=float):
                data = list(map(str.strip, lenses[lens_model]['distortion'][focal_length].split(',')))
                if data[1] is None:
                    f.write('            '
                            '<distortion model="poly3" focal="%s" k1="%s" />\n' %
                            (focal_length, data[0]))
                else:
                    f.write('            '
                            '<distortion model="ptlens" focal="%s" a="%s" b="%s" c="%s" />\n' %
                            (focal_length, data[0], data[1], data[2]))

            # Add tca entries
            focal_lengths = lenses[lens_model]['tca'].keys()
            for focal_length in sorted(focal_lengths, key=float):
                data = lenses[lens_model]['tca'][focal_length]
                if data['complex_tca'] == 'True':
                    f.write('            '
                            '<tca model="poly3" focal="%s" br="%s" vr="%s" bb="%s" vb="%s" />\n' %
                            (focal_length, data['br'], data['vr'], data['bb'], data['vb']))
                else:
                    f.write('            '
                            '<tca model="poly3" focal="%s" vr="%s" vb="%s" />\n' %
                            (focal_length, data['vr'], data['vb']))

            # Add vignetting entries
            focal_lengths = lenses[lens_model]['vignetting'].keys()
            for focal_length in sorted(focal_lengths, key=float):
                apertures = lenses[lens_model]['vignetting'][focal_length].keys()
                for aperture in sorted(apertures, key=float):
                    distances = lenses[lens_model]['vignetting'][focal_length][aperture].keys()
                    for distance in sorted(distances, key=float):
                        data = lenses[lens_model]['vignetting'][focal_length][aperture][distance]

                        if distance == 'inf':
                            distance = '1000'

                        _distances = [ distance ]

                        # If we only have an infinite distance, we need to write two values
                        if len(distances) == 1 and distance == '1000':
                            _distances = [ '10', '1000' ]

                        for _distance in _distances:
                            f.write('            '
                                    '<vignetting model="pa" focal="%s" aperture="%s" distance="%s" '
                                    'k1="%s" k2="%s" k3="%s" />\n' %
                                    (focal_length, aperture, _distance,
                                     data['k1'], data['k2'], data['k3']))

            f.write('        </calibration>\n')
            f.write('    </lens>\n')
        f.write('</lensdatabase>\n')

def run_ship():
    if not os.path.exists("lensfun.xml"):
        print("lensfun.xml not found, please run the calibration steps first!")
        return

    tar_files = [ "lensfun.xml", "tca.pdf", "vignetting.pdf" ]
    tar_name = "lensfun_calibration.tar.xz"

    vignetting_dir = 'vignetting/exported'
    if os.path.exists(vignetting_dir):
        for path, directories, files in os.walk(vignetting_dir):
            for filename in files:
                if os.path.splitext(filename)[1] != '.jpg':
                    continue

                tar_files.append(os.path.join(vignetting_dir, filename))

    tar = tarfile.open(tar_name, 'w:xz')

    for f in tar_files:
        if not os.path.exists(f):
            continue

        try:
            tinfo = tar.gettarinfo(name=f)

            tinfo.uid = 0
            tinfo.gid = 0
            tinfo.uname = "root"
            tinfo.gname = "root"
        except OSError:
            continue

        fh = open(f, "rb")
        tar.addfile(tinfo, fileobj=fh)
        fh.close()

    tar.close()

    print("Created lensfun_calibration.tar.xz")
    print("Open a bug at https://github.com/lensfun/lensfun/issues/ with the data.")

class CustomDescriptionFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

def main():

    description = '''
This is an overview about the calibration steps.\n
\n
To setup the required directory structure simply run:

    lens_calibrate.py init

The next step is to copy the RAW files you created to the corresponding
directories.

Once you have done that run:

    lens_calibrate.py distortion

This will create tiff file you can use to figure out the the lens distortion
values (a), (b) and (c) using hugin. It will also create a lenses.conf where
you need to fill out missing values.

If you don't want to do distortion corrections you need to create the
lenses.conf file manually. It needs to look like this:

    [MODEL NAME]
    maker =
    mount =
    cropfactor =
    aspect_ratio =
    type =

The section name needs to be the lens model name you can figure out with:

    exiv2 -g LensModel -pt <raw file>

The required options are:

maker:        is the manufacturer or the lens, e.g. 'FE 16-35mm F2.8 GM'
mount:        is the name of the mount system, e.g. 'Sony E'
cropfactor:   is the crop factor of the camera as a float, e.g. '1.0' for full
              frame
aspect_ratio: is the aspect ratio of your camera, normally it is '3:2'
type:         is the type of the lens, e.g. 'normal' for rectilinear lenses.
              Other possible values are: stereographic, equisolid, stereographic,
              panoramic or fisheye.

If you want TCA corrections just run:

    lens_calibrate.py tca

If you want vignetting corrections run:

    lens_calibrate.py vignetting

Once you have created data for all corrections you can generate an xml file
which can be consumed by lensfun. Just call:

    lens_calibrate.py generate_xml

To use the data in your favourite software you just have to copy the generated
lensfun.xml file to:

    ~/.local/share/lensfun/

If you want to submit the data to the lensfun project run:

    lens_calibrate.py ship

then create a bug report to add the lens calibration data to the project at:

  https://github.com/lensfun/lensfun/issues/

and provide the lensfun_calibratrion.tar.xz

-----------------------------

'''

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=CustomDescriptionFormatter)

    parser.add_argument('--complex-tca',
                        action='store_true',
                        help='Turns on non-linear polynomials for TCA')
    #parser.add_argument('-r, --rawconverter', choices=['darktable', 'dcraw'])

    parser.add_argument('action',
                        choices=[
                            'init',
                            'distortion',
                            'tca',
                            'vignetting',
                            'generate_xml',
                            'ship'],
                        help='This runs one of the actions for lens calibration')

    args = parser.parse_args()

    if args.action == 'init':
        init()
    elif args.action == 'distortion':
        run_distortion()
    elif args.action == 'tca':
        run_tca(args.complex_tca)
    elif args.action == 'vignetting':
        run_vignetting()
    elif args.action == 'generate_xml':
        run_generate_xml()
    elif args.action == 'ship':
        run_ship()

if __name__ == "__main__":
    main()
