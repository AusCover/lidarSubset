#!/usr/bin/env python

"""
Script that subsets a LiDAR file using the extent of polygons in 
a given OGR file. 

For Auscover.
"""

import sys
import numpy
from numba import jit
from pylidar import lidarprocessor
from pylidar.toolbox import insidepoly
from osgeo import ogr

def chop(data, otherArgs):
    """
    Function that is called by pylidar and does the actual
    subsetting. 
    """
    # get all the data
    pulses = data.input.getPulses()
    points = data.input.getPointsByPulse()
    waveformInfo = data.input.getWaveformInfo()
    recv = data.input.getReceived()
    trans = data.input.getTransmitted()

    if len(pulses) == 0:
        return

    # get a mask with the data inside the polygons
    mask = insidepoly.insideLayer(otherArgs.layer, pulses['X_IDX'], pulses['Y_IDX'])
    # subset
    pulses = pulses[mask]
    data.output.setPulses(pulses)
    points = points[..., mask]
    data.output.setPoints(points)

    if data.info.isFirstBlock():
        # copy scaling for these columns
        for col in ['X', 'Y', 'Z']:
            gain, offset = data.input.getScaling(col, lidarprocessor.ARRAY_TYPE_POINTS)
            data.output.setScaling(col, lidarprocessor.ARRAY_TYPE_POINTS, gain, offset)

    # write out the data where we have it
    if waveformInfo is not None and waveformInfo.size > 0:
        waveformInfo = waveformInfo[...,mask]
        data.output.setWaveformInfo(waveformInfo)
    if recv is not None and recv.size > 0:
        recv = recv[:,:,mask]
        data.output.setReceived(recv)
    if trans is not None and trans.size > 0:
        trans = trans[:,:,mask]
        data.output.setTransmitted(trans)

def main(inFile, shpfile, outFile):
    """
    Main function
    """
    # set up and input and output
    dataFiles = lidarprocessor.DataFiles()
    dataFiles.input = lidarprocessor.LidarFile(inFile, lidarprocessor.READ)
    dataFiles.input.setLiDARDriverOption('BUILD_PULSES', False)
    dataFiles.output = lidarprocessor.LidarFile(outFile, lidarprocessor.CREATE)
    dataFiles.output.setLiDARDriver('LAS')

    # open the OGR layer so we pass it in
    otherArgs = lidarprocessor.OtherArgs()
    ogrds = ogr.Open(shpfile)
    otherArgs.layer = ogrds.GetLayer(0)

    # run the processor
    lidarprocessor.doProcessing(chop, dataFiles, otherArgs=otherArgs)

if __name__ == '__main__':
    # input LiDAR file - can be any pylidar supported format
    inFile = sys.argv[1]
    # any OGR supported file - uses first layer - expects polygons
    shpfile = sys.argv[2]
    # output LAS file. Format could be 
    outFile = sys.argv[3]

    main(inFile, shpfile, outFile)
