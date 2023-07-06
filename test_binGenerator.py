from gen_bin import *

def testBinSolid():
	test_1x2x3		= binSolid(1,2,3,	TopStyle.INT_DIV_MAG, 	BottomStyle.MAGNET_SCREW).translate((gridUnit, gridUnit*0.5, 0))
	test_1x1x6		= binSolid(1,1,6,	TopStyle.INT_DIV, 		BottomStyle.NONE).translate((0, gridUnit, 0))
	test_1x1x1H		= binSolid(1,1,1,	TopStyle.NONE, 			BottomStyle.SCREW_ONLY).translate((-gridUnit, gridUnit, 0))
	test_1x1x1L		= binSolid(1,1,1,	TopStyle.NONE_LOW, 		BottomStyle.MAGNET_ONLY, 2, 2).translate((-gridUnit, 0, 0))
	test_1x1x1B		= binSolid(1,1,1,	TopStyle.STACKING, 		BottomStyle.BLANK).translate((-gridUnit, -gridUnit, 0))
def testSubDivisions():
	test_15x1x1		= binSolid(1.5,1,1,	TopStyle.INT_DIV_MAG,	BottomStyle.MAGNET_SCREW).translate((-gridUnit*1.5/2, -gridUnit, 0))
	test_166x1x1	= binSolid(1.66,1,1,TopStyle.INT_DIV,		BottomStyle.NONE).translate((-gridUnit*1.33/2, gridUnit, 0))
	test_1x1x1_2X	= binSolid(1,1,1, 	TopStyle.NONE,			BottomStyle.SCREW_ONLY, 2).translate((-gridUnit, 0, 0))
	test_05x1x1_3X	= binSolid(0.5,1,1,	TopStyle.NONE_LOW,		BottomStyle.MAGNET_ONLY, 3).translate((gridUnit*0.5/2, -gridUnit, 0))
	test_034x1x1	= binSolid(0.34,1,1,TopStyle.STACKING,		BottomStyle.BLANK).translate((gridUnit*0.66/2, gridUnit, 0))
def testBinCompartments():
	test_1x1x3_2D	= binCompartments(1, 1, 3, 2).translate((gridUnit, 0, 0))
	test_1x1x6_2D	= binCompartments(1, 1, 6, 1, 2, tabStyle=TabStyle.NONE).translate((gridUnit*-1, 0, 0))
	test_3x1x6_3D	= binCompartments(3, 1, 6, 3).translate((0, gridUnit, 0))
	test_2x1x3_42D	= binCompartments(2, 1, 3, 4, 2, tabStyle=TabStyle.NONE).translate((-gridUnit/2, -gridUnit, 0))
def testClearWindow():
	test_1x1x1_ClrT	= trayClearWindow(1, 1, 1).translate((gridUnit, 0, 0))
	test_2x1x1_ClrT	= trayClearWindow(2, 1, 1).translate((gridUnit/2, gridUnit, 0))
	test_1x2x3_ClrY = binClearWindow(1, 2, 3, 1, 2, clearSide="Y").translate((-gridUnit, gridUnit/2, 0))
	test_2x1x3_ClrX = binClearWindow(2, 1, 3, 3, 1, 1).translate((-gridUnit*0.5, -gridUnit, 0))
def testAngleTray():
	test_1x1x3_Angle= trayAngleAdaptor().translate((gridUnit,-gridUnit,0))
	test_1x1x9_Angle= trayAngleAdaptor(1, 1, binHeight=9).translate((-gridUnit, -gridUnit, 0))
	test_1x1x6_Angle= trayAngleAdaptor(1, 1, binHeight=6).translate((0, -gridUnit, 0))
	test_2x2x6_Angle= trayAngleAdaptor(2, 2, binHeight=6, bottomDivX=2, bottomDivY=2).translate((gridUnit*0.25, gridUnit*0.5, 0))

testBinSolid()
testSubDivisions()
testBinCompartments()
testClearWindow()
testAngleTray()