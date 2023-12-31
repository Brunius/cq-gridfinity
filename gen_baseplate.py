import cadquery as cq
from math import sin, cos, tan, asin, acos, atan
from math import floor, ceil

from standards import *

def crossSection(
		item			= None,
		sectionX: float	= 0,
		sectionY: float	= 0,
		type			= CrossSection.QUADRANT,
	):
	"""
	Cuts the supplied object to display a cross-section view.

	:param item: The item to be cut
	:param sectionX: X translation to apply to the cutter
	:param sectionY: Y translation to apply to the cutter
	:param type: Which cutter to use
	:type type: CrossSection.(QUADRANT|HALF|HALFX|HALFY)

	:return: The item, cut as specified
	"""
	if (item is None):
		return None
	maxDist = item.largestDimension()
	sectionCutter = (
		cq.Workplane("XY")
		.box(maxDist*3, maxDist*3, maxDist*3, False)
		.translate((0,0,-maxDist*1.5))
	)
	if (type == CrossSection.HALF
     or type == CrossSection.HALFY):
		sectionCutter = (
			sectionCutter
			.union(
				sectionCutter
				.rotate((0,0,0), (0,0,5), -90)
			)
		)
	elif (type == CrossSection.HALFX):
		sectionCutter = (
			sectionCutter
			.union(
				sectionCutter
				.rotate((0,0,0), (0,0,5), 90)
			)
		)
	item = item.cut(
		sectionCutter
		.translate((sectionX, sectionY, 0))
		)
	return item

def roundedRect(
		xLength		= 10,
		yLength		= 10,
		radius		= 2,
		inObject	= cq.Workplane("XY"),
		):
	"""
	Draws a rounded rectangle on the supplied workplane, or one a default XY workplane if none is supplied

	:param xLength: Length in the X direction
	:param yLength: Length in the Y direction
	:param radius: Radius of the fillet
	:param inObject: The workplane to add the rounded rectangle to

	:return: A rounded rectangle on the workplane
	"""
	xL = (xLength/2 - radius)
	yL = (yLength/2 - radius)
	returnVal = (
		inObject
		.moveTo(xL, yLength/2)
		.radiusArc((xLength/2, yL), radius)
		.lineTo(xLength/2, -yL)
		.radiusArc((xL, -yLength/2), radius)
		.lineTo(-xL, -yLength/2)
		.radiusArc((-xLength/2, -yL), radius)
		.lineTo(-xLength/2, yL)
		.radiusArc((-xL, yLength/2), radius)
		.lineTo(xL, yLength/2)
		.close()
	)

	return returnVal

def baseplate (
		plateX		= 3,
		plateY		= 3,
		plateZ		= None,

		plateStyle	= PlateStyle.MAGNET_ONLY,

		roundTop	= False,
		):
	"""
	Generate a gridfinity baseplate of plateX * plateY

	:param plateX: X dimension of the baseplate, in gridfinity units. Rounds up to the next int.
	:param plateY: Y dimension of the baseplate, in gridfinity units. Rounds up to the next int.
	:param plateZ: Z height of the baseplate, in mm. If this is None (default), then it will automatically calculate the minimum for the specified base style
	:param plateStyle: Style of the baseplate - PlateStyle.(BARE|MAGNET_ONLY|SCREW_ONLY|MAGNET_SCREW)
	:param roundTop: Whether to round the top edges

	:return: A gridfinity baseplate of the specified size
	"""
	if (plateX <= 0):
		raise ValueError("plateX cannot be less than 0")
	if (plateY <= 0):
		raise ValueError("plateY cannot be less than 0")
	if (plateZ is None):
		plateZ = outsideDepth
		if (plateStyle is not PlateStyle.BARE):
			plateZ += magnetDepth+wallThickness
	singleUnit = (
		cq.Workplane("XY")
		.rect(gridUnit, gridUnit)
		.extrude(-plateZ)
	)
	surfaceXY	= gridUnit - tolerance*2
	surfaceRad	= extFilletRadius
	middleXY	= surfaceXY - outsideTop*2
	middleRad	= surfaceRad - outsideTop
	bottomXY	= middleXY - outsideBottom*2-0.1
	bottomRad	= middleRad - outsideBottom

	surfaceProfile	= roundedRect(surfaceXY, surfaceXY, surfaceRad, singleUnit)
	midTopProfile	= roundedRect(middleXY, middleXY, middleRad, surfaceProfile.workplane(-outsideTop))
	midBotProfile	= roundedRect(middleXY, middleXY, middleRad, midTopProfile.workplane(-outsideMid))
	bottomProfile	= roundedRect(bottomXY, bottomXY, bottomRad, midBotProfile.workplane(-outsideBottom))
	singleUnit = (
		bottomProfile
		.loft(True, "s")
	)
	if roundTop:
		singleUnit = (
			singleUnit
			.faces(">Z")
			.rect(plateX*gridUnit*2, plateY*gridUnit*2)
			.extrude(-outsideTop/2, "s")
			.edges(">Z except (>X or <X or >Y or <Y)")
			.fillet(outsideTop/4)
		)
	match plateStyle:
		case PlateStyle.MAGNET_ONLY:
			singleUnit = (
				singleUnit
				.faces(">Z")
				.rect(magnetCCDist, magnetCCDist, forConstruction=True)
				.vertices()
				.circle(magnetDiameter/2)
				.extrude(-magnetDepth-outsideDepth, "s")
			)
		case PlateStyle.SCREW_ONLY:
			singleUnit = (
				singleUnit
				.faces(">Z")
				.rect(magnetCCDist, magnetCCDist, forConstruction=True)
				.vertices()
				.circle(screwDiameter/2)
				.extrude(-screwDepth-outsideDepth, "s")
			)
		case PlateStyle.MAGNET_SCREW:
			singleUnit = (
				singleUnit
				.faces(">Z")
				.rect(magnetCCDist, magnetCCDist, forConstruction=True)
				.vertices()
				.circle(magnetDiameter/2)
				.extrude(-magnetDepth-outsideDepth, "s")
				.faces(">Z")
				.rect(magnetCCDist, magnetCCDist, forConstruction=True)
				.vertices()
				.circle(screwDiameter/2)
				.extrude(-screwDepth-outsideDepth, "s")
			)
	singleUnit = singleUnit.translate((0,0,-tolerance))

	returnPlate = cq.Workplane("XY") #blank

	unionList = []
	for x in range(ceil(plateX)):
		for y in range(ceil(plateY)):
			unionList.append(
				singleUnit.translate((
					(x - (plateX/2 - 0.5))*gridUnit,
					(y - (plateY/2 - 0.5))*gridUnit,
					0
				))
			)
	for item in unionList:
		returnPlate = (
			returnPlate
			.add(item)
		)
	returnPlate = returnPlate.combine()
	
	return returnPlate