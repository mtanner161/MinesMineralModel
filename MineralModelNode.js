// Main Code for Mines Mineral Model
// Author: Michael Tanner

const lib = require("C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/MineralModelFunctionsNode.js");

var selectedPriceIndex = 1;  // 0-Low, 1-Medium, 2-High

// Read in Stock data in GW for various technologies

fileName = 'C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/Inputs/two_degree/energyScenerio_IEABeyond2Degree.xlsx';
var rawResults = [];
rawResults = lib.readExcelFile(fileName, 0);

// Pull out the list of technologies and the raw stock data

var rawStockData = rawResults[1];
var techList = rawResults[0];

numTechnologies = techList.length;

// Remove the first column (years) from the raw Stock data

var StockData = lib.removeColumn(rawStockData, 0);
var yearsInList = lib.getColumn(rawStockData, 0);

var numYears = yearsInList.length - 1;

// Compute difference in Stock usage from year to year

let DeltaS = lib.arrayDiff(StockData);

// Read in the life time data

fileName = 'C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/Inputs/two_degree/lifetime.xlsx';
rawResults = lib.readExcelFile(fileName, 0);
var L = rawResults[1][0];

var InFlow = Array();

// Loop over all technologies in matrix DeltaS to compute the In flow

for (var m = 0; m < numTechnologies-1; m++)
{
    let y = L[m];

    var DeltaS_tech = lib.getColumn(DeltaS, m);

    // Create matrix of size numYears filled with all zeros
    var D = lib.makeArray(numYears, numYears, 0.0);

    // Place one on the main diagonal
    D = lib.addVectorToNegDiag(D, 1, 0);

    // Fill matrix for stock calculation start with for loop to
    // add the off diagonal elements
    for (var k = 0; k < numYears - 1; k++)
    {
        var l = numYears - k - 1;

        var g = -lib.MFA(k+1, y);

        D = lib.addVectorToNegDiag(D, g, k+1);
    }

    // Multiply by the inverse matrix to get inflow
    var invD = lib.inverse(D);
    var inflow = lib.matrixVectorMultiply(invD, DeltaS_tech);

    // Save mth column of matrix Inflow
    InFlow.push(inflow);

}

InFlow = lib.transpose(InFlow);

// Create Outflow matrix for use in recycling calculations

var OutFlow = lib.subtractMatrices(InFlow, DeltaS);

// Read in data with number of sub-technologies

fileName = 'C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/Inputs/two_degree/techShares.xlsx';
rawResults = lib.readExcelFile(fileName, 0);
var techListWithSubTechs = rawResults[0];
var numSubTechs = rawResults[1][0];

// Breakdown flows for different sub-technology types within a resource
// (e.g. solar, battery, etc.)

var subTechCounter = 0;
var TechInFlow = Array();
var TechOutFlow = Array();
for (var m = 0; m < numTechnologies-1; m++)
{
  var num = numSubTechs[m];
  if (num == 1)
  {
    var inFlowCol = lib.getColumn(InFlow, m);
    TechInFlow.push(inFlowCol);

    var outFlowCol = lib.getColumn(OutFlow, m);
    TechOutFlow.push(outFlowCol);
  }
  else
  {
    var inFlowCol = lib.getColumn(InFlow, m);
    var outFlowCol = lib.getColumn(OutFlow, m);

    subTechCounter = subTechCounter + 1;
    rawResults = lib.readExcelFile(fileName, subTechCounter);
    var G = rawResults[1];

    var subMatrixIn = Array();
    var subMatrixOut = Array();
    for (var k = 0; k < numYears; k++)
    {
      var colIn = [];
      var colOut = [];
      for (var l = 0; l < num; l++)
      {
        colIn[l] = G[k][l] * inFlowCol[k];
        colOut[l] = G[k][l] * outFlowCol[k];
      }
      subMatrixIn.push(colIn);
      subMatrixOut.push(colOut);
    }
    for (var i = 0; i < subMatrixIn[0].length; i++)
    {
      TechInFlow.push(lib.getColumn(subMatrixIn, i));
      TechOutFlow.push(lib.getColumn(subMatrixOut, i));
    }
  }
}
TechInFlow = lib.transpose(TechInFlow);
TechOutFlow = lib.transpose(TechOutFlow);

// Import current production rates of materials for comparison

fileName = 'C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/Inputs/two_degree/currentMineralProduction.xlsx';
rawResults = lib.readExcelFile(fileName, 0);
var completeMaterialList = rawResults[0];
var CurrentMatProd = rawResults[1][0];
var totalNumMaterials = completeMaterialList.length;

// Calculate material flows - multiply material intensity by tech inflows

fileName = 'C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/Inputs/two_degree/currentTechIntensity.xlsx';
rawResults = lib.readExcelFile(fileName, 0);
var techIntensityMaterialList = rawResults[0];
var techIntensity = rawResults[1];

// Remove the first two columns and place the results back in the same array

techIntensity = lib.removeColumn(techIntensity, 0);
techIntensity = lib.removeColumn(techIntensity, 0);
techIntensity = lib.replaceBlanksWithZeros(techIntensity);

// Loop over each technology and create material demand per year

var totalTechCount = TechInFlow[0].length;

var MaterialFlow = [];
var MaterialFlowOutEOL = [];
var MaterialFlowIn = [];
for (var i = 0; i < totalTechCount; i++)
{
  var inFlowPerYear = lib.getColumn(TechInFlow, i);
  var outFlowPerYear = lib.getColumn(TechOutFlow, i);
  var intensityForTech = lib.getRow(techIntensity, i);

  // Multiply elements of Inflow and Tech Intensity to get
  // matrix of mineral flows by year

  var B = lib.colArrayTimesRowArray(inFlowPerYear, intensityForTech);
  var Bout = lib.colArrayTimesRowArray(outFlowPerYear, intensityForTech);
  Bout = lib.arrayMultByConstant(Bout, -1.0);

  // Put the results into the ith page of a material flow in matrix

  MaterialFlow.push(B);   // Dimension = [Tech X [Materials X Years]]
  MaterialFlowOutEOL.push(Bout);

  // Replace all negatives of MaterialFlow (outflow) as 0 before creating pages
  // of Material In Flow

  var negB = lib.replaceNegValuesWithZeros(B);

  MaterialFlowIn.push(negB);
}

// Sum across the technology types to get the total material demands by
// year, separate material flow in and out depending on inflows and outflows

// Replace all positives of MaterialFlow (inflow) with 0 and then switch signs

var n1 = MaterialFlow.length;
var n2 = MaterialFlow[0].length;
var n3 = MaterialFlow[0][0].length;

var MaterialFlowOutPre = new Array(n1);
for (var i = 0; i < n1; i++)
{
  MaterialFlowOutPre[i] = new Array(n2);
  for (var j = 0; j < n2; j++)
  {
    MaterialFlowOutPre[i][j] = new Array(n3);
    for (var k = 0; k < n3; k++)
    {
      if (MaterialFlow[i][j][k] < 0)
      {
        MaterialFlowOutPre[i][j][k] = -1.0 * MaterialFlow[i][j][k]
      } else
      {
        MaterialFlowOutPre[i][j][k] = 0.0;
      }
    }
  }
}

var MaterialFlowOut = lib.addMatrices(MaterialFlowOutPre, MaterialFlowOutEOL);

var TotalMaterialFlowIn = lib.sumAcross3DArrayIndex(MaterialFlowIn, 1);
var TotalMaterialFlowOut = lib.sumAcross3DArrayIndex(MaterialFlowOut, 1);

// Import Recycling Rates data

fileName = 'C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/Inputs/two_degree/recycleRates.xlsx';
rawResults = lib.readExcelFile(fileName, 0);

// Get the second column which contains the recylcying rate values
var EolTemp = lib.getColumn(rawResults[1], 1);
var recyclingMineralsList = lib.getColumn(rawResults[1], 0);

// Pull out from the recycling data the values for only the minerals in the list
// defined from the Tech Intensity data file. Keep in the same order

var Eolrr = [];
for (var i = 0; i < completeMaterialList.length; i++)
{
  for (var j = 0; j < recyclingMineralsList.length; j++)
  {
    if (completeMaterialList[i].includes(recyclingMineralsList[j]))
    {
      Eolrr[i] = EolTemp[j];
      break;
    }
  }
}

// At this point you could pull out a selected set from the material list
// Not doing right now.  For now keep the entire list

var keepNumMaterials = totalNumMaterials;

// Use recycling rates to split inflows into virgin and recycled materials

var MaterialFlowInFromRR = [];
for (var i = 0; i < totalTechCount; i++)
{
  MaterialFlowInFromRR[i] = [];
  for (var j = 0; j < numYears; j++)
  {
    MaterialFlowInFromRR[i][j] = [];
    for (var k = 0; k < keepNumMaterials; k++)
    {
      MaterialFlowInFromRR[i][j][k] = Eolrr[k] * MaterialFlowOut[i][j][k];
    }
  }
}

var MaterialFlowInVirgin = lib.subtractMatrices(MaterialFlowIn, MaterialFlowInFromRR);

// Sum across the technologies

var TotalMaterialFlowInFromRR = lib.sumAcross3DArrayIndex(MaterialFlowInFromRR, 1);
var TotalMaterialFlowInVirgin = lib.sumAcross3DArrayIndex(MaterialFlowInVirgin, 1);

// Import tonne metal-to-tonne mineral mineral conversion table

fileName = 'C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/Inputs/two_degree/metalMineralConvert.xlsx';
rawResults = lib.readExcelFile(fileName, 0);
var MineralListTradeName = lib.getColumn(rawResults[1], 1);
var MineralConvFactor = lib.getColumn(rawResults[1], 8)

// Pull out the mineral conversion factors for the selected materials
// For now keep them all

// Compute the Virgin Mineral Flow

var MineralFlowInVirgin = [];
for (var i = 0; i < totalTechCount; i++)
{
  MineralFlowInVirgin[i] = [];
  for (var j = 0; j < numYears; j++)
  {
    MineralFlowInVirgin[i][j] = [];
    for (var k = 0; k < keepNumMaterials; k++)
    {
      MineralFlowInVirgin[i][j][k] = MineralConvFactor[k] * MaterialFlowInVirgin[i][j][k];
    }
  }
}

// MARKET SIZING FOR VIRGIN MATERIALS

fileName = 'C:/Users/MichaelTanner/Documents/code_doc/minesmineralmodel/Inputs/two_degree/mineralPrice.xlsx';
rawResults = lib.readExcelFile(fileName, 0);
var MineralListWithPrices = lib.getColumn(rawResults[1], 0);

// Pull out from the price data the values for only the minerals in the list
// defined from the Tech Intensity data file. Keep in the same order

var tempPrice = lib.getColumn(rawResults[1], 3);
var VirginPricesLow = [];
for (var i = 0; i < completeMaterialList.length; i++)
{
  for (var j = 0; j < MineralListWithPrices.length; j++)
  {
    if (completeMaterialList[i].includes(MineralListWithPrices[j]))
    {
      VirginPricesLow[i] = tempPrice[j];
      break;
    }
  }
}

tempPrice = lib.getColumn(rawResults[1], 4);
var VirginPricesMedium = [];
for (var i = 0; i < completeMaterialList.length; i++)
{
  for (var j = 0; j < MineralListWithPrices.length; j++)
  {
    if (completeMaterialList[i].includes(MineralListWithPrices[j]))
    {
      VirginPricesMedium[i] = tempPrice[j];
      break;
    }
  }
}

tempPrice = lib.getColumn(rawResults[1], 5);
var VirginPricesHigh = [];
for (var i = 0; i < completeMaterialList.length; i++)
{
  for (var j = 0; j < MineralListWithPrices.length; j++)
  {
    if (completeMaterialList[i].includes(MineralListWithPrices[j]))
    {
      VirginPricesHigh[i] = tempPrice[j];
      break;
    }
  }
}

var VirginPrices = [];
if (selectedPriceIndex == 1)
{
  VirginPrices = VirginPricesLow;
} else if (selectedPriceIndex == 2)
{
  VirginPrices = VirginPricesMedium;
} else if (selectedPriceIndex == 3)
{
  VirginPrices = VirginPricesHigh;
}

//  Sum data for all 50 years together 
// (keep technologies and materials separate)
// The dimension of the cumulative arrays is [numTech X numMaterials]

var CumulativeMaterialFlowInVirginByTech = lib.sumAcross3DArrayIndex(MaterialFlowInVirgin, 2);
var CumulativeMaterialFlowOutByTech = lib.sumAcross3DArrayIndex(MaterialFlowOut, 2);

// Find yearly market size data per technology and material using a loop

var VirginMarketSizeLow = [];
var VirginMarketSizeMedium = [];
var VirginMarketSizeHigh = [];
for (var i = 0; i < totalTechCount; i++)
{
  VirginMarketSizeLow[i] = [];
  VirginMarketSizeMedium[i] = [];
  VirginMarketSizeHigh[i] = [];
  for (var j = 0; j < numYears; j++)
  {
    VirginMarketSizeLow[i][j] = [];
    VirginMarketSizeMedium[i][j] = [];
    VirginMarketSizeHigh[i][j] = [];
    for (var k = 0; k < keepNumMaterials; k++)
    {
      VirginMarketSizeLow[i][j][k] = VirginPricesLow[k] * MaterialFlowInVirgin[i][j][k];
      VirginMarketSizeMedium[i][j][k] = VirginPricesMedium[k] * MaterialFlowInVirgin[i][j][k];
      VirginMarketSizeHigh[i][j][k] = VirginPricesHigh[k] * MaterialFlowInVirgin[i][j][k];
    }
  }
}

// Sum across technologies

var TotalVirginMarketSizeLow = lib.sumAcross3DArrayIndex(VirginMarketSizeLow, 1);
var TotalVirginMarketSizeMedium = lib.sumAcross3DArrayIndex(VirginMarketSizeMedium, 1);
var TotalVirginMarketSizeHigh = lib.sumAcross3DArrayIndex(VirginMarketSizeHigh, 1);

// Find reference yearly production and reference yearly market size based on
// reference production values if current production continues

// Pull out the data for the selected materials
// For now take them all

var VirginPricesForSelectedMaterial = VirginPrices;
var CurrentMatProdForSelectedMaterial = CurrentMatProd;

var RefProduction = [];
var RefMarketSize = [];
for (var i = 0; i < numYears; i++)
{
  RefProduction[i] = [];
  RefMarketSize[i] = [];
  for (var j = 0; j < keepNumMaterials; j++)
  {
    RefProduction[i][j] = CurrentMatProdForSelectedMaterial[j];
    RefMarketSize[i][j] = CurrentMatProdForSelectedMaterial[j] * VirginPricesForSelectedMaterial[j];
  }
}

// Find cumulative reference market (added from 2000 to 2050)

var CumulativeRefProduction = lib.sumAcross2DArrayIndex(RefProduction, 1);
var CumulativeRefMarketSize = lib.sumAcross2DArrayIndex(RefMarketSize, 1);

// Find the cumulative market size data per technology and material using a
// continuous loop (added from 2000 to 2050)

var CumulativeVirginMarketSize = [];
for (var i = 0; i < keepNumMaterials; i++)
{
  CumulativeVirginMarketSize[i] = [];
  for (var j = 0; j < totalTechCount; j++)
  {
    CumulativeVirginMarketSize[i][j] = CumulativeMaterialFlowInVirginByTech[j][i] * VirginPricesForSelectedMaterial[i];
  }
}

console.log(CumulativeVirginMarketSize)