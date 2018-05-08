"""
 ------------------------------------------------------------------- 
  This is UNPUBLISHED PROPRIETARY SOURCE CODE of Three Blue Monkeys  
  Inc.  The contents of this file may not be disclosed to third      
  parties, copied or duplicated in any form, in whole or in part,    
  without the prior written permission of Three Blue Monkeys.        
 ------------------------------------------------------------------- 


Image processor that uses Image Magick command line to process images for 
use on jflorist website. Creates 4 sizes of images for website use.


Miscellaneous Information:
Alternative sweet spots for sharpening resize into landscape and portrait images:   
Sweet spot 1:  1x1+1.5+.08
Sweet spot 2:  2x2+1+.08
Sweet spot 3:  1x2+1.5+.1



JFlorist old settings:
unsharpMaskImage(0.5, 1, 1.0, 0.02);
"""


import os
import argparse
import subprocess
import math


#CONVERT_PATH = '/usr/bin/convert'
CONVERT_PATH = 'convert'
WIZARD_PATH = 'home/jflori5/public_html/wizard'


def get_width(img_path):
    """Return width of image in integer number of pixels."""
    width_command = '-ping -format "%w" info:'
    command = CONVERT_PATH + ' ' + img_path + ' ' + width_command
    width = subprocess.check_output(command, shell=True)
    return int(width)
    
  
def get_height(img_path):
    """Return height of image in integer number of pixels."""
    height_command = '-ping -format "%h" info:'
    command = CONVERT_PATH + ' ' + img_path + ' ' + height_command
    height = subprocess.check_output(command, shell=True)
    return int(height)
    
    
def get_img_size(img_path):
    """Return array of width & height of image in integer number of pixels."""
    width = get_width(img_path)
    height = get_height(img_path)
    return [width, height]
    
    
def get_rgb_of_pixel(img_path, coordinate):
    """Return array of image's RGB value at the x, y pixel coordinates."""
    command = '%s %s[1x1+%d+%d] -format "%%[fx:floor(255*u.r)],%%[fx:floor(255*u.g)],%%[fx:floor(255*u.b)]" info:' % (CONVERT_PATH, 
                                                                                                                      img_path,
                                                                                                                      coordinate[0], 
                                                                                                                      coordinate[1])
    rgb = subprocess.check_output(command, shell=True)
    rgb = rgb.split(',')
    rgb = [int(x) for x in rgb]
    
    return rgb

    
def is_similar(rgb1, rgb2, acceptable_distance):
    """Return True/False depending on if RGB are within acceptable distance."""
    distance = math.sqrt(((rgb1[0] - rgb2[0]) ** 2) 
                       + ((rgb1[1] - rgb2[1]) ** 2)
                       + ((rgb1[2] - rgb2[2]) ** 2))
    if distance <= acceptable_distance:
        return True
    else:
        return False
    
    
def is_white(img_path):
    """Return True/False if image has a white background."""
    WHITE = (255, 255, 255)
    DISTANCE = 6
    
    width = get_width(img_path)
    height = get_height(img_path)
 
    rgb_top_left = get_rgb_of_pixel(img_path, (0, 0))
    if is_similar(rgb_top_left, WHITE, DISTANCE):

        rgb_top_right = get_rgb_of_pixel(img_path, (width - 1, 0))
        if is_similar(rgb_top_left, WHITE, DISTANCE):
        
            rgb_bottom_left = get_rgb_of_pixel(img_path, (0, height - 1))
            if is_similar(rgb_bottom_left, WHITE, DISTANCE):
            
                rgb_bottom_right = get_rgb_of_pixel(img_path, (width - 1, height - 1))
                if is_similar(rgb_bottom_right, WHITE, DISTANCE):
                    return True
                    
    return False
    

def process_img(img_path):
    """Create view, item, portrait, and landscape images.
    
    If the image has a white background, a temporary image is created such that
    the original image is overlayed onto a square white canvas background 
    greater than the maximum size of the width and height of the given image. 
    This new overlayed image is then processed by the different image 
    processing functions instead of the original supplied image.
    """
    
    temp_white_path = ''
    white = is_white(img_path)

    if white:
        temp_white_path = overlay_img_on_white(img_path)
        
    make_view_img(img_path, temp_white_path)
    make_item_img(img_path, temp_white_path)
    make_landscape_img(img_path, temp_white_path)
    make_portrait_img(img_path, temp_white_path)

    if temp_white_path:
        os.remove(temp_white_path)
    
    
def overlay_img_on_white(img_path):
    """Overlay image on to square white background."""
    temp_white_path = 'magick/temp_white.png'
    trim = '%s %s -fuzz 1%% -trim +repage %s' % (CONVERT_PATH, 
                                                 img_path, 
                                                 temp_white_path)
    os.system(trim)

    width = get_width(temp_white_path)
    height = get_height(temp_white_path)
    canvas_width = int(width / .9)
    canvas_height = int(height / .9)
    canvas_max = max(canvas_width, canvas_height)
    
    x_coor_overlay = int((canvas_max - width) / 2)
    y_coor_overlay = int(canvas_max - height * 1.04)
    
    make_white_bg(canvas_max, canvas_max)
    overlay = '%s magick/background.jpg %s -geometry "+%s+%s" -composite %s' % (CONVERT_PATH, 
                                                                                temp_white_path, 
                                                                                x_coor_overlay, 
                                                                                y_coor_overlay, 
                                                                                temp_white_path)
    os.system(overlay)
    os.remove('magick/background.jpg')
    
    return temp_white_path
    
    
def make_white_bg(width, height):
    """Create white canvas background image given width and height."""
    command = '%s -size %sx%s canvas:white magick/background.jpg' % (CONVERT_PATH, 
                                                                     width, height)
    os.system(command)
    
    
def make_view_img(img_path, temp_white_path):
    """Create view image of dimensions 450x450
    
    If a temporary white overlayed version of the image exist, use that 
    temporary white image to create view image instead of original image. Also, 
    if image is not square, resize will resize the largest side of image as 450 
    and keep the image proportional.
    """
    
    save_path = insert_substr(img_path, -4, 'v')
    command_format = (CONVERT_PATH, img_path, save_path)

    if temp_white_path:
        command_format = (CONVERT_PATH, temp_white_path, save_path)
        
    command = '%s ( -unsharp 2x2+3+.1 ( %s -resize 450x450 ) ) -strip -colorspace rgb -quality 92%% %s' % command_format
    os.system(command)
    
    
def make_item_img(img_path, temp_white_path):
    """Create item image of dimensions 275x275
    
    If a temporary white overlayed version of the image exist, use that 
    temporary white image to create view image instead of original image. Also, 
    if image is not square, resize will resize the largest side of image as 275
    and keep the image proportional.
    """
    
    save_path = insert_substr(img_path, -4, 'b')
    command_format = (CONVERT_PATH, img_path, save_path)

    if temp_white_path:
        command_format = (CONVERT_PATH, temp_white_path, save_path)
        
    command = '%s ( -unsharp 2x2+3+.1 ( %s -resize 275x275 ) ) -strip -colorspace rgb -quality 92%% %s' % command_format
    os.system(command)
    
    
def make_landscape_img(img_path, temp_white_path):
    """Create landscape image of dimensions 105x130
    
    If a temporary white overlayed version of the image exist, use that 
    temporary white image to create view image instead of original image.
    """
    
    save_path = insert_substr(img_path, -4, 'm')
    temp_landscape_path = 'magick/temp_landscape.png'
    
    if temp_white_path:
        trim = '%s %s -fuzz 1%% -trim +repage %s' % (CONVERT_PATH,
                                                     temp_white_path, 
                                                     temp_landscape_path)
        os.system(trim)
        resize_to_101_width = '%s %s -resize 101x %s' % (CONVERT_PATH, 
                                                         temp_landscape_path, 
                                                         temp_landscape_path)
        os.system(resize_to_101_width)
        
        # If resized image height is odd number of pixels, crop off 1 pixel
        new_height = get_height(temp_landscape_path)
        if (new_height % 2 != 0):
            crop_off_1_pixel = '%s %s -crop "101x%s+0+0" +repage %s' % (CONVERT_PATH, 
                                                                        temp_landscape_path, 
                                                                        new_height - 1, 
                                                                        temp_landscape_path)
            os.system(crop_off_1_pixel)
            
        height_border = abs(int((130 - get_height(temp_landscape_path))/2))
        add_border_save = '%s ( -unsharp 1x2+1.5+.08 ( %s -bordercolor white -border 2x%s ) ) -strip -colorspace rgb -quality 98%% %s' % (CONVERT_PATH, 
                                                                                                                                          temp_landscape_path, 
                                                                                                                                          height_border, 
                                                                                                                                          save_path)
        os.system(add_border_save)
    else:
        resize_to_130_height = '%s %s -resize x130 %s' % (CONVERT_PATH, 
                                                          img_path, 
                                                          temp_landscape_path)
        os.system(resize_to_130_height)
        width_crop = int((get_width(temp_landscape_path) - 105) / 2)
        crop_105_130_save = '%s ( -unsharp 1x2+1.5+.08 ( %s -crop "105x130+%s+0" +repage ) ) -strip -colorspace rgb -quality 98%% %s' % (CONVERT_PATH, 
                                                                                                                                         temp_landscape_path, 
                                                                                                                                         width_crop, 
                                                                                                                                         save_path)
        os.system(crop_105_130_save)
    
    os.remove(temp_landscape_path)
        
        
def make_portrait_img(img_path, temp_white_path):
    """Create portrait image of dimensions 105x130
    
    If a temporary white overlayed version of the image exist, use that 
    temporary white image to create view image instead of original image.
    """
    
    save_path = insert_substr(img_path, -4, 'n')
    temp_portrait_path = 'magick/temp_portrait.png'
    
    if temp_white_path:
        trim = '%s %s -fuzz 1%% -trim +repage %s' % (CONVERT_PATH, 
                                                     temp_white_path, 
                                                     temp_portrait_path)
        os.system(trim)
        resize_to_120_height = '%s %s -resize x120 %s' % (CONVERT_PATH, 
                                                          temp_portrait_path, 
                                                          temp_portrait_path)
        os.system(resize_to_120_height)

        # If resized image width is even number of pixels, crop off 1 pixel
        new_width = get_width(temp_portrait_path)
        if (new_width % 2 == 0):
            crop_off_1_pixel = '%s %s -crop "%sx120+0+0" +repage %s' % (CONVERT_PATH, 
                                                                        temp_portrait_path, 
                                                                        new_width - 1, 
                                                                        temp_portrait_path)
            os.system(crop_off_1_pixel)
            
        width_border = abs(int((105 - get_width(temp_portrait_path))/2))
        add_border_save = '%s ( -unsharp 1x2+1.5+.08 ( %s -bordercolor white -border %sx5 ) ) -strip -colorspace rgb -quality 98%% %s' % (CONVERT_PATH, 
                                                                                                                                          temp_portrait_path,
                                                                                                                                          width_border, 
                                                                                                                                          save_path)
        os.system(add_border_save)
    else:
        resize_to_105_width = '%s %s -resize 105x %s' % (CONVERT_PATH, 
                                                         img_path, 
                                                         temp_portrait_path)
        os.system(resize_to_105_width)
        height_crop = int((get_height(temp_portrait_path) - 130) / 2)
        crop_105_130_save = '%s ( -unsharp 1x2+1.5+.08 ( %s -crop 105x130+0+%s +repage ) ) -strip -colorspace rgb -quality 98%% %s' % (CONVERT_PATH, 
                                                                                                                                       temp_portrait_path, 
                                                                                                                                       height_crop, 
                                                                                                                                       save_path)
        os.system(crop_105_130_save)
        
    os.remove(temp_portrait_path)
        
    
def insert_substr(my_string, index, substr):
    """Insert sub-string at desired index in string."""
    my_string = my_string[:index] + substr + my_string[index:] 
    return my_string  
    
    
# Create command line interface for outside programs to call
parser = argparse.ArgumentParser()
parser.add_argument('--process_img', help='Create the 4 images for jFlorist website')
parser.add_argument('--is_img_white', help='Check if the image has a white background')
parser.add_argument('--get_width', help='Get the width of image in pixels')
parser.add_argument('--get_height', help='Get the height of image in pixels')

# Process command line calls and execute appropriate functions
args = parser.parse_args()
if args.process_img:
    process_img(args.process_img)
if args.is_img_white:
    print is_white(args.is_img_white)
if args.get_width:
    print get_width(args.get_width)
if args.get_height:
    print get_height(args.get_height)
