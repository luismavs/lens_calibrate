lens_calibrate.py
=================

Requirements
------------

The script needs the following dependencies to be installed on your system:

* python3
* python3-exiv2 ([py3exiv2](http://py3exiv2.tuxfamily.org/) >= 0.2.1)
* python3-numpy
* python3-scipy
* darktable-cli ([darktable](https://darktable.org) >= 2.4.4)
* tca_correct ([hugin](http://hugin.sourceforge.net) >= 2018)
* convert ([ImageMagick](https://www.imagemagick.org/script/index.php))

Optional:

* gnuplot

Running the calibration
-----------------------

To setup the required directory structure simply run:

    ./lens_calibrate.py init

The next step is to copy the RAW files you created to the corresponding
directories.

Once you have done that run:

    ./lens_calibrate.py distortion

This will create tiff file you can use to figure out the the lens distortion
values (a), (b) and (c) using hugin. It will also create a lenses.conf where
you need to fill in missing values.

If you don't want to do distortion corrections you need to create the
lenses.conf file manually. It needs to look like this:

    [MODEL NAME]
    maker =
    mount =
    cropfactor =
    aspect_ratio =
    type =

The values are:

* *maker*: is the manufacturer or the lens, e.g. 'FE 16-35mm F2.8 GM'
* *mount*: is the name of the mount system, e.g. 'Sony E'
* *cropfactor*: Is the crop factor of the camera as a float, e.g. '1.0' for full frame
* *aspect_ratio*: This is the aspect_ratio, e.g. '3:2'
* *type*: is the type of the lens, e.g. 'normal' for rectilinear lenses. Other
  values are: stereographic, equisolid, stereographic, panoramic or fisheye.

If you want TCA corrections run:

    ./lens_calibrate.py tca

If you want vignetting corrections run:

    ./lens_calibrate.py vignetting

Once you have created data for all corrections you can generate an xml file
which can be consumed by lensfun. Just call:

    ./lens_calibrate.py generate_xml

Using and testing your calibration
----------------------------------

To use the data in your favourite software you just have to copy the generated
lensfun.xml file to:

    ~/.local/share/lensfun/


Send your data to lensfun
-------------------------

If you wonder if your lens is supported check the lens database at:

https://wilson.bronger.org/lensfun_coverage.html

The database is updated daily.

To add lens data to the project please open a bug at:

https://sourceforge.net/p/lensfun/features/
