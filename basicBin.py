import cadquery as cq
from math import tan

from standards import *

def roundedRect(
		xLength		= 10,
		yLength		= 10,
		radius		= 2,
		inObject	= cq.Workplane("XY"),
		):
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
				.rect(gridUnit-magnetOffset*2, gridUnit-magnetOffset*2, forConstruction=True)
				.vertices()
				.circle(magnetDiameter/2)
				.extrude(-magnetDepth-outsideDepth, "s")
			)
		case PlateStyle.SCREW_ONLY:
			singleUnit = (
				singleUnit
				.faces(">Z")
				.rect(gridUnit-magnetOffset*2, gridUnit-magnetOffset*2, forConstruction=True)
				.vertices()
				.circle(screwDiameter/2)
				.extrude(-screwDepth-outsideDepth, "s")
			)
		case PlateStyle.MAGNET_SCREW:
			singleUnit = (
				singleUnit
				.faces(">Z")
				.rect(gridUnit-magnetOffset*2, gridUnit-magnetOffset*2, forConstruction=True)
				.vertices()
				.circle(magnetDiameter/2)
				.extrude(-magnetDepth-outsideDepth, "s")
				.faces(">Z")
				.rect(gridUnit-magnetOffset*2, gridUnit-magnetOffset*2, forConstruction=True)
				.vertices()
				.circle(screwDiameter/2)
				.extrude(-screwDepth-outsideDepth, "s")
			)
	singleUnit = singleUnit.translate((0,0,-tolerance))

	returnPlate = cq.Workplane("XY") #blank

	unionList = []
	for x in range(plateX):
		for y in range(plateY):
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

def binSolid(
		binX: float	= 1,
		binY: float	= 1,
		binZ: float	= 6,

		topStyle	= TopStyle.STACKING,
		bottomStyle	= BottomStyle.MAGNET_ONLY
		):
		
	binWidth	= binX*gridUnit-tolerance*2
	binDepth	= binY*gridUnit-tolerance*2
	binHeight	= binZ*heightUnit

	bin = (cq.Workplane("XY", (0,0,binHeight/2))
				.box(binWidth, binDepth, binHeight)
				.edges("|Z")
				.fillet(extFilletRadius)
	)
			
	
	# bottom of bin
	interlockWidth = gridUnit-tolerance*2-insideTop*2
	magnetLocation = gridUnit-magnetOffset*2
	
	interlockBlank = (
		bin
		.faces("<Z")
		.rect(interlockWidth, interlockWidth)
		.extrude(-insideDepth, False)
		.edges("|Z")
		.fillet(insideFillet)
		.faces("<Z")
		.chamfer(insideBottom)
		.faces(">Z")
		.rect(gridUnit-tolerance*2, gridUnit-tolerance*2)
		.extrude(-insideTop)
		.edges("|Z")
		.fillet(extFilletRadius)
		.faces(">Z[1]")
		.edges(">>X or <<X or >>X[0] or >>X[-1] or >>Y or <<Y")
		.chamfer(insideTop-0.01)
	)
	
	unionObject = None
	match bottomStyle:
		case BottomStyle.BLANK:
			unionObject = interlockBlank
		case BottomStyle.MAGNET_ONLY:
			unionObject = (
				interlockBlank
				.faces("<Z")
				.rect(magnetLocation, magnetLocation, forConstruction=True)
				.vertices()
				.circle(magnetDiameter/2)
				.extrude(magnetDepth, "s")
			)
		case BottomStyle.SCREW_ONLY:
			unionObject = (
				interlockBlank
				.faces("<Z")
				.rect(magnetLocation, magnetLocation, forConstruction=True)
				.vertices()
				.circle(screwDiameter/2)
				.extrude(screwDepth, "s")
			)
		case BottomStyle.MAGNET_SCREW:
			unionObject = (
				interlockBlank
				.faces("<Z")
				.rect(magnetLocation, magnetLocation, forConstruction=True)
				.vertices()
				.circle(magnetDiameter/2)
				.extrude(magnetDepth, "s")
				.faces("<Z")
				.rect(magnetLocation, magnetLocation, forConstruction=True)
				.vertices()
				.circle(screwDiameter/2)
				.extrude(screwDepth, "s")
				.faces("<Z")
				.rect(magnetLocation, magnetLocation, forConstruction=True)
				.vertices()
				.rect(screwDiameter, screwSlitLength)
				.extrude(magnetDepth+screwSlit, "s")
			)

	if (unionObject is not None):
		xOffset = (binX-1 % 2) * -gridUnit/2
		yOffset = (binY-1 % 2) * -gridUnit/2
		
		unionList = []

		for x in range(binX):
			for y in range(binY):
				unionList.append(
					unionObject
					.translate((
						xOffset+x*gridUnit,
						yOffset+y*gridUnit,
						0
					))
				)
		for item in unionList:
			bin = (
				bin
				.add(item)
			)
		bin = bin.combine()
	
	# top of bin
	match topStyle:
		case TopStyle.NONE_LOW:
			bin = (
				bin
				.faces(">Z")
				.rect(binWidth, binDepth)
				.extrude(-outsideDepth, "s")
			)
		case TopStyle.STACKING:
			cutoutObject = (
				bin
				.faces(">Z")
				.rect(binWidth-outsideTop*2, binDepth-outsideTop*2)
				.extrude(-outsideDepth-tolerance, False)
				.edges("|Z")
				.fillet(outsideFillet)
				.faces("-Z")
				.chamfer(outsideBottom)
				.faces(">Z")
				.rect(binWidth, binDepth)
				.extrude(-outsideTop/2)
			)
			bin = (
				bin
				.cut(cutoutObject)
				.edges(">Z")
				#eliminate straight edges on outside
				.edges("not(>X or <X or >Y or <Y)")
				#eliminate outside curves
				.edges("not >>X[0] or >>X[-1]")
				.chamfer(outsideTop/2+tolerance)
				#fillet outside + transition to chamfer
				.edges(">Z")
				.fillet(outsideTop/4)
			)
		case TopStyle.INT_DIV:
			baseForTop = (
				baseplate(binX, binY, None, PlateStyle.BARE, True)
				.translate((0, 0, binZ*heightUnit))
				.intersect(bin)
			)
			bin = (
				bin
				.faces(">Z")
				.rect(binWidth, binDepth)
				.extrude(-outsideDepth-tolerance, "s")
			).union(baseForTop)
		case TopStyle.INT_DIV_MAG:
			baseForTop = (
				baseplate(binX, binY, None, PlateStyle.MAGNET_ONLY, True)
				.translate((0, 0, binZ*heightUnit))
				.intersect(bin)
			)
			bin = (
				bin
				.faces(">Z")
				.rect(binWidth, binDepth)
				.extrude(-outsideDepth-tolerance-magnetDepth, "s")
			).union(baseForTop)

	return bin

def tabGenerator(
		tabStyle	= TabStyle.FULL,
		tabAngle	= 45,
		binWidth	= gridUnit-tolerance*2-wallThickness*2
	):
	match tabStyle:
		case TabStyle.NONE:
			return None
		case TabStyle.FULL:
			returnTab = (
				cq.Workplane("YZ")
				.moveTo(0,0)
				.lineTo(-tabDepth-outsideBottom, 0)
				.lineTo(-tabDepth-outsideBottom, -wallThickness)
				.lineTo(0, -wallThickness-tan((90-tabAngle)*3.14/180)*(tabDepth-outsideBottom))
				.close()
				.extrude(binWidth/2, both=True)
				.edges("<Y")
				.fillet(wallThickness/2)
			)
			return returnTab

def binCutter(
		binWidth	= None,
		binDepth	= None,
		binHeight	= None,

		scoop: float= 0,

		tabStyle	= TabStyle.FULL,
		tabAngle	= 45,
	):

	if (binWidth is None or binDepth is None or binHeight is None):
		return None

	binTopFillet	= outsideFillet-outsideBottom
	binBodyFillet	= binTopFillet+outsideBottom
	binTransition	= outsideBottom
	binChamfer		= outsideBottom+outsideTop-wallThickness

	returnCutter = (
		cq.Workplane("XY", (0, 0, -outsideBottom/2))
		.rect(binWidth, binDepth)
		.extrude(-binHeight)
		.edges("|Z or <Z")
		.fillet(binBodyFillet)
		.edges(">Z")
		.chamfer(binChamfer)
	)
	returnCutterTop = (
		returnCutter
		.faces(">Z")
		.rect(binWidth-binChamfer*2, binDepth-binChamfer*2)
		.extrude(binTransition, False)
		.edges("|Z")
		.edges(">Z")
		.fillet(binTopFillet)
	)
	returnCutter = (
		returnCutter
		.add(returnCutterTop)
		.combine()
	)

	tab = tabGenerator(
			tabStyle=tabStyle,
			tabAngle=tabAngle,
			binWidth=binWidth
		)
	if tab is not None:
		tab = (
			tab
			.translate((
				0,
				binDepth/2,
				outsideBottom/2
			))
		)
		returnCutter = (
			returnCutter
			.cut(tab)
		)
	
	if scoop > 0:
		scoopUnit = min(binHeight, binDepth)/4*scoop
		scoopCutter = (
			cq.Workplane("YZ", ( 0, -binDepth/2, -binHeight-outsideBottom/2))
			.moveTo(scoopUnit,0)
			.radiusArc((0,scoopUnit), scoopUnit)
			.lineTo(0, 0)
			.close()
			.extrude(binWidth/2, both=True)
		)
		returnCutter = (
			returnCutter
			.cut(scoopCutter)
		)
	
	return returnCutter

def binCompartments(
		binX: float	= 1,
		binY: float	= 1,
		binZ: float	= 6,

		divX: float	= 1,
		divY: float	= 1,

		scoop: float= 0,

		tabStyle	= TabStyle.FULL,
		tabAngle	= 45,

		topStyle	= TopStyle.STACKING,
		bottomStyle	= BottomStyle.MAGNET_ONLY
		):
	returnBin = binSolid(binX, binY, binZ, topStyle, bottomStyle)

	widthAvail	= (
		binX*gridUnit-tolerance*2	#base bin width
		-wallThickness*2			#outside walls
		-wallThickness*(divX-1)		#inside walls
	)
	depthAvail	= (
		binY*gridUnit-tolerance*2	#base bin depth
		-wallThickness*2			#outside walls
		-wallThickness*(divY-1)		#inside walls)
	)
	heightAvail	= (
		binZ*heightUnit				#base bin height
		-insideDepth
	)

	eachBinWidth	= widthAvail/divX
	eachBinDepth	= depthAvail/divY

	cutterTemplate = (
		binCutter(
			binWidth	= eachBinWidth,
			binDepth	= eachBinDepth,
			binHeight	= heightAvail,
			tabStyle	= tabStyle,
			tabAngle	= tabAngle,
			scoop		= scoop,
		)
		.translate((
			(-widthAvail+eachBinWidth-wallThickness*(divX-1))/2,
			(-depthAvail+eachBinDepth-wallThickness*(divY-1))/2,
			heightAvail
		))
	)

	cutList = []
	for x in range(divX):
		for y in range(divY):
			cutList.append(
				cutterTemplate
				.translate((
					x*(eachBinWidth+wallThickness),
					y*(eachBinDepth+wallThickness),
					0
				))
			)
	for item in cutList:
		returnBin = (
			returnBin
			.cut(item)
		)

	return returnBin

def trayClearWindow(
		trayX: float= 1,
		trayY: float= 1,
		trayZ: float= 1,

		insertX		= gridUnit-magnetOffset,
		insertY		= gridUnit-magnetOffset,
		insertZ		= 1,

		topStyle	= TopStyle.INT_DIV_MAG,
		bottomStyle	= BottomStyle.MAGNET_ONLY,
		):
	returnTray		= binSolid(trayX, trayY, trayZ, topStyle, bottomStyle)
	clearSectionX	= min(insertX*0.8, gridUnit-magnetOffset*2)
	clearSectionY	= min(insertY*0.8, gridUnit-magnetOffset*2)
	magClearance	= magnetDiameter/2 + wallThickness
	alignmentMagicNumber = -0.45 #as the name implies, this is a magic number. where does it come from?> I haven't a goddamn clue.
	windowHeight = alignmentMagicNumber-heightUnit-insideBottom+magnetDepth
	clearCutter = (
		returnTray
		.transformed(offset=(0,0,windowHeight))
		.rect(insertX+tolerance*4, insertY+tolerance*4)
		.extrude(insertZ+tolerance*2, False)
	)
	windowCutter = (
		clearCutter
		.transformed(offset=(0,0,0))
		.moveTo(-clearSectionX/2, 0)
		.lineTo(-clearSectionX/2, -clearSectionY/2+magClearance)
		.radiusArc((-clearSectionX/2+magClearance, -clearSectionY/2), magClearance)
		.lineTo(0, -clearSectionY/2)
		.mirrorX()
		.mirrorY()
		.extrude(trayZ*heightUnit*2, "a", both=True)
	)
	
	cutList = []
	for x in range(trayX):
		for y in range(trayY):
			cutList.append(
				windowCutter
				.translate((
					(x - (trayX/2 - 0.5))*gridUnit,
					(y - (trayY/2 - 0.5))*gridUnit,
					0
				))
			)
	
	for item in cutList:
		returnTray = returnTray.cut(item)
	return returnTray

centreBin = binCompartments(
		binX		= 1,
		binY		= 1,
		binZ		= 6,

		divX		= 1,
		divY		= 1,
		scoop		= 2,

		tabStyle	= TabStyle.FULL,
		tabAngle	= 45,

		topStyle	= TopStyle.STACKING,	
		bottomStyle	= BottomStyle.MAGNET_ONLY,
	)
#del centreBin
crossSection = False
if 'centreBin' in locals() and crossSection:
	#cut for cross section
	centreBin = (
		centreBin
		.transformed((0,0,0), (0,0,-50))
		.moveTo(-magnetCCDist/2, 0)
		.lineTo(-magnetCCDist/2, 50) #half view front
		.lineTo(50,50) #half view front
		.lineTo(50, 0)
		.lineTo(50,-50)
		.lineTo(-magnetCCDist/2, -50)
		#.lineTo(-50,-50) #half view side
		#.lineTo(-50,  0) #half view side
		.close()
		.extrude(500, "s")
	)
"""
s2 = binCompartments(
		binX		= 1,
		binY		= 1,
		binZ		= 3,

		divX		= 3,
		divY		= 1,

		tabStyle	= TabStyle.FULL,
		topStyle	= TopStyle.STACKING,	
		bottomStyle	= BottomStyle.MAGNET_ONLY
	)

s2 = (
	s2
	.faces("<Z")
	.transformed((0,0,0), (0,0,-50))
	.moveTo(0, 0)
	.lineTo(0, 50)
	.lineTo(50,50)
	.lineTo(50,-50)
	.lineTo(-50,-50)
	.lineTo(-50, 0)
	.close()
	.extrude(500, "s")
).translate((gridUnit/2, 0, 0))

s3 = binCompartments(
		binX		= 1,
		binY		= 1,
		binZ		= 3,

		divX		= 4,
		divY		= 1,

		tabStyle	= TabStyle.FULL,
		topStyle	= TopStyle.STACKING,	
		bottomStyle	= BottomStyle.MAGNET_ONLY
	)
s3 = (
	s3
	.faces("<Z")
	.transformed((0,0,0), (0,0,-50))
	.moveTo(0, 0)
	.lineTo(0, 50)
	.lineTo(50,50)
	.lineTo(50,-50)
	.lineTo(-50,-50)
	.lineTo(-50, 0)
	.close()
	.extrude(500, "s")
).translate((gridUnit, 0, 0))#"""

testSolid		= False
testBin			= False
testClearWindow	= True
testFlag		= testSolid or testBin or testClearWindow
if (testFlag):
	testTray = binSolid(
		binX	= 3, 
		binY	= 3,
		binZ	= 1,
		topStyle=TopStyle.INT_DIV_MAG
		).translate((0,0,-heightUnit))
	if (testSolid):
		test_1x2x3		= binSolid(1,2,3, TopStyle.STACKING, BottomStyle.MAGNET_SCREW).translate((gridUnit, gridUnit*0.5, 0))
		test_1x1x6		= binSolid(1,1,6, TopStyle.STACKING, BottomStyle.NONE).translate((0, gridUnit, 0))
		test_1x1x1H		= binSolid(1,1,1, TopStyle.NONE, BottomStyle.SCREW_ONLY).translate((-gridUnit, gridUnit, 0))
		test_1x1x1L		= binSolid(1,1,1, TopStyle.NONE_LOW, BottomStyle.MAGNET_ONLY).translate((-gridUnit, 0, 0))
	if (testBin):
		test_1x1x3_2D	= binCompartments(1, 1, 3, 2).translate((gridUnit, 0, 0))
		test_1x1x6_2D	= binCompartments(1, 1, 6, 1, 2, tabStyle=TabStyle.NONE).translate((gridUnit*-1, 0, 0))
		test_3x1x6_3D	= binCompartments(3, 1, 6, 3).translate((0, gridUnit, 0))
		test_2x1x3_42D	= binCompartments(2, 1, 3, 4, 2, tabStyle=TabStyle.NONE).translate((-gridUnit/2, -gridUnit, 0))
	if (testClearWindow):
		test_1x1x1_Clr	= trayClearWindow(1,1).translate((gridUnit, 0, 0))
		test_2x1x1_Clr	= trayClearWindow(2,1).translate((gridUnit/2, gridUnit, 0))
sectionCutter = (
	cq.Workplane("XY")
	.moveTo(-13, 0)
	.lineTo(-13, 50) #half view front
	.lineTo(50,50) #half view front
	.lineTo(50, 0)
	#.lineTo(50,-50)
	#.lineTo(0, -50)
	#.lineTo(-50,-50) #half view side
	#.lineTo(-50,  0) #half view side
	.close()
	.extrude(500, both=True)
)
clearWindowTray = trayClearWindow()
clearWindowTray = (
	clearWindowTray
	.cut(sectionCutter)
)
del clearWindowTray
del sectionCutter