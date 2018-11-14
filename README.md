lens_calibrate.py
=================

To setup the required directory structure simply run:

    ./lens_calibrate.py init

The next step is to copy the RAW files you created to the corresponding
directories.

Once you have done that run:

    ./lens_calibrate.py distortion

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

To use the data in your favourite software you just have to copy the generated
lensfun.xml file to:

    ~/.local/share/lensfun/

Create a bug report or pull request to add the lens to the project at:

https://sourceforge.net/p/lensfun/bugs/
https://github.com/lensfun/lensfun/
