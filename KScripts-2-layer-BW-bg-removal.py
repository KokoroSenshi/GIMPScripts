#!/usr/bin/env python

#http://www.gimp.org/docs/
#https://duckduckgo.com/?q=gimp+object+documentation&t=ffsb
#https://www.gimp.org/docs/python/index.html
#http://www.jamesh.id.au/software/pygimp/
#http://www.jamesh.id.au/software/pygimp/gimp-objects.html
#http://www.jamesh.id.au/software/pygimp/support-modules.html#GIMPSHELF-MODULE
#https://duckduckgo.com/?q=up+to+date+gimp+python+fu+docuentation&t=ffsb
	#http://registry.gimp.org/node/24275
#http://wiki.gimp.org/wiki/Hacking:Plugins#Debugging_GIMP_Plug-ins
#http://myvirtualbrain.blogspot.com.au/2012/06/gimp-python-fu-very-basics.html?view=classic

# Automates the following based on bottom two layers https://graphicdesign.stackexchange.com/questions/8057/using-gimp-can-you-erase-a-color
# >>> image = gimp.image_list()[0]
# >>> layer = image.layers[0]
# >>> gimp.pdb.python_fu_2_layer_BW_bg_removal(image, layer)

# http://www.jamesh.id.au/software/pygimp/gimp-module-procedures.html
# len() gives the length
# help(gimp) is useful, eg, help(gimp.Image.merge_down)
#convert hyphens (that the pdb info may say) to underscores!
#(still haven't confirmed that the function args are the active image and layer respectively...)
#Current docs are outdated! some Layer functions used on/with an Image have been replaced by functions on/with a Layer itself! help(gimp.Layer) is useful!
#Debugging! If it shows in the menu, the structure is right,
#then if it fails to do what you want, then open gimp's python console to see where it stops (put print(asdf) statements to identify is one thing you could do)

from gimpfu import *

def remove_bg_BW(img, layer) :
	''' Does the background removal explained at  https://graphicdesign.stackexchange.com/questions/8057/using-gimp-can-you-erase-a-color
	
	Parameters:
	img   : image  The current image.
	layer : layer  The layer of the image that is selected.
	'''
	
	# Initializes the progress bar
	gimp.progress_init("Starting background removal extraction on bottom two layers...")
	
	# Makes an undo group, so undo will undo the whole operation (saves undo-recording effort?)
	img.undo_group_start()
	
	layers_array = img.layers #note that the var will therefore not change (or need to be recalculated y/n?)
	num_layers = len(img.layers)
	#Gives array of ids, which is useless(?):# num_layers, layers_array = pdb.gimp_image_get_layers(img)
	#(white above black; bottom two)
	###Add alpha to bottom two layers just in case:
	#Save + alpha-ize upper layer
	white_bg = layers_array[num_layers-2]
	white_bg.add_alpha()
	##OR:#pdb.gimp_layer_add_alpha(white_bg)
	#Save + alpha-ize lower layer
	black_bg = layers_array[num_layers-1]
	black_bg.add_alpha()
	##OR:#pdb.gimp_layer_add_alpha(black_bg)
	
	#Copy the 'black layer' for later:
	black_copy = black_bg.copy(True)
	##OR: #black_copy = pdb.gimp_layer_copy(black_bg, True)
	
	#Set 'white layer' to "difference" mode
	white_bg.mode = DIFFERENCE_MODE #<- a constant that is 6
	##OR: #pdb.gimp_layer_set_mode(white_bg, 6)
	#Merge down onto the black layer to get the desired image's alpha channel:
	alpha_channel_result = img.merge_down(white_bg, EXPAND_AS_NECESSARY)
	##OR?: #alpha_channel_result = pdb.gimp_image_merge_down(img, white_bg, EXPAND_AS_NECESSARY)
	##Eventally found image.merge_down(layer,type) using help(gimp.Image) and trying invalid arguments and reading the errors
	#Invert the result:
	pdb.gimp_invert(alpha_channel_result)
	
	#extra copy to paste into layer mask later
	alpha_channel_copy = alpha_channel_result.copy(True)
	##OR: #alpha_channel_copy = pdb.gimp_layer_copy(alpha_channel_result, True)
	
	#(alpha channel layer; bottom layer)
	#Set the alpha channel result to "divide" mode
	alpha_channel_result.mode = DIVIDE_MODE
	##OR: #pdb.gimp_layer_set_mode(alpha_channel_result, 15)
	#Merge it onto the black layer after pasting it:
	#(There should be one less layer than started with, but just in case of code changes/reuse...:)
	img.add_layer(black_copy, len(img.layers))#num_layers)
	##OR?: #pdb.gimp_image_insert_layer(img, black_copy, None, num_layers) #Use None, not 0 !?!?!?
	#(alpha channel layer > black layer; bottom 2 layers)
	alpha_on_black_result = img.merge_down(alpha_channel_result, EXPAND_AS_NECESSARY)
	##OR?: #pdb.gimp_image_merge_down(img, alpha_channel_result)
	#(resultant layer; bottom layer)
	
	#Then add layer mask to result:
	alpha_on_black_result.add_mask(alpha_on_black_result.create_mask(0))
	alpha_on_black_result.edit_mask = True
	#Copy + Paste the alphaChannelLayer, then anchor it into the mask
	img.add_layer(alpha_channel_copy, len(img.layers))
	is_non_empty_copy = pdb.gimp_edit_copy(alpha_channel_copy)
	img.remove_layer(alpha_channel_copy)
	#paste (needs the previous line or gimp_edit_cut)
	#The pasting won't act on the mask - Maybe I need to specifically target the mask-object!?
	floating_sel = pdb.gimp_edit_paste(alpha_on_black_result.mask, False)
	#The anchoring won't go into the mask?? or it's fine?: 
	pdb.gimp_floating_sel_anchor(floating_sel)
	
	##Then OPTIONALLY apply the mask
	
	#Close the undo group so undo-recording is back to normal
	img.undo_group_end()
	
	#End/finish/remove the progress bar
	pdb.gimp_progress_end()
	
	
register(
	"python_fu_2_layer_BW_bg_removal",					# name
	"Black/White layers Background removal",			# blurb
	"Does the bg removal explained at https://graphicdesign.stackexchange.com/questions/8057/using-gimp-can-you-erase-a-color",			# help
	"KokoroSenshi",										# author
	"KokoroSenshi - CC BY-SA",							# copyright
	"2016",												# date
	"<Image>/Scripts/KScripts/2 layer BW BG Removal",	# menupath
	"*",												# imagetypes
	[],													# params
	[],													# results
	remove_bg_BW)										# function - Don't forget this!!

main()													# Don't forget this!