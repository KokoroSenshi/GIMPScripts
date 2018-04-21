#!/usr/bin/env python

#Basic reference for gimp.* methods: https://www.gimp.org/docs/python/index.html
#Main reference: https://developer.gimp.org/api/2.0/libgimp/index.html

# When running in console: 
#pdb.python_fu_spritesheet_extract_2(gimp.image_list()[0], gimp.image_list()[0].layers[0])

# For minor testing:
#img = gimp.image_list()[0]
#layer = gimp.image_list()[0].layers[0]

from gimpfu import *
#from math import *

def spritesheet_extract_2(img, layer) :
	''' Assumes top-left pixel is the color of the non-sprite surrounding region.
	    Warning: Can't seem to use tiles, since removing the black/sprite region won't update on the tiles I'm iterating through no matter how I try to flush, refetch etc. ...
	
	Parameters:
	img   : image  The current image.
	layer : layer  The layer of the image that is selected.
	'''
	
	# Initializes the progress bar
	gimp.progress_init("Starting spritesheet extraction on " + layer.name + "...")
	
	# Makes an undo group, so undo will undo the whole operation (saves undo-recording effort?)
	img.undo_group_start()
	
	##Create a top layer of a solid color (black I guess)
	
	cover_layer = gimp.Layer(img, "Cover Layer", layer.width, layer.height, RGB_IMAGE, 100, NORMAL_MODE) 
	#(image, name, width, height, type (pick a constant), opacity, mode (pick a constant))
	#NOTE: that it has no alpha, so deleting will leave white, not transparent
	
	img.add_layer(cover_layer, 0)
	#(layer, position)
	
	#https://stackoverflow.com/a/20483571
	#https://developer.gimp.org/api/2.0/libgimp/libgimp-gimpimageselect.html#gimp-image-select-contiguous-color
	##Use fuzzy select on top corner of starting layer with 0 threshold and delete the selection from top layer
	pdb.gimp_context_set_antialias(False)
	pdb.gimp_context_set_feather(False)
	###pdb.gimp_context_set_feather_radius(0,0) #No need?
	pdb.gimp_context_set_sample_merged(False)
	pdb.gimp_context_set_sample_criterion(SELECT_CRITERION_COMPOSITE)
	pdb.gimp_context_set_sample_threshold(0)
	pdb.gimp_context_set_sample_transparent(True)
	pdb.gimp_image_select_contiguous_color(img, CHANNEL_OP_REPLACE, layer, 0, 0) #Select (from starting layer) the empty space around sprites using top-left pixel
	pdb.gimp_edit_clear(cover_layer) #delete selection from the cover layer
	
	##No change in settings (gimp_context_*) for gimp_image_select_contiguous_color for the following code
	
	##Then it begins below...
	
	#At each pixel, if it's part of a sprite, fuzzy select it and float to new layer
	try:
		layer_width = cover_layer.width
		layer_height = cover_layer.height
		
		#Store the first pixel (whose rgba color was used to determine the non-sprite area)
		non_sprite_pixel = pdb.gimp_drawable_get_pixel(cover_layer,0,0)
		
		for y in range(layer_height): #Iterate over the tile's pixels (going left-right then top-bottom)
			for x in range(layer_width):
				#Store current pixel
				current_pixel = pdb.gimp_drawable_get_pixel(cover_layer,x,y)
				
				if (current_pixel != non_sprite_pixel) : #Thus, a sprite
					
					#Select the sprite
					pdb.gimp_image_select_contiguous_color(img, CHANNEL_OP_REPLACE, cover_layer, x, y)
					
					#Delete this region from cover_layer so this sprite doesn't get recounted
					pdb.gimp_edit_clear(cover_layer) #delete selection from the cover layer
					
					#Float the selection then to new layer
					pdb.gimp_floating_sel_to_layer(pdb.gimp_selection_float(layer,0,0))
					
				
				#Update progress bar
				gimp.progress_update( (y*layer_width+x) / (layer_width*layer_height) )
				
		
	except Exception as error_code: #For the Exception error type; the Exception is assigned to the variable error_code
		gimp.message( "Unexpected error: " + str(error_code) )
		gimp.message("(xt, yt) = ("+str(xt)+" "+str(yt)+")") #The tile at which the Exception occurred
	
	#NOTE: Have to use export layers plugin after this, unless I can do the same thing here..
	
	#Close the undo group so undo-recording is back to normal
	img.undo_group_end()
	
	#End/finish/remove the progress bar
	pdb.gimp_progress_end()
	
	
	
register(
	"python_fu_spritesheet_extract_2",					# name
	"Spritesheet extractor 2",							# blurb
	"Extracts sprites from certain spritesheets",		# help
	"KokoroSenshi",										# author
	"KokoroSenshi - CC BY-SA",							# copyright
	"2017",												# date
	"<Image>/Scripts/KScripts/Spritesheet extractor 2",	# menupath
	"*",												# imagetypes
	[],													# params
	[],													# results
	spritesheet_extract_2)								# function - Don't forget this!!

main()													# Don't forget this!