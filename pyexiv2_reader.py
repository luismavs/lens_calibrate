#!/usr/bin/env python3

#######################################################################
#
# A script to calibrate camera lenes for lensfun
# Exif data reader using pyexiv2
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


from pyexiv2.metadata import ImageMetadata
from pyexiv2.exif import ExifTag

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