import json
import pandas as pd

diDataRaw = pd.read_excel(
    r"C:\Users\MichaelTanner\Documents\code_doc\minesmineralmodel\energyScenerio_IEABeyond2Degree_Better.xlsx"
)

diDataRaw.to_json(
    r"C:\Users\MichaelTanner\Documents\code_doc\java\msm-web-app\src\testData.json",
    orient="records",
)


print("yay")
