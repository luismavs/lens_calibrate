lens_calibrate.py
=================

Tutorial
--------

You can find a complete tutorial about lens calibration and the use of the
lens_calibrate.py script here:

https://pixls.us/articles/create-lens-calibration-data-for-lensfun/

Requirements
------------

The script needs the following dependencies to be installed on your system:

* python3
* python3-exiv2 ([py3exiv2](http://py3exiv2.tuxfamily.org/) >= 0.2.1)
* python3-numpy
* python3-scipy
* python3-PyPDF2
* darktable-cli ([darktable](https://darktable.org) >= 3.0.0)
* tca_correct ([hugin](http://hugin.sourceforge.net) >= 2018)
* convert ([ImageMagick](https://www.imagemagick.org/script/index.php) or [GraphicsMagick](http://www.graphicsmagick.org))
* gnuplot

Packages
--------

Packages for most major distributions are available at:

https://software.opensuse.org/download.html?project=graphics:darktable&package=lens_calibrate

Installing dependencies
-----------------------

If one of the python modules is not available you can do the following to
install them on your system:

* Install the packages python3-pip and python3-venv (e.g. with apt-get)
* Change to directory where lens_calibrate.py is located
* Setup a virtual env directory using: `python3 -m venv .venv`
* Source the environment with: `source .venv/bin/activate`
* Install missing packages with e.g. `pip3 install py3exiv2 numpy scipy PyPDF2`
* Run the calibration script like documented below

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

    [MODEL_NAME]
    maker =
    mount =
    cropfactor =
    aspect_ratio =
    type =

The values are:

* *MODEL_NAME*: is the lens model 'FE 16-35mm F2.8 GM'
* *maker*: is the manufacturer or the lens, e.g. 'Sony'
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

To add lens data to the lensfun project first run:

    ./lens_calibrate.py ship

This will create a file `lensfun_calibration.tar.xz` including the xml file and
the plots showing if the calibration data is valid.

With that tarball please open a bug at

* https://github.com/lensfun/lensfun/issues/

and provide the `lensfun_calibration.tar.xz` file.
