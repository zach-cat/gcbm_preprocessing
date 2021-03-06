# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Create_16ha_fishnetXY.py
# Created on: 2016-07-18 13:11:24.00000
#   (generated by ArcGIS/ModelBuilder)
# Description:
# ---------------------------------------------------------------------------

#Processing time on A105338 (locally) for 100mile house TSA: 2 hrs 36 min 40 sec

# Imports
import arcpy
import inspect
import math
import time

import preprocess_tools

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## New

class Fishnet(object):
	def __init__(self, inventory, resolution_degrees, ProgressPrinter):
		self.ProgressPrinter = ProgressPrinter
		self.inventory = inventory
		self.resolution_degrees = resolution_degrees

		self.XYgrid = "XYgrid"
		self.XYgrid_temp = "XYgrid_temp"

	def createFishnet(self):
		arcpy.env.workspace = self.inventory.getWorkspace()
		arcpy.env.overwriteOutput=True
		self.inventory.refreshBoundingBox()

		oCorner = self.inventory.getBottomLeftCorner()
		tCorner = self.inventory.getTopRightCorner()
		self.blc_x, self.blc_y = self.roundCorner(oCorner[0], oCorner[1], -1, self.resolution_degrees)
		self.trc_x, self.trc_y = self.roundCorner(tCorner[0], tCorner[1], 1, self.resolution_degrees)

		self.inventory_template = self.inventory.getLayerName()

		self.origin_coord = "{} {}".format(self.blc_x, self.blc_y)
		self.y_axis_coord = "{} {}".format(self.blc_x, self.blc_y+1)
		self.corner_coord = "{} {}".format(self.trc_x, self.trc_y)
		
		tasks = [
			lambda:arcpy.CreateFishnet_management(self.XYgrid, self.origin_coord, self.y_axis_coord, self.resolution_degrees, self.resolution_degrees,
				"", "", self.corner_coord, "NO_LABELS", self.inventory_template, "POLYGON"),
			lambda:self._createFields(),
			lambda:self._calculateFields()
		]
		pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
		for t in tasks:
			t()
			pp.updateProgressV()
		pp.finish()

	def roundCorner(self, x, y, ud, res):
		if ud==1:
			rx = math.ceil(float(x)/res)*res
			ry = math.ceil(float(y)/res)*res
		elif ud==-1:
			rx = math.floor(float(x)/res)*res
			ry = math.floor(float(y)/res)*res
		else:
			raise Exception("Invalid value for 'ud'. Provide 1 (Round up) or -1 (Round down).")
		return rx, ry

	def test_multiprocessing(self, args, workspace):
		arcpy.env.workspace = workspace
		arcpy.env.overwriteOutput=True
		arcpy.AddField_management(args)

	def _createFields(self):
		field_name_types = {
			"X":"DOUBLE",
			"Y":"DOUBLE",
			"X_ID":"SHORT",
			"Y_ID":"SHORT",
			"TEST_E":"LONG",
			"TEST_E2":"LONG",
			"TEST_N":"LONG",
			"TEST_N2":"LONG",
			"CELL_ID":"TEXT",
			"TileID":"LONG"
		}

		pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(field_name_types), 1)
		pp.start()

		# jobs = []
		for field_name in field_name_types:
			field_type = field_name_types[field_name]
			field_length = "25" if field_type.upper()=="TEXT" else ""
			arcpy.AddField_management(self.XYgrid, field_name, field_type, "", "", field_length, "", "NULLABLE", "NON_REQUIRED", "")
			pp.updateProgressP()
		# 	process = multiprocessing.Process(target=self.test_multiprocessing,args=((self.XYgrid, field_name, field_type, "", "", field_length, "", "NULLABLE", "NON_REQUIRED", ""),self.workspace))
		# 	jobs.append(process)
		# 	process.start()
		#
		# for j in jobs:
		# 	j.join()

		pp.finish()

	def _calculateFields(self):

		x_middle_coord = self.blc_x + (self.resolution_degrees/2) -0.00001 #Center of bottom left tile x coordinate - 1
		y_middle_coord = self.blc_y + (self.resolution_degrees/2) -0.00001 #Center of bottom left tile y coordinate - 1

		functions = [
			lambda:arcpy.CalculateField_management(self.XYgrid, "X", "!SHAPE.CENTROID.X!", "PYTHON_9.3"),
			lambda:arcpy.CalculateField_management(self.XYgrid, "Y", "!SHAPE.CENTROID.Y!", "PYTHON_9.3"),
			lambda:arcpy.CalculateField_management(self.XYgrid, "TEST_E", "(!X! - {})*1000".format(x_middle_coord), "PYTHON_9.3", ""),
			lambda:arcpy.MakeFeatureLayer_management(self.XYgrid, self.XYgrid_temp),
			lambda:arcpy.SelectLayerByAttribute_management(self.XYgrid_temp, "NEW_SELECTION", "TEST_E > 1"),
			lambda:arcpy.CalculateField_management(self.XYgrid_temp, "TEST_E2", "round(!TEST_E! ,0)", "PYTHON_9.3", ""),
			lambda:arcpy.CalculateField_management(self.XYgrid_temp, "TEST_E", "!TEST_E2! + 1", "PYTHON_9.3", ""),
			lambda:arcpy.SelectLayerByAttribute_management(self.XYgrid_temp, "CLEAR_SELECTION", ""),
			lambda:arcpy.CalculateField_management(self.XYgrid_temp, "X_ID", "!TEST_E!", "PYTHON_9.3", ""),
			lambda:arcpy.CalculateField_management(self.XYgrid_temp, "TEST_N", "(!Y! -{})*1000".format(y_middle_coord), "PYTHON_9.3", ""),
			lambda:arcpy.SelectLayerByAttribute_management(self.XYgrid_temp, "NEW_SELECTION", "TEST_N > 1"),
			lambda:arcpy.CalculateField_management(self.XYgrid_temp, "TEST_N2", "round(!TEST_N!,0)", "PYTHON_9.3", ""),
			lambda:arcpy.CalculateField_management(self.XYgrid_temp, "TEST_N", "!TEST_N2! + 1", "PYTHON_9.3", ""),
			lambda:arcpy.SelectLayerByAttribute_management(self.XYgrid_temp, "CLEAR_SELECTION", ""),
			lambda:arcpy.CalculateField_management(self.XYgrid_temp, "Y_ID", "!TEST_N!", "PYTHON_9.3", ""),
			lambda:arcpy.CalculateField_management(self.XYgrid_temp, "CELL_ID", "'{}_{}'.format(!X_ID!,!Y_ID!)", "PYTHON_9.3", "")
		]

		pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(functions), 1).start()
		for f in functions:
			f()
			pp.updateProgressP()

		pp.finish()


class TileID(object):
	def __init__(self, workspace, number_of_tiles, ProgressPrinter):
		arcpy.env.workspace = workspace
		arcpy.env.overwriteOutput=True

		self.ProgressPrinter = ProgressPrinter

		self.numberofTiles = number_of_tiles

		self.XYgrid = "XYgrid"
		self.XYgrid_temp = "XYgrid_temp"

	def runTileID(self):
		tasks = [
			lambda:self._addField(),
			lambda:self._makeFeatureLayer(),
			lambda:self._tileIDs()
		]
		pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
		for t in tasks:
			t()
			pp.updateProgressV()
		pp.finish()

	def _addField(self):
		pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
		arcpy.AddField_management(self.XYgrid, "TileID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
		pp.finish()

	def _makeFeatureLayer(self):
		pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
		arcpy.MakeFeatureLayer_management(self.XYgrid, self.XYgrid_temp)
		pp.finish()

	def _tileIDs(self):
		cur = arcpy.UpdateCursor(self.XYgrid_temp, sort_fields = "Y_ID D")

		all_rows = arcpy.GetCount_management(self.XYgrid_temp)
		nrows = int(all_rows.getOutput(0))
		pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], nrows, 1).start()

		max = cur.next().getValue("Y_ID")
		print "\tMax value for gridding is:", max
		division = int(max / self.numberofTiles) +1
		print "\tTiles will be split every", division, "records."
		for row in cur:
		    # The variable 'age' will get the value from the column
		    yValue = row.getValue("Y_ID")
		    value = int(yValue /division)+1
		    if yValue == max:
		        row.setValue("TileID", self.numberofTiles)
		    else:
		        row.setValue("TileID", value)
		    cur.updateRow(row)
		    pp.updateProgressP()

		pp.finish()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## Old Script

"""
## 01_create_fishnet_1ha

# Working location:
arcpy.env.workspace = r"H:\Nick\GCBM\04_DogRiver\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb"

# Local variables:
origin = (489400, 12420800)
top_right_corner = (596500, 12553900)

origin_coord = "{} {}".format(origin[0], origin[1]) # these are rounded west and south of the left and bottom extents of the inventory
y_axis_coord = "{} {}".format(origin[0], origin[1]+10) # same as origin except +10 for y coord
corner_coord = "{} {}".format(top_right_corner[0], top_right_corner[1]) # these are the rounded east and south values of the right and top extents of the inventory

resolution_meters = 100
inventory_template = "inventory_177"

x_middle_coord = origin[0] + (resolution_meters/2) -1 #Center of bottom left tile x coordinate - 1
y_middle_coord = origin[1] + (resolution_meters/2) -1 #Center of bottom left tile y coordinate - 1

XYgrid_1ha = "XYgrid_1ha"
XYgrid_1ha_temp = "XYgrid_1ha_temp"


print "Start time: " +(time.strftime('%a %H:%M:%S'))
# Process: Create Fishnet---------------
arcpy.CreateFishnet_management(XYgrid_1ha, origin_coord, y_axis_coord, resolution_meters, resolution_meters, "", "", corner_coord, "NO_LABELS", inventory_template, "POLYGON")
print "Fishnet created. " +(time.strftime('%a %H:%M:%S'))
print "Process: Add Field-------------------"
arcpy.AddField_management("XYgrid_1ha", "X", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (2)"
arcpy.AddField_management(XYgrid_1ha, "Y", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (4)"
arcpy.AddField_management(XYgrid_1ha, "Y", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (5)"
arcpy.AddField_management(XYgrid_1ha, "X_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (6)"
arcpy.AddField_management(XYgrid_1ha, "Y_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (7)"
arcpy.AddField_management(XYgrid_1ha, "TEST_E", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (8)"
arcpy.AddField_management(XYgrid_1ha, "TEST_E2", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (9)"
arcpy.AddField_management(XYgrid_1ha, "TEST_N", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (10)"
arcpy.AddField_management(XYgrid_1ha, "TEST_N2", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (11)"
arcpy.AddField_management(XYgrid_1ha, "CELL_ID", "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")

print "Process: Add Field (12)"
arcpy.AddField_management(XYgrid_1ha, "TileID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Finished creating fields. " +(time.strftime('%a %H:%M:%S'))

print "Process: Calculate Field--------------------"

arcpy.CalculateField_management(XYgrid_1ha, "X", "!SHAPE.CENTROID.X!", "PYTHON_9.3")

arcpy.CalculateField_management(XYgrid_1ha, "Y", "!SHAPE.CENTROID.Y!", "PYTHON_9.3")

# put the x and y in the middle of the first cell - also see line 87 - calculate centroid for first cell and SUBTRACT meter value by 1
arcpy.CalculateField_management(XYgrid_1ha, "TEST_E", "!X! - ({})".format(x_middle_coord), "PYTHON_9.3", "")

print "Make Feature Layer"
arcpy.MakeFeatureLayer_management(XYgrid_1ha, XYgrid_1ha_temp)

print "Process: Select Layer By Attribute"
arcpy.SelectLayerByAttribute_management(XYgrid_1ha_temp, "NEW_SELECTION", "TEST_E > 1")

print "Process: Calculate Field (2)"
arcpy.CalculateField_management(XYgrid_1ha_temp, "TEST_E2", "round(!TEST_E! /100,0)", "PYTHON_9.3", "")

print "Process: Calculate Field (3)"
arcpy.CalculateField_management(XYgrid_1ha_temp, "TEST_E", "!TEST_E2! + 1", "PYTHON_9.3", "")

print "Process: Select Layer By Attribute (2)"
arcpy.SelectLayerByAttribute_management(XYgrid_1ha_temp, "CLEAR_SELECTION", "")

print "Process: Calculate Field (4)"
arcpy.CalculateField_management(XYgrid_1ha_temp, "X_ID", "!TEST_E!", "PYTHON_9.3", "")

print "Process: Calculate Field (5)"
arcpy.CalculateField_management(XYgrid_1ha_temp, "TEST_N", "!Y! -{}".format(y_middle_coord), "PYTHON_9.3", "")

print "Process: Select Layer By Attribute (3)"
arcpy.SelectLayerByAttribute_management(XYgrid_1ha_temp, "NEW_SELECTION", "TEST_N > 1")

print "Process: Calculate Field (6)"
arcpy.CalculateField_management(XYgrid_1ha_temp, "TEST_N2", "round(!TEST_N!/100,0)", "PYTHON_9.3", "")

print "Process: Calculate Field (7)"
arcpy.CalculateField_management(XYgrid_1ha_temp, "TEST_N", "!TEST_N2! + 1", "PYTHON_9.3", "")

print "Process: Select Layer By Attribute (4)"
arcpy.SelectLayerByAttribute_management(XYgrid_1ha_temp, "CLEAR_SELECTION", "")

print "Process: Calculate Field (8)"
arcpy.CalculateField_management(XYgrid_1ha_temp, "Y_ID", "!TEST_N!", "PYTHON_9.3", "")

print "Process: Calculate Field (9)"
arcpy.CalculateField_management(XYgrid_1ha_temp, "CELL_ID", "'{}_{}'.format(!X_ID!,!Y_ID!)", "PYTHON_9.3", "")

print "Finished calculating fields. " +(time.strftime('%a %H:%M:%S'))


## 02_tileID

# Working location:
arcpy.env.workspace = r"H:\Nick\GCBM\04_DogRiver\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb"
# Local variables:
resolution_meters = 100
numberofTiles = 16

XYgrid_1ha = "XYgrid_1ha"
XYgrid_temp = "XYgrid_1ha_temp"

print "Start time: " +(time.strftime('%a %H:%M:%S'))

# Process: Add Field (12)
arcpy.AddField_management(XYgrid_1ha, "TileID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

print "Finished creating fields. " +(time.strftime('%a %H:%M:%S'))

# Make Feature Layer
arcpy.MakeFeatureLayer_management(XYgrid_1ha, XYgrid_1ha_temp)

cur = arcpy.UpdateCursor(XYgrid_1ha_temp, sort_fields = "Y_ID D")
max = cur.next().getValue("Y_ID")
print "Max value for gridding is:",
print max
division = round(max / numberofTiles,0) +1
print "Tiles will be split every",
print division,
print "records."
#Need to set tile for first cell separately apparently...
progress = 0
all_rows = arcpy.GetCount_management("XYgrid_1ha_temp")
nrows = int(all_rows.getOutput(0))
for row in cur:
    progress += 1
    # The variable 'age' will get the value from the column
    yValue = row.getValue("Y_ID")
    value = int(yValue /division)+1
    if yValue == max:
        row.setValue("TileID", numberofTiles)
    else:
        row.setValue("TileID", value)
    cur.updateRow(row)
    sys.stdout.write("Progress: [{}%] \r".format(round(float(progress)/float(nrows),3)*100))
    sys.stdout.flush()

print "Finished calculating fields. " +(time.strftime('%a %H:%M:%S'))

"""
