#  
#  Copyright (C) 2002 Andrew T. Csillag <drew_csillag@yahoo.com>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
#   
# $Id: UrlBuilder.py,v 1.3 2002/05/09 19:10:46 drew_csillag Exp $
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
