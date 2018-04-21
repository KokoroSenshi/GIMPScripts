#!/usr/bin/env python

#https://duckduckgo.com/?q=gimp+script+get+pointer+location&t=ffsb
##http://www.gimpusers.com/forums/gimp-developer/16255-get-pointer-coordinates-in-a-python-script
#https://duckduckgo.com/?q=gimp+script+request+input+after+start&t=ffsb
##http://gimpforums.com/thread-get-current-image-with-script-fu
##^how the script defaults to current image and drawable, and later on a bit about getting pointer location

#VITAL INFORMATION!!!! I finally found something useful on how to make UIs (other than documentation that gives function details but not simply how to make one to actually get started - now I should be able to figure the rest out maybe):
#https://duckduckgo.com/?q=gimp+python+fu+gtk+UI&t=ffsb
##http://stackoverflow.com/questions/34973281/gimp-how-can-i-get-the-coordinates-of-path-tool-points
#Would try http://developer.gimp.org/api/2.0/libgimpwidgets/GimpDialog.html , but again, it doesn't tell me how to use it in a (Python) script
#https://duckduckgo.com/?q=GimpDialog.&t=ffab
##http://developer.gimp.org/api/2.0/gtk/GtkDialog.html
##^has example code, though in C (?)
#gtk.ColorSelectionDialog("s").run()
#https://duckduckgo.com/?q=gtk+in+python+documentation&t=ffab
##http://stackoverflow.com/questions/11586396/pygobject-gtk-3-documentation
###http://python-gtk-3-tutorial.readthedocs.org/en/latest/introduction.html#simple-example
###http://python-gtk-3-tutorial.readthedocs.org/en/latest/entry.html
###http://python-gtk-3-tutorial.readthedocs.org/en/latest/dialogs.html


#http://developer.gimp.org/api/2.0/libgimp/libgimp-gimpvectors.html
#gimp.image_list()[0].vectors[0].strokes[0].points[0]
#a stroke is one path you draw (each point by default? has 6 consecutive data points ? 3 xy pairs?)
#The supposed xy pairs are the coordinates of the top-left corner of the pixel it's on? so round down to get pixel coordinate?
#The 2nd pair refers to point location, the other two refer to the other two handles for curving the lines that join to that point
#....points[1] is False.... why?

#https://duckduckgo.com/?q=gimp+script+change+active+tool&t=ffsb
##http://www.gimpusers.com/forums/gimp-user/11527-change-active-tool-from-script
##^xdotool as a useful workaround for GIMP (python) scripting limitations?

#(http://www.gimp.org/docs/python/index.html)
#(^Plugin Framework section)

#gimp.image_list()[0].vectors[0].strokes[-1].points[0][?]
#^gives the last added vector, stroke and ?th ordinate stored in the array
#The 2nd coordinate pair of the last added point is wanted, which is the 3rd and 4th ordinates from the end, which is:
#gimp.image_list()[0].vectors[0].strokes[-1].points[0][-4] , gimp.image_list()[0].vectors[0].strokes[-1].points[0][-3] 

#import gtk
#import gimpui
#^or use help()?

#http://shallowsky.com/blog/gimp/pygimp-pixel-ops.html

from gimpfu import *
import gtk

def sprite_clicker(img, layer) :
	''' Click a sprite to extract it! 
	Based on assumption of rectangle sprite regions + boundary color borders top-left and bottom-right of sprites + boundary color is foreground color http://www.spriters-resource.com/fullview/68256/
	
	Parameters:
	img   : image  The current image.
	layer : layer  The layer of the image that is selected.
	'''
	
	##Instructions
	Instruct = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, "Make sure the background/boundary color is chosen as foreground. \nUse the paths tool to select the desired sprite and click OK")
	response = Instruct.run()
	#gimp.message("Use the paths tool to select the desired sprite and click OK")
	if response == -5:
		
		# Initializes the progress bar
		gimp.progress_init("Extracting selected sprite from " + layer.name + "...")

		# Makes an undo group, so undo will undo the whole operation (saves undo-recording effort?)
		img.undo_group_start()

		#TEMP: Give layer alpha #Ignore non-alpha channels
		layer.add_alpha()

		#Convert foreground color to string form - to compare with each pixel
		fg_tuple = gimp.get_foreground()
		fg_string = chr(fg_tuple[0]) + chr(fg_tuple[1]) + chr(fg_tuple[2]) + chr(fg_tuple[3]) #e.g. (50,97,168,255) is '2'+'a'+'\xa8'+'\xff'

		#Takes the last placed vector point and floats the sprite to a new layer
		try:
			
			LAYER_WIDTH = layer.width
			LAYER_HEIGHT = layer.height
			
			#Get last vector location (int should round down the point values?)
			pixel_x = int(img.vectors[0].strokes[-1].points[0][-4])
			pixel_y = int(img.vectors[0].strokes[-1].points[0][-3])
			#gimp.message("("+str(pixel_x)+", "+str(pixel_y)+")")
			
			#get relevant pixels .... (x,y,width,height,...,...)
			pixel_row = layer.get_pixel_rgn(0,pixel_y,LAYER_WIDTH,1,False,False)
			pixel_col = layer.get_pixel_rgn(pixel_x,0,1,LAYER_HEIGHT,False,False)
			
			for x in range(pixel_x,LAYER_WIDTH):
				if pixel_row[x,pixel_y] == fg_string:
					right_pos = x-1
					break
			
			for x in range(0,pixel_x):
				if pixel_row[(pixel_x-1)-x,pixel_y] == fg_string:
					left_pos = (pixel_x-1)-x + 1
					break
			
			for y in range(pixel_y,LAYER_HEIGHT):
				if pixel_col[pixel_x,y] == fg_string:
					bottom_pos = y-1
					break
			
			for y in range(0,pixel_y):
				if pixel_col[pixel_x,(pixel_y-1)-y] == fg_string:
					top_pos = (pixel_y-1)-y + 1
					break
			
			sprite_width = right_pos - left_pos + 1
			sprite_height = bottom_pos - top_pos + 1
			
			#Create selection based on this pixel location and sprite_width and sprite_height found
			pdb.gimp_image_select_rectangle(img, 2, left_pos, top_pos, sprite_width, sprite_height)
			#Float it then to new layer
			float = pdb.gimp_selection_float(layer,0,0)
			##pdb.gimp_floating_sel_to_layer(float) #no need if saving?
			
			#Exporting with a script is not convenient to allow the same customizations as doing it normally, so create just new image?
			#... but that's not going easily either...
			#(Self note: making new objects/structures may simply be itself as a function, by that I mean to make an Image, do Image(...)!)
			#sprite_image = gimp.Image(sprite_width,sprite_height) #(3rd param is RGB, Greyscale, Indexed... ?)
			
			#Stray ideas:
			#filename = img.filename
			#TEST: pdb.gimp_file_save(gimp.image_list()[0], gimp.image_list()[0].layers[0], "D:\\Fa.png", "Fs")
			#\ or \\, both fine since Python converts the string to escape the \ automatically?
			#pdb.gimp_file_save(img, float, "D:\\Fa.png", "Fs")
			
		except Exception as error_code: #except = on 'try' failing, if error type is Exception, store the error info(?) in variable err (as a number?)
			gimp.message( "Unexpected error: " + str(error_code) )


		#Close the undo group so undo-recording is back to normal
		img.undo_group_end()

		#End/finish/remove the progress bar
		pdb.gimp_progress_end()
		
	else:
		gimp.message( "Operation Cancelled.")
	
register(
	"python_fu_sprite_clicker",									# name
	"Sprite clicker",											# blurb
	"Extracts individual sprites from certain spritesheets",	# help
	"KokoroSenshi",												# author
	"KokoroSenshi - CC BY-SA",									# copyright
	"2016",														# date
	"<Image>/Scripts/KScripts/Sprite clicker",					# menupath
	"*",														# imagetypes
	[],															# params
	[],															# results
	sprite_clicker)												# function - Don't forget this!!

main()															# Don't forget this!