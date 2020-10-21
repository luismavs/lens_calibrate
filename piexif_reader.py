#!/usr/bin/env python3

#######################################################################
#
# 
# Exif data reader using pyexif
#
# Copyright (c) 2012-2016 Torsten Bronger <bronger@physik.rwth-aachen.de>
# Copyright (c) 2018-2019 Andreas Schneider <asn@cryptomilk.org>
# Copyright (c) 2020 Luis Seabra <luismavseabra@gmail.com>
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

import unicodedata
from pathlib import Path
import piexif

def strip_control_chars(data: str) -> str:
    return ''.join(c for c in data if not unicodedata.category(c).startswith('C'))

def image_read_exif(filename):

    exif_dict = piexif.load(str(filename))
    keys = ['Exif']
    tags_to_extract = ['FocalLength', 'LensModel', 'FNumber']
    exif_dict_out = {}

    for ifd in keys:
        for tag in exif_dict[ifd]:
            name, data = piexif.TAGS[ifd][tag]["name"], exif_dict[ifd][tag]
            if name in tags_to_extract:
                exif_dict_out[name] = data

    for tag in tags_to_extract:
        if tag not in exif_dict_out.keys():
            exif_dict_out[tag] = None
            if tag == 'FNumber':
                print("%s doesn't have Exif.Photo.FNumber set. " % (filename) + "Please fix it manually.")
            if  tag == 'FocalLength':
                print("%s doesn't have Exif.Photo.FocalLength set. " % (filename) + "Please fix it manually.")

    str_ = strip_control_chars(exif_dict_out['LensModel'].decode('utf-8', errors='ignore'))
    try:
        out_dict = {'lens_model' : str_,
                'focal_length' : float(exif_dict_out['FocalLength'][0]),
                'aperture' : float(exif_dict_out['FNumber'][0])/10. }
    except KeyError as e:
        print('Could not extract data for key: ' + str(e))
        out_dict = {}
        
    return out_dict

if __name__ == "__main__":

    test_image = Path('..') / 'test' / 'P8240349.orf'
    out = image_read_exif(test_image)
    print(out)