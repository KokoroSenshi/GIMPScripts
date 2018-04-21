#!/usr/bin/env python

#gimp_selection_border is useful idea... not always though, e.g. if box inner edge isn't consistent for a selection
#hmm...https://duckduckgo.com/?q=gimp+python+loop+over+all+pixels
##http://shallowsky.com/blog/gimp/pygimp-pixel-ops.html
##idea: exclude rows of identical pixels to save time?
#^pixel level (pixel region) operations = slow!!!?
# e.g. prev link and just below both comment on tiles or storing into arrays as faster
# http://registry.gimp.org/node/28123
#https://wiki.python.org/moin/WhileLoop

#Identify the foreground color and convert to the string needed for comparing with each pixel (instead of converting either the fb color to str or pixel color to RGBAlpha in the loop, and wasteful computation)

#Idea: identify ALL CORNERS!!! or rather, identify top left, then strictly right and down to find next corners
# Note that need 4 pixels, three of which are the bg color; the sprite pixel could be any color/alpha  
#Human: First sample the bg color and make foreground (fg) 
#Next, scan rightward, then downward all pixels until fg then not, then check above pixels for fg-fg (note that scanning for fg-fg then checking below pixels will get too many useless hits I think)
#Then scan down until fg again then right until fg again, then construct selection
#(alternative is select fg then check pixels selected/not)

#Identify the foreground color and convert to the string needed for comparing with each pixel (instead of converting either the fb color to str or pixel color to RGBAlpha in the loop, and wasteful computation)

#the R,G,B,Alpha is the ord(pixel[n]) for n=0,1,2,3 respectively

#####Testing lines:
#layer = gimp.image_list()[0].layers[0]
#tilee = layer.get_tile(False,0,0)
#tilee[0,0] = '3a\xa8\xff'
#layer.flush() #Color picker will work right
#layer.merge_shadow(True) #?
#layer.update(0, 0, layer.width, layer.height) #Looks right when viewed
#ord(tilee[0,0][0])
#str(ord(tilee[0,0][0]))
#####

#http://stackoverflow.com/questions/730764/try-except-in-python-how-do-you-properly-ignore-exceptions#
#https://wiki.python.org/moin/HandlingExceptions

#try: #Because it's nice to catch when something unexpected happens and respond
#Determine grid of tiles #if 20, range(...) is 0 to 19? #need int to do range()
#layer.get_tile(False, yt, xt) #False for 'off the shadow buffer', whatever that is
#current_pixel = current_tile[x,y] #Yes, (x,y), I believe (location x units right and y units down of top-left corner of the square/pixel?)#read: Tile Mapping Behaviour at http://www.gimp.org/docs/python/index.html

#(i.e. current tile is layer.get_tile(False, yt, xt)[x,y])
#(location is by tile then pixel - location is tile_num * 64 + pixel_num)

#TODO: clean out educational notes and tidy comments

#Useful instead of restarting GIMP: 
#>>> import pdb
#>>> reload(pdb)
#but... breaks use of pdb.___ !?!?
#OR: if run through console (at least), no need to refresh
#^didn't actually do anything?

#>>> pdb.python_fu_spritesheet_extract(gimp.image_list()[0], gimp.image_list()[0].layers[0])

#First run: caught all 554 sprites, (counted and summed in Excel myself)
#However, some sprites are cut-off on the right side (x-dir)! Larger ones are fine, so not size related? Only the right edge ones are messed up? Even when I swap it to scan tiles row by row. Even when I replace all else by boundary color - it must be something about the position and my code... Not boundary color related.
#If I leave only the info box the Sprite Ripper put, then it encounters an exception in fact... when with the whole lot it's fine...
##oh, I see... it doesn't manage to calculate sprite_width (the error is referencing sprite_width before assignment)
##Still happens when I transpose the spritesheet, i.e. the issue would occurs in both x and y directions
##confirmed that foundx == False on error, using gimp.message on exception to display it
##AH... maybe it isn't checking the last column of pixels! off-by-one?
##(Image/configure grid to set to 64x64, noticed that none of the pixels along edge aren't checked when calculating sprite width/height? - though the code looks right... tried to increase num_w_tiles by one and it seems to work)
##^Found the issue - integer division (in Python 2.x, though not 3.0) gives integer instead of float 
#AT FIRST decided to float the TILE_..... constants but that causes issues... so I'll only float only for that calculation

from gimpfu import *
from math import *

def spritesheet_extract(img, layer) :
	''' Based on assumption of rectangle sprite regions + boundary color borders top-left and bottom-right of sprites + boundary color is foreground color http://www.spriters-resource.com/fullview/68256/
	
	Parameters:
	img   : image  The current image.
	layer : layer  The layer of the image that is selected.
	'''
	
	# Initializes the progress bar
	gimp.progress_init("Starting spritesheet extraction on " + layer.name + "...")
	
	# Makes an undo group, so undo will undo the whole operation (saves undo-recording effort?)
	img.undo_group_start()
	
	#TEMP: Give layer alpha #Ignore non-alpha channels
	layer.add_alpha()
	
	#Convert foreground color to string form - to compare with each pixel
	fg_tuple = gimp.get_foreground()
	fg_string = chr(fg_tuple[0]) + chr(fg_tuple[1]) + chr(fg_tuple[2]) + chr(fg_tuple[3]) #e.g. (50,97,168,255) is '2'+'a'+'\xa8'+'\xff'
	
	#store tile dimensions
	TILE_WIDTH = gimp.tile_width()
	TILE_HEIGHT = gimp.tile_height()
	
	#The main program: to identify top-left corners (of sprites), the dimensions of such sprites, and create a selection to float to new layer
	try:
		#Determine dimensions of tile grid
		num_w_tiles = int(ceil(layer.width / float(TILE_WIDTH)))
		num_h_tiles = int(ceil(layer.height / float(TILE_HEIGHT)))
		
		#Iterate over tiles (starts top-left at (0,0), counting right & down?)
		for yt in range(num_h_tiles):
			for xt in range(num_w_tiles):
				#Update progress bar at each tile
				gimp.progress_update(float(yt*num_w_tiles + xt) / float(num_w_tiles*num_h_tiles))
				
				#Store current tile
				current_tile = layer.get_tile(False, yt, xt)
				
				#Iterate over the tile's pixels (height/width starting from 0; matches tile's 2-tuple array of pixels)
				for y in range(current_tile.eheight):
					for x in range(current_tile.ewidth):
						
						#First, locate a top-left corner (4 pixels)
						current_pixel = current_tile[x,y] #From (0,0), counting right/down (x/y)
						
						#If sprite pixel (not fg), see if top left 3 pixels are fg; if x or y is 0, then need to move to preceding tile(s); (don't overthink efficiency yet)
						if (current_pixel != fg_string) : #If not bg color (i.e. is sprite pixel)
							
							is_corner = False
							 #(btw left tile = inner tile => (TILE_######-1) will always be right)(except if leftmost)
							if x == 0 : # X|E
								if xt == 0 or fg_string == layer.get_tile(False, yt, xt-1)[TILE_WIDTH-1,y] : #check l; but first, if image's leftmost pixel, then is sprite
									if y == 0 : 
										# -+- 
										# D|E
										if yt == 0 or fg_string == layer.get_tile(False, yt-1, xt)[x,TILE_HEIGHT-1] == layer.get_tile(False, yt-1, xt-1)[TILE_WIDTH-1,TILE_HEIGHT-1] : #check t then tl; but first, if image's topmost pixel, then is sprite
											is_corner = True
									else : #if y != 0:
										# X|X
										# D|E
										if fg_string == current_tile[x,y-1] == layer.get_tile(False, yt, xt-1)[TILE_WIDTH-1,y-1] : #check t then tl
											is_corner = True
							else: #if x != 0: # |XE
								if fg_string == current_tile[x-1,y] : #check l
									if y == 0 :
										# +--
										# |DE
										if yt == 0 or fg_string == layer.get_tile(False, yt-1, xt)[x,TILE_HEIGHT-1] == layer.get_tile(False, yt-1, xt)[x-1,TILE_HEIGHT-1] : #check t then tl; but first, if image's topmost pixel, then is sprite
											is_corner = True
									else : #if y != 0:
										# XX
										# DE
										if fg_string == current_tile[x,y-1] == current_tile[x-1,y-1] : #check t then tl
											is_corner = True
							
							if (is_corner) : #If the current pixel is a sprite's corner pixel
								
								#Find sprite edges by checking rightward and downward
								#( range(1,3) = [1,2]		range(3) = [0,1,2] )
								#Iterate over tiles and pixels in x-dir
								foundx = False
								for pixx in range(x+1,current_tile.ewidth): #if x is last pixel, then get [] i.e. do nothing!?
									if current_tile[pixx,y] == fg_string : 
										sprite_width = (pixx - x) #e.g. if x==62 (!fg), pixx==63 is fg: sprite_width is 1 pixel
										foundx = True
										break
								if foundx == False: 
									for tilex in range(xt+1,num_w_tiles):
										this_tile = layer.get_tile(False, yt, tilex)
										for pixx in range(this_tile.ewidth):
											if this_tile[pixx,y] == fg_string : 
												sprite_width = (TILE_WIDTH-x) + (TILE_WIDTH)*(tilex - 1 - xt) + (pixx)
												#^e.g. if TILE_WIDTH=3,xt=1,x=1 (!fg), tilex=3,pixx=2 if fg: 
												#sprite_width is 3-1+3*(3-1-1)+2=7: OOO OXX XXX XXO (pixx is the first NON-sprite pixel)
												foundx = True
												break
										if foundx: 
											break
										##elif tilex == num_w_tiles-1 : #If still didn't find end of sprite, must stop at at the image's edge 
										##	sprite_width = (TILE_WIDTH-x) + (TILE_WIDTH)*(tilex - 1 - xt) + (this_tile.ewidth-1)
								
								#Iterate over tiles and pixels in y-dir
								foundy = False
								for pixy in range(y+1,current_tile.eheight): #if y is last pixel, then get [] i.e. do nothing!?
									if current_tile[x,pixy] == fg_string : 
										sprite_height = (pixy - y) #e.g. if y==62 (!fg), pixy==63 is fg: sprite_width is 1 pixel
										foundy = True
										break
								if foundy == False: 
									for tiley in range(yt+1,num_h_tiles):
										this_tile = layer.get_tile(False, tiley, xt)
										for pixy in range(this_tile.eheight):
											if this_tile[x,pixy] == fg_string : 
												sprite_height = (TILE_HEIGHT-y) + (TILE_HEIGHT)*(tiley - 1 - yt) + (pixy)
												#^e.g. if TILE_HEIGHT=3,yt=0,y=1 (!fg), tiley=2,pixy=2 if fg: 
												#sprite_width is 3-1+3*(2-1-0)+2=7: OXX XXX XXO (pixy is the first NON-sprite pixel)
												foundy = True
												break
										if foundy:
											break
										##elif tiley == num_h_tiles-1 : #If still didn't find end of sprite, must stop at at the image's edge 
										##	sprite_height = (TILE_HEIGHT-y) + (TILE_HEIGHT)*(tiley - 1 - yt) + (this_tile.eheight-1) 
								
								#(continuing operations on the spite of the pixel that is its corner:)
								#Create selection based on this pixel location and sprite_width and sprite_height found
								pdb.gimp_image_select_rectangle(img, 2, TILE_WIDTH*xt+x, TILE_HEIGHT*yt+y, sprite_width, sprite_height)
								#Float it then to new layer
								pdb.gimp_floating_sel_to_layer(pdb.gimp_selection_float(layer,0,0))
		
	except Exception as error_code: #except = on 'try' failing, if error type is Exception, store the error info(?) in variable err (as a number?)
		gimp.message( "Unexpected error: " + str(error_code) )
		gimp.message("xt = "+str(xt))
		#gimp.message("Corner: x pos = "+str(TILE_WIDTH*xt+x)+", y pos = "+str(TILE_HEIGHT*yt+y))
		#gimp.message("Last checked: x pos = "+str(TILE_WIDTH*xt+x)+", y pos = "+str(TILE_HEIGHT*yt+y))
		#gimp.message( "Did you remember to choose the boundary color?")
	
	
	
	#Then proceed again from the top-right identified corner and loop.
	
	#ENDNOTE: identify all sprites first then split off, or same time? same time I'll try first at least - as for to-image-ing, separate, in case of bug/issues
	#Next is to convert layers to new images
	
	#Close the undo group so undo-recording is back to normal
	img.undo_group_end()
	
	#End/finish/remove the progress bar
	pdb.gimp_progress_end()
	
	
	
register(
	"python_fu_spritesheet_extract",					# name
	"Spritesheet extractor",							# blurb
	"Extracts sprites from certain spritesheets",		# help
	"KokoroSenshi",										# author
	"KokoroSenshi - CC BY-SA",							# copyright
	"2016",												# date
	"<Image>/Scripts/KScripts/Spritesheet extractor",	# menupath
	"*",												# imagetypes
	[],													# params
	[],													# results
	spritesheet_extract)								# function - Don't forget this!!

main()													# Don't forget this!