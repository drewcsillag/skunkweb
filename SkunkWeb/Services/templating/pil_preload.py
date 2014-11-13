#  
#  Copyright (C) 2002 Andrew T. Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/04/25 16:10:18 smulloni>
########################################################################
"""
This module exists to load the entirety of the PIL package so that
if userModuleCleanup is on, we don't whack the PIL modules
"""
PILmods = ['ArgImagePlugin', 'BdfFontFile', 'BmpImagePlugin', 'ContainerIO', 
           'CurImagePlugin', 'DcxImagePlugin', 'EpsImagePlugin',
           'FliImagePlugin', 'FontFile', 'FpxImagePlugin', 'GbrImagePlugin',
           'GdImageFile', 'GifImagePlugin', 'GimpGradientFile',
           'GimpPaletteFile', 'IcoImagePlugin', 'ImImagePlugin', 'Image',
           'ImageChops', 'ImageDraw', 'ImageEnhance', 'ImageFile',
           'ImageFileIO', 'ImageFilter', 'ImageFont', 'ImageOps',
           'ImagePalette', 'ImagePath', 'ImageSequence', 'ImageStat',
           'ImageTk', 'ImageWin', 'ImtImagePlugin', 'IptcImagePlugin',
           'JpegImagePlugin', 'McIdasImagePlugin', 'MicImagePlugin',
           'MpegImagePlugin', 'MspImagePlugin', 'OleFileIO', 'PSDraw',
           'PaletteFile', 'PcdImagePlugin', 'PcfFontFile', 'PcxImagePlugin',
           'PdfImagePlugin', 'PixarImagePlugin', 'PngImagePlugin',
           'PpmImagePlugin', 'PsdImagePlugin', 'SgiImagePlugin',
           'SunImagePlugin', 'TarIO', 'TgaImagePlugin', 'TiffImagePlugin',
           'TiffTags', 'WmfImagePlugin', 'XVThumbImagePlugin',
           'XbmImagePlugin', 'XpmImagePlugin']

for i in PILmods:
    try:
        __import__('PIL.%s' % PILmods)
    except:
        pass
