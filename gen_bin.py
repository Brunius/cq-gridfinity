import cadquery as cq
from math import sin, cos, tan, asin, acos, atan
from math import floor, ceil

from standards import *
from gen_baseplate import *

def binSolid(
		binX: float	= 1,
		binY: float	= 1,
		binZ: float	= 6,

		topStyle	= TopStyle.STACKING,
		bottomStyle	= BottomStyle.MAGNET_ONLY,
		bottomDivX	= 1,
		bottomDivY	= 1,
		):
	if (binX <= 0):
		raise Exception("binX cannot be less than 0")
	if (binY <= 0):
		raise Exception("binY cannot be less than 0")
	if (binZ <= 0):
		raise Exception("binZ cannot be less than 0")
	if (bottomDivX <=0):
		raise Exception("bottomDivX cannot be less than 0")
	if (bottomDivY <=0):
		raise Exception("bottomDivY cannot be less than 0")

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
	magnetLocation = magnetCCDist
	
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
		#check if the requested subdivisions will actually work or not
		printableThreshold = wallThickness*4
		if (bottomDivX is not None):
			bottomDivX_interlockWidth = gridUnit/bottomDivX-insideTop*2 #calculate width of interlock vertical section
			if (bottomDivX_interlockWidth < printableThreshold):
				raise Exception("bottomDivX of {:.2f} is too big - would result in hard to print features of {:.2f}mm".format(bottomDivX, bottomDivX_interlockWidth))
		if (bottomDivY is not None):
			bottomDivY_interlockWidth = gridUnit/bottomDivY-insideTop*2 #calculate depth of interlock vertical section
			if (bottomDivY_interlockWidth < printableThreshold):
				raise Exception("bottomDivY of {:.2f} is too big - would result in hard to print features of {:.2f}mm".format(bottomDivY, bottomDivY_interlockWidth))
		
		#if unspecified, automatically calculate subdivisions
		maxDivisions = floor(gridUnit/(printableThreshold+insideTop*2))
		if (bottomDivX is None):
			if (binX%1):
				autoInverse = 1/(binX%1)
				bottomDivX = autoInverse
				#cycle through whole number options, up to the allowable max
				for i in range(1, maxDivisions+1):
					#if (round(binX%(1/i), 2) == 0.0):
					#	bottomDivX = i
					#	print("method 1")
					#	break
					if (round(i/autoInverse, 1)%1 == 0):
						#if i and autoInverse share a common factor (or nearly share), then accept that
						#this is necessary to allow "nearly" correct numbers such as 0.66 intead of (2/3)
						bottomDivX = autoInverse*round(i/autoInverse, 1)
						break
			else:
				bottomDivX = 1
		if (bottomDivY is None):
			if (binY%1):
				bottomDivY = 1/(binY%1)
				#cycle through whole number options, up to the allowable max
				for i in range(1, maxDivisions+1):
					if (round(binY%(1/i), 2) == 0.0):
						bottomDivY = i
						break
			else:
				bottomDivY = 1
		if (bottomDivX != 1 or bottomDivY != 1):
			#break into parts by intersecting
			#create single unit
			offsetObject = (
				unionObject
				.intersect(
					unionObject
					.translate((
						gridUnit*(1-1/bottomDivX),
						gridUnit*(1-1/bottomDivY),
						0
					))
				)
			)
			#may have weird edges - round them off
			offsetObject = (
				offsetObject
				.intersect(
					offsetObject
					.mirror("YZ")
					.translate((
						gridUnit*(1-1/bottomDivX),
						0,
						0
					))
				)
			)
			unionObject = (
				offsetObject
				.rotate((0,0,0),(0,0,5),180)
			)

		#tile across bottom of bin
		xOffset = (binX-1 % 2) * -gridUnit/2
		yOffset = (binY-1 % 2) * -gridUnit/2
		
		unionList = []

		for x in range(int(binX*bottomDivX)): #binX
			for y in range(int(binY*bottomDivY)): #binY
				unionList.append(
					unionObject
					.translate((
						xOffset+x*gridUnit/bottomDivX,
						yOffset+y*gridUnit/bottomDivY,
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
		tabAngle	= 60,
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
		tabAngle	= 60,
	):

	if (binWidth is None or binDepth is None or binHeight is None):
		return None

	binTopFillet	= outsideFillet-outsideBottom
	binBodyFillet	= outsideFillet
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
		tabAngle	= 60,

		topStyle	= TopStyle.STACKING,
		bottomStyle	= BottomStyle.MAGNET_ONLY,
		bottomDivX	= 1,
		bottomDivY	= 1,
		):
	if (divX < 1):
		raise Exception("divX cannot be less than 1")
	if (divY < 1):
		raise Exception("divY cannot be less than 1")
	returnBin = binSolid(binX, binY, binZ, topStyle, bottomStyle, bottomDivX, bottomDivY)

	widthAvail	= (
		binX*gridUnit-tolerance*2	#base bin width
		-wallThickness*2			#outside walls
		-wallThickness*(divX-1)		#inside walls
	)
	depthAvail	= (
		binY*gridUnit-tolerance*2	#base bin depth
		-wallThickness*2			#outside walls
		-wallThickness*(divY-1)		#inside walls
	)
	heightAvail	= (
		binZ*heightUnit				#base bin height
		- insideDepth
		- wallThickness
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
			heightAvail+wallThickness
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

def binClearWindow(
		binX: float	= 1,
		binY: float	= 1,
		binZ: float	= 6,

		divX: float	= 1,
		divY: float	= 1,

		scoop: float= 0,

		tabStyle	= TabStyle.FULL,
		tabAngle	= 60,

		topStyle	= TopStyle.STACKING,
		bottomStyle	= BottomStyle.MAGNET_ONLY,
		bottomDivX	= 1,
		bottomDivY	= 1,

		clearSide	= "X",
		clearDepth	= 1,
		clearWidth	= 0,
		clearHeight	= 0,
		):
	addX = 0
	addY = 0
	whichBin = 0
	rotateAngle = 0
	if (clearSide.find("X")+1):
		addY		= clearDepth
		whichBin	= binY
		rotateAngle	= 0
	if (clearSide.find("Y")+1):
		addX		= clearDepth
		whichBin	= binX
		rotateAngle	= 90

	#------------------------------------------
	#  Almost all the same as binCompartments
	#------------------------------------------
	returnBin = binSolid(binX, binY, binZ, topStyle, bottomStyle, bottomDivX, bottomDivY)

	widthAvail	= (
		binX*gridUnit-tolerance*2	#base bin width
		-wallThickness*2			#outside walls
		-wallThickness*(divX-1)		#inside walls
		-addX
	)
	depthAvail	= (
		binY*gridUnit-tolerance*2	#base bin depth
		-wallThickness*2			#outside walls
		-wallThickness*(divY-1)		#inside walls
		-addY
	)
	heightAvail	= (
		binZ*heightUnit				#base bin height
		- insideDepth
		- wallThickness
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
			heightAvail+wallThickness
		))
	)

	cutList = []
	for x in range(divX):
		for y in range(divY):
			cutList.append(
				cutterTemplate
				.translate((
					x*(eachBinWidth+wallThickness)-addX/2,
					y*(eachBinDepth+wallThickness)+addY/2,
					0
				))
			)
	for item in cutList:
		returnBin = (
			returnBin
			.cut(item)
		)
	#------------------------------------------
	if (clearDepth < 0):
		raise Exception("binClearWindow only accepts clearDepth >= 0")
	if clearWidth == 0:
		if (clearSide.find("X")+1):
			clearWidth = binX*gridUnit-tolerance*2-wallThickness*2-extFilletRadius*2
		if (clearSide.find("Y")+1):
			clearWidth = binY*gridUnit-tolerance*2-wallThickness*2-extFilletRadius*2
	if clearHeight == 0:
		clearHeight = binZ*heightUnit-insideDepth-wallThickness+tolerance*2
	print(  "Bin:       {:2d}x{:2d}x{:2d}\n".format(binX, binY, binZ) +
			"   Window: {:2.0f}x{:2.0f}x{:2.0f}".format(clearWidth, clearHeight, clearDepth)
			)
	windowCutter = (
		cq.Workplane("XY")
		.box(clearWidth, clearDepth, clearHeight)
		.faces("<Y")
		.workplane()
	)
	windowCutter = roundedRect(clearWidth-wallThickness*2, clearHeight-wallThickness*2, extFilletRadius-wallThickness, windowCutter)
	windowCutter = roundedRect(clearWidth, clearHeight, extFilletRadius, windowCutter.workplane(wallThickness))
	windowCutter = (
		windowCutter
		.loft(True)
		.translate((
			0,
			-whichBin/2*gridUnit+clearDepth-tolerance+wallThickness,
			clearHeight/2+outsideBottom-tolerance*2
			))
		.rotate((0,0,0), (0,0,10), rotateAngle)
	)
	returnBin = (
		returnBin
		.cut(windowCutter)
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
		bottomDivX	= 1,
		bottomDivY	= 1,
		):
	returnTray		= binSolid(trayX, trayY, trayZ, topStyle, bottomStyle, bottomDivX, bottomDivY)
	clearSectionX	= min(insertX*0.8, magnetCCDist)
	clearSectionY	= min(insertY*0.8, magnetCCDist)
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

def trayAngleAdaptor(
		topX: float	= 1,
		trayY: float= 1,

		angleDeg	= None,
		binHeight	= 3,

		topStyle	= TopStyle.INT_DIV_MAG,
		bottomStyle	= BottomStyle.MAGNET_ONLY,
		bottomDivX	= 1,
		bottomDivY	= 1,
		):
	angleRad = 0
	if (angleDeg is None):
		angleRad = atan(binHeight*heightUnit/gridUnit)
		angleDeg = angleRad*180/3.14
	else:
		angleRad = angleDeg*3.14/180
	#check angleDeg isn't going to be impossible to calculate
	if (angleDeg > 80):
		raise Exception("Angle too high - could not calculate")
	if (angleDeg < 0.75):
		raise Exception("Angle too low - could not calculate")
	trayXGrid	= gridUnit/cos(angleRad)
	topFaceX	= cos(angleRad)*gridUnit
	sideFaceX	= trayXGrid - topFaceX

	roundEdgeFlag = True
	bottomX = floor((trayXGrid*topX)/(gridUnit))
	#if cut would be mid-face, add one to the tray size
	if (((gridUnit*bottomX)%trayXGrid) < topFaceX):
		bottomX = bottomX + 1/bottomDivX
		roundEdgeFlag = False
	bottomTray	= binSolid(bottomX, trayY, 1, TopStyle.NONE_LOW, bottomStyle, bottomDivX, bottomDivY)

	topPlate	= binSolid(1, trayY, 1, topStyle, BottomStyle.NONE)
	topPlateRotationEdge = heightUnit-(insideTop+tolerance)/2
	topPlateX	= gridUnit*(bottomX/2-0.5)
	topPlateZ	= -outsideDepth+outsideTop/2+tolerance
	#cutter for deleting sections below 0Z
	negZBox		= (
		cq.Workplane("XY")
		.box(gridUnit*30, gridUnit*30, gridUnit*3)
		.translate((0,0,-gridUnit*1.5))
	)
	#extrude below topplate to meet XY plane
	topPlate	= (
		roundedRect(
			gridUnit-tolerance*2,
			trayY*gridUnit-tolerance*2,
			extFilletRadius,
			topPlate
			.faces("<Z")
			.workplane()
		)
		.extrude(sin(angleRad)*trayXGrid)
	)
	#cutter for trimming to size of tray
	traySizeCutter = (
		cq.Workplane("XY", (0,0,0))
		.rect(bottomX*gridUnit-tolerance*2, trayY*gridUnit-tolerance*2)
		.extrude(50)
		.edges("|Z")
		.fillet(extFilletRadius)
	)
	#create topPlateCutter to clean up geometry on bottom faces
	topPlateCutter = (
		binSolid(1, trayY, 1, TopStyle.NONE, BottomStyle.NONE)
		.cut(
			topPlate
		)
		.faces("<Z[1]")
		.workplane(0, True)
		.rect(gridUnit, gridUnit*trayY)
		.extrude(bottomTray.largestDimension())
	)
	topPlateCutter = (
		topPlateCutter
		.edges(">X or <X or >Y or <Y")
		.edges("<Z")
		.chamfer(tolerance*1)
	)
	#rotate and translate topPlate and topPlateCutter
	topPlate			= (
		topPlate
		.rotate((gridUnit/2-tolerance, -5, topPlateRotationEdge), (gridUnit/2-tolerance, 5, topPlateRotationEdge), angleDeg)
	)
	topPlate			= (
		roundedRect(gridUnit-tolerance*2, trayY*gridUnit-tolerance*2, extFilletRadius, topPlate)
		.extrude(-extFilletRadius*3)
		.translate((topPlateX,0,topPlateZ))
		.cut(negZBox)
		.intersect(traySizeCutter)
	)
	topPlateCutter		= (
		topPlateCutter
		.rotate((gridUnit/2-tolerance, -5, topPlateRotationEdge), (gridUnit/2-tolerance, 5, topPlateRotationEdge), angleDeg)
		.translate((topPlateX,0,topPlateZ))
	)
	#tile in X
	topConsol = cq.Workplane("XY")
	for x in range(topX):
		topPlateCutter = (
			topPlateCutter
			.add(
				topPlateCutter
				.translate((
					-x*trayXGrid,
					0,
					0
				))
			)
		)
		topConsol = (
			topConsol
			.add(
				topPlate
				.translate((
					-x*trayXGrid,
					0,
					0
				))
			)
		)
	topPlateCutter	= topPlateCutter.combine()
	topPlate		= (
		topConsol
		.combine()
		.intersect(traySizeCutter)
	)
	roundEdgeFlag = True
	if roundEdgeFlag:
		try:
			topPlate = (
				topPlate
				.edges("<X")
				.edges(">Z")
				.fillet(extFilletRadius)
			)
		except:
			topPlate = (
				topPlate
			)
	#smoosh it all together
	bottomTray = (
		bottomTray
		.union(topPlate)
		.cut(topPlateCutter)
	)
	return bottomTray