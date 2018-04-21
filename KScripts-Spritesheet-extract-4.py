#!/usr/bin/env python

#Basic reference for gimp.* methods: https://www.gimp.org/docs/python/index.html
#Main reference: https://developer.gimp.org/api/2.0/libgimp/index.html
#Guide: https://www.gimp.org/docs/plug-in/sect-tiles.html
# When running in console: 
#pdb.python_fu_spritesheet_extract_2(gimp.image_list()[0], gimp.image_list()[0].layers[0])

#Pro tip: Even undo grouping still drags things down: https://stackoverflow.com/a/28086967

# For minor testing:
#img = gimp.image_list()[0]
#layer = gimp.image_list()[0].layers[0]

from gimpfu import *
from math import *

def spritesheet_extract_4(img, layer) :
	''' Assumes top-left pixel is the color of the non-sprite surrounding region.
	    Warning 1: Can't seem to use tiles, since removing the black/sprite region won't update on the tiles I'm iterating through no matter how I try to flush, refetch etc. ...
	    Note: Doing gimp_drawable_get_pixel was too slow for large spritesheets (all spritesheets are large...)
	    Note: Instead of reselecting the sprite regions, subtract the sprite regions that are done
	    Note: Though, we still need the extra layer to do individual sprite selection
	
	Parameters:
	img   : image  The current image.
	layer : layer  The layer of the image that is selected.
	'''
	
	#Initializes the progress bar
	gimp.progress_init("Starting spritesheet extraction on " + layer.name + "...")
	
	#Disable undo to make it faster
	pdb.gimp_image_undo_disable(img)
	
	#Change the image color mode to RGB to match cover_layer 
	pdb.gimp_image_convert_rgb(img)
	
	##Create a top layer of a solid color (black I guess)
	
	cover_layer = gimp.Layer(img, "Cover Layer", layer.width, layer.height, RGB_IMAGE, 100, NORMAL_MODE) 
	#(image, name, width, height, type (pick a constant), opacity, mode (pick a constant))
	#NOTE: that it has no alpha, so deleting will leave white, not transparent
	
	img.add_layer(cover_layer, 0)
	#(layer, position)
	
	#sprite_pixel = pdb.gimp_drawable_get_pixel(cover_layer,0,0)
	#sprite_pixel_color = pdb.gimp_image_pick_color(img, cover_layer, 0, 0, False, False, 0) #gives a triplet
	
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
	
	#Select the sprite regions
	pdb.gimp_selection_invert(img)
	
	#Save the sprite regions to a channel to work with/on
	remaining_sprite_regions = pdb.gimp_selection_save(img)
	
	##No change in settings (gimp_context_*) for gimp_image_select_contiguous_color for the following code
	
	#store tile width, then number of tiles across
	TILE_WIDTH = gimp.tile_width()
	num_w_tiles = int(ceil(layer.width / float(TILE_WIDTH)))
		
	#Fuzzy select each sprite and float to new layer
	try:
		layer_width = cover_layer.width
		layer_height = cover_layer.height
		
		#Store the first pixel (whose rgba color was used to determine the non-sprite area)
		#non_sprite_pixel = pdb.gimp_drawable_get_pixel(cover_layer,0,0)
		
		while True: #While there's a sprite region to harvest from:
			
			#It should be that the sprite regions are already loaded
			
			#Check that there's a selection, and locate a pixel of the sprite regions
			non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(img) #(Is there a selection?) (top-left) (bottom-right)
			
			if non_empty == 0: #0 if empty (no selection)
				break #No sprite regions left
			
			#else there are sprite regions:
			#Use a tile cache so the plugin knows to cache whatever tiles it accesses, instead of refetching each pixel? No need to use get_tile explicitly..?
			gimp.tile_cache_ntiles(num_w_tiles)
			for x in range(x1,x2):
				if pdb.gimp_selection_value(img, x, y1) > 0:
					#gimp.message(str(pdb.gimp_selection_value(img, x, y1)))
					#Select the sprite
					pdb.gimp_image_select_contiguous_color(img, CHANNEL_OP_REPLACE, cover_layer, x, y1)
					
					#Float the selection then to new layer
					pdb.gimp_floating_sel_to_layer(pdb.gimp_selection_float(layer,0,0))
					
					#Reload the sprite regions
					pdb.gimp_image_select_item(img, CHANNEL_OP_REPLACE, remaining_sprite_regions)
					
					#Subtract this sprite from the selection
					pdb.gimp_image_select_contiguous_color(img, CHANNEL_OP_SUBTRACT, cover_layer, x, y1)
					
					#Resave the sprite regions
					remaining_sprite_regions = pdb.gimp_selection_save(img)
					
					#Update progress bar
					#gimp.message( str((1.0*y1*layer_width+x) / (layer_width*layer_height)) )
					gimp.progress_update( (1.0*y1*layer_width+x) / (layer_width*layer_height) )
					
					break
					
			
		
	except Exception as error_code: #For the Exception error type; the Exception is assigned to the variable error_code
		gimp.message( "Unexpected error: " + str(error_code) )
		gimp.message("(xt, yt) = ("+str(xt)+" "+str(yt)+")") #The tile at which the Exception occurred
	
	#NOTE: Have to use export layers plugin after this, unless I can do the same thing here..
	
	#Re-enable undo
	pdb.gimp_image_undo_enable(img)
	
	#End/finish/remove the progress bar
	pdb.gimp_progress_end()
	
	
register(
	"python_fu_spritesheet_extract_4",					# name
	"Spritesheet extractor 4",							# blurb
	"Extracts sprites from certain spritesheets",		# help
	"KokoroSenshi",										# author
	"KokoroSenshi - CC BY-SA",							# copyright
	"2017",												# date
	"<Image>/Scripts/KScripts/Spritesheet extractor 4",	# menupath
	"*",												# imagetypes
	[],													# params
	[],													# results
	spritesheet_extract_4)								# function - Don't forget this!!

main()													# Don't forget this!