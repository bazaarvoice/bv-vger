import math

def percentile_calculation (percentile, sortedWeeks):
    if not sortedWeeks:
        return 0
    numWeek = len(sortedWeeks)
    percentileIndex = (percentile * numWeek) - 1
    lowerPercentileIndex = math.floor(percentileIndex)
    upperPercentileIndex = lowerPercentileIndex + 1
    diffPercentile = percentileIndex - lowerPercentileIndex
    if (lowerPercentileIndex < 0):
        data = sortedWeeks[0]
    elif (upperPercentileIndex >= numWeek):
        data = sortedWeeks[numWeek-1]
    else :
        percentileFloor = sortedWeeks[int(lowerPercentileIndex)]
        percentileCeil = sortedWeeks[int(upperPercentileIndex)]
        # Perform the interpolation calculation
        data = percentileFloor + diffPercentile * (percentileCeil - percentileFloor)
    return (round(data,2))

def R7PercentileCalculator(percentile, sortedData, lengthOfSortedData):
    rank = (percentile/100 * (lengthOfSortedData-1)) + 1
    fracRank, wholeRank = math.modf(rank)
    wholeRank = int(wholeRank)
    if(fracRank == 0):
        return sortedData[wholeRank-1]

    else:
        currentBound = sortedData[wholeRank-1]
        upperBound = sortedData[wholeRank]
        return (fracRank * (upperBound - currentBound)) + currentBound