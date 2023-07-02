from enum import Enum
from math import sin, atan

# basic params
gridUnit		= 42
tolerance		= 0.25
extFilletRadius	= 7.5/2
heightUnit		= 7
tabDepth		= 13

# stacking params
insideTop		= 2.15
insideMid		= 1.8
insideBottom	= 0.7
insideDepth		= insideTop+insideMid+insideBottom
insideFillet	= extFilletRadius-insideTop

outsideTop		= insideTop-tolerance
outsideMid		= insideMid
outsideBottom	= insideBottom + tolerance*0.4
outsideDepth	= outsideTop+outsideMid+outsideBottom
outsideFillet	= extFilletRadius-outsideTop

magnetOffset	= gridUnit/4	#distance from outside
magnetCCDist	= (gridUnit-magnetOffset*2) #distance from centre to centre
magnetDiameter	= 6.5
magnetDepth		= 2.4

screwOffset		= magnetOffset
screwDiameter	= 3
screwSlit		= 0.2 #printable slit for inside magnet hole
screwSlitLength = (magnetDiameter-0.2)*sin(atan(magnetDiameter/screwDiameter))
screwDepth		= 5

# mechanical properties
wallThickness = 1.2 #this should probably be an EXACT multiple of your nozzle diameter

class TopStyle(Enum):
	NONE		= 0
	STACKING	= 1
	NONE_LOW	= 2
	INT_DIV		= 3
	INT_DIV_MAG	= 4

class BottomStyle(Enum):
	NONE		= 0
	BLANK		= 1
	MAGNET_ONLY	= 2
	SCREW_ONLY	= 3
	MAGNET_SCREW= 4

class TabStyle(Enum):
	NONE		= 0
	FULL		= 1

class PlateStyle(Enum):
	BARE		= 0
	MAGNET_ONLY	= 1
	SCREW_ONLY	= 2
	MAGNET_SCREW= 3

class CrossSection(Enum):
	QUADRANT	= 0
	HALF		= 1
	HALFY		= 1
	HALFX		= 2