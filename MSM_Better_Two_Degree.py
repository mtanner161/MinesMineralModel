"""
Name:           Mines Mineral Model
Developer:      Michael Tanner, Wilson Martin
Date:           8/22/2021
Description:    
"""
# packages

import os
from typing import cast
import pandas as pd
import numpy as np
import math
import numpy.matlib as mat
import csv
import copy
from pandas.core.arrays.string_ import StringDtype
from datetime import datetime


# Creating our MFA function to be used
def MFA(yearK, yearY):
    ratio = yearK / yearY
    constant = 3.5  # assumption
    mfaValue = (constant / yearY) * pow(ratio, 2.5) * \
        math.exp(-pow(ratio, constant))
    return mfaValue


# import
techList = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/techListXls.xlsx"
)  # Technology List (oil, gas etc...)
mineralList = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/mineralListXls.xlsx"
)  # Mineral List of raw minerals being used
energyScenario = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/energyScenerio_IEABeyond2Degree.xlsx"
)  # Energy Secenario being tested
lifetime = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/lifetime.xlsx"
)  # Lifetime of Each technology MUST MATCH
techShares = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/techShares.xlsx", sheet_name=0
)  # reads in the sub-tech breakdown - indexed to first tab in the sheet
currentProd = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/currentMineralProduction.xlsx"
)  # reads in current mineral production
techIntensity = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/currentTechIntensity.xlsx"
)  # reads in latest Tech Intensity
recycleRates = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/recycleRates.xlsx"
)  # reads in recycle rates for each of the minerals
mineralMetalConvert = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/metalMineralConvert.xlsx"
)  # read in metal to mineral conversion
mineralPrice = pd.read_excel(
    r"./minesmineralmodel/Inputs/two_degree/mineralPrice.xlsx"
)  # read in mineralPrice


# Creating our change in GW's for upcoming loop
energyScenarioCopy = energyScenario.copy()
stockArray = energyScenario.to_numpy()
stockArrayCopy = np.copy(stockArray, order="C", subok=True)
stockArray = np.delete(stockArray, 0, 1)

# Creating counter year and technology variables
numberOfYears = len(stockArray) - 1
numberOfTech = len(lifetime)
numberofTechCopy = copy.deepcopy(numberOfTech)

# intialzing a table with all zeros
deltaES = np.zeros([numberOfYears, numberOfTech], dtype=float)

# Takes the year-by-year difference of each technolgoy (GW/time)
for i in range(0, numberOfTech):
    for j in range(0, numberOfYears):
        deltaES[j][i] = stockArray[j + 1][i] - stockArray[j][i]

# Final Table which will hold Inflow per technology
inflowTotal = np.zeros([numberOfYears, numberOfTech], dtype=float)

# Inflow/Outflow Calulations
# Double For Loops
# below loop covers the cycle through the lifetimes of each of the
for tech in range(0, numberOfTech):

    techLifetime = lifetime.iloc[tech, 1]  # sets table
    deltaES_tech = deltaES[
        :, tech
    ]  # selects column vector of stock change for the technology
    h = 0  # counter for upcoming MFA calculation
    v = np.zeros([50, 50], dtype=float)  # creates a 50x50 array with 0's
    np.fill_diagonal(v, 1)  # fills the 50x50 arrary diagonal with 1's
    counter = 0  # setting a counter variable to 0

    for x in range(numberOfYears):

        year = x + 1  # year counter
        lenDiag = numberOfYears - year - 1
        g = MFA(year, techLifetime)
        h = h + g  # keeps track of the total MFA values
        counter = counter + 1
        i = 0  # counter for while loop

        # adding the new g value to the correct diag
        while i <= lenDiag:

            v[counter + i][i] = -g
            i = i + 1

    vInverse = np.linalg.inv(v)  # competes the inverse of the matrix v
    inflow = np.matmul(
        vInverse, deltaES_tech
    )  # multiples vInverse and DeltaES_tech together
    inflowTotal[:, tech] = inflow  # adding to correct column

outflowTotal = inflowTotal - deltaES

# Breakdown of Flows between different subtypes

# coverts techShares to an array for calculations
subTechArray = techShares.to_numpy()
sumTechArray = np.sum(subTechArray[:, 1], 0)
# creating our inflow and outflow tables that will expand with
techInflow = np.zeros([numberOfYears, sumTechArray], dtype=float)
techOutflow = np.zeros([numberOfYears, sumTechArray], dtype=float)
# temp variable for inner for lop on subtechnology
subTechInflow = np.zeros([numberOfYears, 1])
subTechOutflow = np.zeros([numberOfYears, 1])

# counter for upcoming for loop (needs to be different than numberOfTech because we are increasing to new value)
counterTotalNumberOfTech = 0

totalTechList = []  # empty array used for

# Adding sub technology use percents to total inflow/outflow breakdown
for i in range(numberOfTech):

    # checks sub technolgoy array to see if any sub tech's exist
    if subTechArray[i][1] == 1:
        # take entire
        techInflow[:, counterTotalNumberOfTech] = inflowTotal[:, i]
        techOutflow[:, counterTotalNumberOfTech] = outflowTotal[:, i]
        totalTechList.append(subTechArray[i][0])
        counterTotalNumberOfTech = counterTotalNumberOfTech + 1
    else:
        tempSubTechVar = pd.read_excel(
            r"./minesmineralmodel/Inputs/two_degree/techShares.xlsx",
            sheet_name=subTechArray[i][0],
        )
        subTechNames = list(tempSubTechVar.columns)
        tempSubTechVar = tempSubTechVar.to_numpy()

        # adding the new subtech to the inflow table
        for subTech in range(subTechArray[i][1]):
            for j in range(numberOfYears):
                subTechInflow[j] = inflowTotal[j][i] * \
                    tempSubTechVar[j][subTech]
                subTechOutflow[j] = outflowTotal[j][i] * \
                    tempSubTechVar[j][subTech]

            totalTechList.append(
                subTechArray[i][0] + "-" + subTechNames[subTech])

            techInflow[:, counterTotalNumberOfTech] = subTechInflow[:, 0]
            techOutflow[:, counterTotalNumberOfTech] = subTechOutflow[:, 0]
            counterTotalNumberOfTech = counterTotalNumberOfTech + 1

# sets the new total number of technology variation to be used in later calculations
numberOfTech = counterTotalNumberOfTech

techIntensityNP = techIntensity.to_numpy()  # changes to array for calculations
techIntensityNP = techIntensityNP[:, 1: len(mineralList) + 1]


# setting up blank arrays for upcoming loop
B = np.zeros([numberOfYears, len(mineralList)], dtype=float)
Bout = np.zeros([numberOfYears, len(mineralList)], dtype=float)
matFlow = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float)
matFlowOut = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float)

# Looping over each technology and creating material demand per year
for i in range(0, numberOfTech):

    # selects inflows for all years for i-column technology
    jin = techInflow[:, i]
    # selects outflow for all years for i-column technology
    jout = techOutflow[:, i]
    # selects techIntensity for all years in the i-row
    k = techIntensityNP[i, :]

    for m in range(0, numberOfYears):
        for n in range(0, len(mineralList)):
            B[m][n] = (
                jin[m] * k[n]
            )  # creating matFlow one-bye one matrix by taking jin at year,mineral and multiply by techIntensity for the given mineral
            Bout[m][n] = (
                -1 * jout[m] * k[n]
            )  # creating matFlowOut one-by-one (same as row above)

    # adding matFlow and matFlowout tables together
    matFlow[:, :, i] = B
    matFlowOut[:, :, i] = Bout


# Creating copies of matFlow for new variables
matFlowIn = np.copy(matFlow, order="C", subok=True)
matFlowIn[matFlowIn < 0] = 0  # removes any negative and replaces with zero
# creating arrays for upcoming loops
matFlowOutPre = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float)
matFlowOutFinal = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float)
totalMatFlowIn = np.zeros([numberOfYears, len(mineralList)], dtype=float)
totalMatFlowOut = np.zeros([numberOfYears, len(mineralList)], dtype=float)

# replace all positives of matFlow (inflow) as 0 and AGAIN switch signs
for i in range(0, numberOfYears):
    for j in range(0, len(mineralList)):
        for k in range(0, numberOfTech):

            if matFlow[i][j][k] < 0:
                matFlowOutPre[i][j][k] = -matFlow[i][j][k]
            else:
                matFlowOutPre[i][j][k] = 0

            matFlowOutFinal[i][j][k] = matFlowOut[i][j][k] + \
                matFlowOutPre[i][j][k]

# sum of matFlow for totalMatFlowIn/Out
for i in range(0, numberOfYears):
    for j in range(0, len(mineralList)):

        h1 = 0
        h2 = 0

        for k in range(0, numberOfTech):
            h1 = h1 + matFlowIn[i][j][k]
            h2 = h2 + matFlowOutFinal[i][j][k]

        totalMatFlowIn[i][j] = h1
        totalMatFlowOut[i][j] = h2


recycleArray = recycleRates.to_numpy()  # converts our RR table to array

matFlowInFromRecycle = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float
)  # setting at 3x3 array
recycleArray = np.delete(recycleArray, 0, axis=1)  # removes first column


# use the RR to split inflows into virgin and recycles material
for i in range(0, numberOfYears):
    for j in range(0, len(mineralList)):

        currentRecycleRate = recycleArray[j]

        for k in range(0, numberOfTech):
            matFlowInFromRecycle[i][j][k] = (
                currentRecycleRate * matFlowOutFinal[i][j][k]
            )


# sets up our virgin
matFlowInVirgin = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float)

# use RR rates to split demand in virgin (new) and recylced production
for i in range(0, numberOfYears):
    for j in range(0, len(mineralList)):
        for k in range(0, numberOfTech):
            matFlowInVirgin[i][j][k] = (
                matFlowIn[i][j][k] - matFlowInFromRecycle[i][j][k]
            )

totalMatFlowInFromRecycle = np.zeros(
    [numberOfYears, len(mineralList)], dtype=float
)  # setting at 3x3 array
totalMatFlowInVirgin = np.zeros(
    [numberOfYears, len(mineralList)], dtype=float
)  # setting at 3x3 array

# summing across all technologies for totalVirgin and RR tables in to one
for i in range(0, numberOfYears):
    for j in range(0, len(mineralList)):

        h1 = 0
        h2 = 0

        for k in range(0, numberOfTech):
            h1 = h1 + matFlowInFromRecycle[i][j][k]
            h2 = h2 + matFlowInVirgin[i][j][k]

        totalMatFlowInFromRecycle[i][j] = h1
        totalMatFlowInVirgin[i][j] = h2


# Currently not used due to lack of data
# mineralMetalArray = mineralMetalConvert.to_numpy()
# mineralMetalArray = np.delete(mineralMetalArray,0,axis=1) #removes first column

# mineralFlowInVirgin = np.zeros([numberOfYears,len(mineralList),numberOfTech], dtype=float)

# for i in range(0,numberOfYears):
#   for j in range(0,len(mineralList)):
#     for k in range(0,numberOfTech):
#       mineralFlowInVirgin[i][j][k] = mineralMetalArray[j] * mineralFlowInVirgin[i][j][k]


# set up our 2x2 arrays for cumulative demand
cumMatFlowInVirgin = np.zeros([len(mineralList), numberOfTech], dtype=float)
cumMatFlowOut = np.zeros([len(mineralList), numberOfTech], dtype=float)

# sum across all years for each of the minerals and technologies for total demand
for i in range(0, len(mineralList)):
    for j in range(0, numberOfTech):

        h1 = 0
        h2 = 0

        for k in range(0, numberOfYears):

            h1 = (
                h1 + matFlowInVirgin[k][i][j]
            )  # notice change in order k,i,j - counter k is the years we are summing across
            h2 = h2 + matFlowOut[k][i][j]

        cumMatFlowInVirgin[i][j] = h1
        cumMatFlowOut[i][j] = h2

# convert our mineralPrice to an array for calculations
mineralPriceArray = mineralPrice.to_numpy()
mineralPriceArray = np.delete(
    mineralPriceArray, 0, axis=1)  # remove the first column

# setting our array for Market Size
virginMarketSizeLow = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float
)
virginMarketSizeMed = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float
)
virginMarketSizeHigh = np.zeros(
    [numberOfYears, len(mineralList), numberOfTech], dtype=float
)

# calculate the Virgin Market Size
for i in range(0, numberOfYears):
    for j in range(0, len(mineralList)):
        for k in range(0, numberOfTech):
            virginMarketSizeLow[i][j][k] = (
                matFlowInVirgin[i][j][k] * mineralPriceArray[j][0]
            )
            virginMarketSizeMed[i][j][k] = (
                matFlowInVirgin[i][j][k] * mineralPriceArray[j][1]
            )
            virginMarketSizeHigh[i][j][k] = (
                matFlowInVirgin[i][j][k] * mineralPriceArray[j][2]
            )


totalVirginMarketSizeLow = np.zeros(
    [numberOfYears, len(mineralList)], dtype=float)
totalVirginMarketSizeMed = np.zeros(
    [numberOfYears, len(mineralList)], dtype=float)
totalVirginMarketSizeHigh = np.zeros(
    [numberOfYears, len(mineralList)], dtype=float)

# summing across all technologies for totalVirgin and RR tables in to one
for i in range(0, numberOfYears):
    for j in range(0, len(mineralList)):

        h1 = 0
        h2 = 0
        h3 = 0

        for k in range(0, numberOfTech):
            h1 = h1 + virginMarketSizeLow[i][j][k]
            h2 = h2 + virginMarketSizeMed[i][j][k]
            h3 = h3 + virginMarketSizeHigh[i][j][k]

        totalVirginMarketSizeLow[i][j] = h1
        totalVirginMarketSizeMed[i][j] = h2
        totalVirginMarketSizeHigh[i][j] = h3


# setting our cumulative market size for low, med and high
cumVirginMarketSizeLow = np.zeros(
    [len(mineralList), numberOfTech], dtype=float)
cumVirginMarketSizeMed = np.zeros(
    [len(mineralList), numberOfTech], dtype=float)
cumVirginMarketSizeHigh = np.zeros(
    [len(mineralList), numberOfTech], dtype=float)

# summing up market size by year
for i in range(0, len(mineralList)):
    for j in range(0, numberOfTech):

        h1 = 0
        h2 = 0
        h3 = 0

        for k in range(0, numberOfYears):

            h1 = (
                h1 + virginMarketSizeLow[k][i][j]
            )  # notice change in order k,i,j - counter k is the years we are summing across
            h2 = h2 + virginMarketSizeMed[k][i][j]
            h3 = h3 + virginMarketSizeHigh[k][i][j]

        cumVirginMarketSizeLow[i][j] = h1
        cumVirginMarketSizeMed[i][j] = h2
        cumVirginMarketSizeHigh[i][j] = h3

###MODEL COMPLETE - the below code only cleans spreadsheets to make it easier to visualize###
###Creating the formatted PowerBi tables###


mineralListPandas = []
subMineralList = mineralList.to_numpy()

for i in range(0, len(mineralList)):
    mineralName = subMineralList[i][0]
    mineralListPandas.append(mineralName)


cleanDemandPandas = pd.DataFrame(
    totalMatFlowInVirgin, columns=mineralListPandas)

cleanMarketSizePandas = pd.DataFrame(
    totalVirginMarketSizeMed, columns=mineralListPandas)

cleanDemandPandas.to_excel(
    r"./minesmineralmodel/outputs/two_degree/cleanDemandPandas.xlsx", index=False
)

cleanMarketSizePandas.to_excel(
    r"./minesmineralmodel/outputs/two_degree/cleanMarketSize Pandas.xlsx", index=False
)

print(type(mineralList))
print(type(subMineralList))


# Clean the energy scenerio
fp = open(
    "./minesmineralmodel/outputs/two_degree/cleanIeaPowerBi.csv", "w"
)  # setting a file pointer
fp.write("Year,Technolgy,Energy\n")

for i in range(0, numberOfYears + 1):

    year = stockArrayCopy[i][0]

    for j in range(0, numberofTechCopy):
        techName = subTechArray[j][0]
        fp.write("1/1/%d," % year)
        fp.write("%s," % techName)
        fp.write("%4f\n" % stockArray[i][j])

fp.close()

# Clean the cumulative virgin demand size
fp = open(
    "./minesmineralmodel/outputs/two_degree/cleanMarketSize.csv", "w"
)  # setting a file pointer
fp.write("Year,Material,USD Low, USD Med, USD High\n")

subMineralList = mineralList.to_numpy()

for i in range(0, numberOfYears):

    year = stockArrayCopy[i][0] + 1

    for j in range(0, len(mineralList)):
        mineralName = subMineralList[j][0]
        fp.write("1/1/%d," % year)
        fp.write("%s," % mineralName)
        fp.write("%2f," % totalVirginMarketSizeLow[i][j])
        fp.write("%2f," % totalVirginMarketSizeMed[i][j])
        fp.write("%2f\n" % totalVirginMarketSizeHigh[i][j])

fp.close()

# Clean the recyclying spreadsheet
fp = open(
    "./minesmineralmodel/outputs/two_degree/cleanRecyclying.csv", "w"
)  # setting a file pointer
fp.write("Year,Material,Tons\n")

for i in range(0, numberOfYears):

    year = stockArrayCopy[i][0] + 1

    for j in range(0, len(mineralList)):
        mineralName = subMineralList[j][0]
        fp.write("1/1/%d," % year)
        fp.write("%s," % mineralName)
        fp.write("%2f\n" % (totalMatFlowInFromRecycle[i][j] * -1))

fp.close()

# Clean the virgin market size spreadsheet
fp = open(
    "./minesmineralmodel/outputs/two_degree/cleanDemand.csv", "w"
)  # setting a file pointer
fp.write("Year,Material,Tons\n")

for i in range(0, numberOfYears):

    year = stockArrayCopy[i][0] + 1

    for j in range(0, len(mineralList)):
        mineralName = subMineralList[j][0]
        fp.write("1/1/%d," % year)
        fp.write("%s," % mineralName)
        fp.write("%2f\n" % totalMatFlowInVirgin[i][j])

fp.close()


fp = open("./minesmineralmodel/outputs/two_degree/cleanTechIntensity.csv", "w")
fp.write("Technology, Material, Tech Intensity\n")

for i in range(0, counterTotalNumberOfTech):
    techName = totalTechList[i]

    for j in range(0, len(mineralList)):
        mineralName = subMineralList[j][0]
        fp.write("%s," % techName)
        fp.write("%s," % mineralName)
        fp.write("%2f\n" % techIntensityNP[i][j])

fp.close()


timeNow = datetime.now()
timestampStr = timeNow.strftime("%d-%b-%Y (%H:%M:%S.%f)")

fp = open("./minesmineralmodel/outputs/two_degree/refreshTime.csv", "w")
fp.write("Date-Time\n")
fp.write(timestampStr)
fp.close()

print("IEA Two Degree Scenerio Done")

print("done")
