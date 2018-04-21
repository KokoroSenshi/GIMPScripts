#!/usr/bin/env python
#http://registry.gimp.org/node/28124
	#pdb.gimp_invert(layer) refers to gimp-invert in the procedure list
	#so... everything I need is there, except have "-" instead of "_" and no "pdb." is that why (not exactly \/)
#img : image => img is of type 'image'? Or does it mean img=image=current? 
	# type help(gimpfu) after import gimpfu etc. for info (not useful tho?)
	# As a menu item, the img and layer default to current (?)
	#item can refer to not just layer/image/etc. ?
	#gimp.asdf refers to the gimp module that comes with gimpfu; use dir(gimp) to see, e.g. Layer (note capital L)
#pdb doesn't work for new layer stuff..... so use gimp.Layer stuff...(?)
	#http://myvirtualbrain.blogspot.com.au/2012/06/gimp-python-fu-very-basics.html
	#Makes sense now (tho isn't relev?): http://stackoverflow.com/questions/12608210/gimp-2-8-plugin-script-how-do-you-add-a-new-grouplayer
#omfg, from ##put None, not 0! The pdb listing info lied? Refer pdb.gimp_image_insert_layer at http://stackoverflow.com/questions/13882808/gimp-python-fu-nested-group-layers
	#hmm http://developer.gimp.org/api/2.0/libgimp/libgimp-gimplayer.html#gimp-layer-new
#Tried to make a new layer, but is it easier to just copy then clear? (refer bundle of scripts)
# ok, I give up on gimp_layer_new; my attempts makes it break, even.
	#sometimes comments will have stuff that messes things up /somehow/ ........ so keep versions I suggest
# Copy then clear, as in test-discolour-layer-v4.py
	#example code for img. and gimp. ? http://gimpforums.com/thread-gimp-script-help
	#Has gimp module info, e.g. img.add_layer #http://www.gimp.org/docs/python/index.html
	#^ under Plugin Framework, " the first parameter to the plugin function should be the image, and the second should be the current drawable"
	#^ i.e. first two params are automatically the current image then drawable (e.g. image or a pasted-but-not-floated thing?)
#Color are in ( , , ) form, as it now doesn't fail to load+does the color change; deduced from: http://stackoverflow.com/questions/22622370/gimp-script-fu-how-can-i-set-a-value-in-the-colormap-directly
#Btw, you know it failed to load since menu item isn't there.
#btw if explicit need img etc: 
	# >>> image = gimp.image_list()[0]
	# >>> layer = image.layers[0]
	# >>> gimp.pdb.python_fu_bg_removal_setup(image, layer) #uses the name from the "register"
#According to error when tried to do add_layer on bg_layer twice , 'gimp-image-insert-layer' is the same as img.Layer?
#IMPORTANT### Turns out using spaces instead of [tab] caused most of the issues earlier??????? (those that led me to use the non pdb. ones?
from gimpfu import *

def bg_removal_setup(img, layer) :
	''' Does the usual stuff when doing Zelda Wiki background removal
	
	Parameters:
	img   : image  The current image.
	layer : layer  The layer of the image that is selected.
	'''
	#Useful? pdb.gimp_image_raise_item_to_top(image, item)
	layer_copy = pdb.gimp_layer_copy(layer, TRUE)       #makes the alpha channeled version
	pdb.gimp_item_set_visible(layer, FALSE)             #hide original ##works!
	pdb.gimp_image_insert_layer(img, layer_copy, None, 1)  #inserts the alpha chanelled ver to position 1 ##put None, not 0! The pdb listing info lied?
	#this causes problems? Was instead due to spaces vs [tab]s?#bg_layer = pdb.gimp_layer_new(img, 5, 5, 0, "bgZW", 100, 0) #makes new layer bg_layer ##did I forget that this only makes, not insert?
	foreground = pdb.gimp_context_get_foreground()
	pdb.gimp_context_set_foreground((23,69,110))
	bg_layer = gimp.Layer(img, "bgZW", layer.width, layer.height, layer.type, layer.opacity, layer.mode) #creates with foreground?
	img.add_layer(bg_layer, 2)	#creates with black (NOT foreground)(?)#inserts the bg layer to position 2
	#no need now since ^ #pdb.gimp_image_insert_layer(img, bg_layer, None, 2)  #inserts the bg layer to position 2
	added_bg_layer = pdb.gimp_image_get_layer_by_name(img, "bgZW")
	#issue was due to [space]s vs [tab]? #img.add_layer(added_bg_layer, 2) #<-to test if the get_layer_.. works
	pdb.gimp_drawable_fill(added_bg_layer, 0)
	alpha_layer = pdb.gimp_image_get_layer_by_name(img, layer.name + " copy")
	pdb.gimp_image_set_active_layer(img, alpha_layer)



register(
	"python_fu_bg_removal_setup",					# name
	"Background removal setup",						# blurb
	"Does the usual stuff for bg removal",			# help
	"KokoroSenshi",									# author
	"KokoroSenshi - CC BY-SA",						# copyright
	"2016",											# date
	"<Image>/Scripts/KScripts/BG Removal Setup",	# menupath
	"*",											# imagetypes
	[],												# params
	[],												# results
	bg_removal_setup)								# function

main()												# Don't forget this!
