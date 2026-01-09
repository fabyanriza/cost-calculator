import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Shipping Calculation Dashboard", layout="wide")

# ==========================================
# 1. DATABASE SETUP
# ==========================================

# A. DATA KAPAL 
data_kapal = {
    "Nama Kapal": ["AKA", "ASJ", "ASN", "BGI", "BKU", "BSA", "PBI", "OSI", "ORU"],
    "ME_Cons_L_Day": [4050, 6800, 10500, 4500, 4500, 4500, 7410, 34000, 36000],
    "AE_Cons_L_Day": [500, 1100, 1080, 528, 528, 528, 300, 1650, 1800],
    "DOC_OH": [66504323, 93106052, 93106052, 66504323, 66504323, 66504323, 66504323, 133008645, 159610374]
}
df_kapal = pd.DataFrame(data_kapal)

# B. DATA PORT & JARAK
ports_order = [
    "AMB","BPN","BMS","BTM","BTL","BAU","BRU","BIA","BIT","FAK","GTO","JKT","JYP","KAI","KDR","KTG",
    "LUW","MKS","MRI","MDN","MKE","NBR","NNK","PDG","PAL","PKB","PRW","PNK","SDA","SPT","SMG","SBY",
    "SRI","SRG","TRK","TTE","TIM","TUA"
]

ports_stay = {
    "AMB": 2, "BPN": 1, "BMS": 1, "BTM": 3, "BAU": 2, "BRU": 4, "BIA": 1, "BIT": 2,
    "FAK": 1, "GTO": 1, "JKT": 1, "JYP": 2, "KAI": 1, "KDR": 1, "KTG": 1, "MKS": 1,
    "MRI": 2, "MKE": 2, "NBR": 2, "NNK": 2, "PDG": 1, "PAL": 2, "PKB": 2, "PRW": 2,
    "PNK": 2, "SDA": 1, "SPT": 1, "SMG": 1, "SBY": 1, "SRI": 1, "SRG": 1, "TRK": 1,
    "TTE": 3, "TIM": 2, "TUA": 2,
}


df_port = pd.DataFrame({
    "Port": ports_order,
    "Port_Stay_Hours": [ports_stay.get(port, 1.0) * 24.0 for port in ports_order]
})

# Jarak antar pelabuhan dalam nautical miles (NM)
matrix_data = [
     [0.0, 1284.78, 1509.68, 2729.22, 1348.77, 659.7, 1329.43, 924.05, 617.72, 462.5, 704.85, 2377.86, 1396.6, 623.46, 623.16, 1615.55, 648.54, 991.49, 709.41, 3375.55, 1472.12, 824.31, 1428.26, 3101.49, 964.9, 2979.71, 964.9, 2123.0, 1253.08, 1689.04, 2005.64, 1763.5, 921.08, 433.52, 1399.64, 457.58, 970.3, 558.48],
    [1284.78, 0.0, 346.14, 1444.46, 267.53, 801.4, 376.65, 2135.35, 978.75, 1736.13, 722.16, 1228.38, 2663.45, 1905.96, 716.43, 820.7, 668.47, 528.0, 1922.39, 2094.81, 2737.56, 2101.06, 597.08, 1828.29, 344.95, 1696.42, 344.96, 838.55, 79.62, 451.89, 954.68, 661.06, 2149.38, 1607.73, 531.82, 1198.27, 2255.08, 1829.4],
    [1509.68, 346.14, 0.0, 1274.97, 161.35, 922.57, 691.97, 2401.99, 1296.21, 1971.43, 1037.53, 904.14, 2905.72, 2131.45, 893.9, 535.44, 952.77, 573.69, 2185.88, 1948.26, 2913.07, 2333.95, 899.44, 1602.24, 657.05, 1504.49, 657.06, 687.86, 424.8, 197.48, 608.81, 348.67, 2410.16, 1874.12, 836.45, 1497.54, 2468.8, 2025.6],
    [2729.22, 1444.46, 1274.97, 0.0, 1428.61, 2192.17, 1503.43, 3559.73, 2356.18, 3179.12, 2120.21, 869.59, 4101.56, 3350.13, 2142.56, 1548.97, 2102.65, 1848.28, 3351.22, 675.87, 4172.93, 3543.78, 1551.69, 467.21, 1774.92, 266.18, 1774.93, 606.68, 1480.47, 1077.9, 1148.95, 656.63, 3578.53, 3037.37, 1530.75, 2600.1, 3699.51, 3270.59],
    [1348.77, 267.53, 161.35, 1428.61, 0.0, 764.65, 643.07, 2243.99, 1156.3, 1810.71, 898.63, 1053.25, 2745.04, 1970.27, 732.57, 553.17, 803.03, 421.31, 2027.63, 2099.66, 2753.55, 2172.96, 862.01, 1762.96, 524.06, 1661.97, 524.07, 833.5, 344.49, 352.14, 730.97, 429.04, 2251.37, 1716.66, 796.94, 1348.84, 2307.46, 1864.52],
    [659.7, 801.4, 922.57, 2192.17, 764.65, 0.0, 1015.8, 1583.56, 814.6, 1110.13, 661.22, 1741.24, 2032.72, 1250.74, 160.13, 956.12, 496.41, 355.97, 1369.1, 2860.68, 1991.59, 1458.14, 1196.99, 1458.16, 605.99, 1568.42, 606.0, 1592.05, 806.14, 1116.77, 1357.86, 1213.43, 1579.0, 1082.84, 1144.34, 869.44, 1569.36, 1117.7],
    [1329.43, 376.65, 691.97, 1503.43, 643.07, 1015.8, 0.0, 2075.22, 859.83, 1741.3, 645.37, 1493.69, 2633.47, 1920.08, 886.03, 1195.6, 683.41, 836.25, 1873.88, 2800.54, 2873.27, 2098.02, 221.62, 2296.45, 413.0, 2149.31, 413.0, 1768.45, 305.42, 725.61, 1280.28, 1012.53, 2099.31, 1565.55, 156.5, 1110.31, 2276.54, 1887.81],
    [924.05, 2135.35, 2401.99, 3559.73, 2243.99, 1583.56, 2075.22, 0.0, 1216.9, 493.03, 1440.13, 3288.91, 575.82, 435.11, 1538.76, 2539.58, 1466.88, 1911.56, 216.91, 4173.95, 1018.71, 314.09, 2963.4, 4611.02, 2098.98, 4744.74, 2098.98, 3962.49, 2149.38, 3002.22, 3543.78, 314.45, 59.18, 528.6, 2093.4, 964.92, 491.8, 661.09],
    [617.72, 978.75, 1296.21, 2356.18, 1156.3, 814.6, 859.83, 1216.9, 0.0, 928.18, 258.71, 2199.2, 1780.85, 1108.08, 668.44, 1259.44, 377.13, 971.97, 1020.0, 3530.88, 2013.39, 1266.1, 1771.44, 3181.17, 890.05, 3243.13, 890.05, 2775.62, 916.49, 1885.76, 2619.27, 2416.48, 1243.19, 720.18, 879.2, 254.31, 1460.52, 1129.83],
    [462.5, 1736.13, 1971.43, 3179.12, 1810.71, 1110.13, 1741.3, 493.03, 928.18, 0.0, 1096.95, 2839.39, 934.33, 180.4, 1085.27, 1633.35, 1079.82, 1450.98, 301.99, 3817.18, 1086.11, 364.96, 2574.37, 4130.92, 1808.66, 4533.0, 1808.66, 3559.35, 1607.73, 2464.39, 3432.54, 3198.67, 477.05, 257.25, 1789.89, 685.47, 536.26, 279.06],
    [704.85, 722.16, 1037.53, 2120.21, 898.63, 661.22, 645.37, 1440.13, 258.71, 1096.95, 0.0, 1940.52, 1991.32, 1276.33, 502.01, 1159.19, 166.01, 746.01, 1234.15, 3373.56, 2165.14, 1452.66, 1527.96, 2857.24, 723.79, 3037.79, 723.79, 2531.06, 662.52, 1628.89, 2381.23, 2179.92, 1460.88, 922.89, 697.79, 481.8, 1632.86, 1257.6],
    [2377.86, 1228.38, 904.14, 869.59, 1053.25, 1741.24, 1493.69, 3288.91, 2199.2, 2839.39, 1940.52, 0.0, 4298.03, 3033.4, 1747.24, 331.65, 1906.49, 1405.78, 3091.07, 1419.38, 4389.67, 3145.97, 1945.46, 1234.81, 1530.71, 1091.93, 1530.71, 937.72, 1249.12, 846.78, 430.09, 685.63, 3306.16, 2797.79, 1898.61, 2044.04, 3391.31, 2934.16],
    [1396.6, 2663.45, 2905.72, 4101.56, 2745.04, 2032.72, 2633.47, 575.82, 1780.85, 934.33, 1991.32, 4298.03, 0.0, 770.19, 1988.01, 3391.31, 2017.97, 2490.43, 364.02, 4811.54, 600.71, 314.22, 3510.62, 5139.63, 2750.04, 5511.96, 2750.04, 467.21, 2685.36, 3644.74, 4542.45, 4092.67, 577.12, 1182.89, 2644.03, 1524.9, 314.52, 1036.1],
    [623.46, 1905.96, 2131.45, 3350.13, 1970.27, 1250.74, 1920.08, 435.11, 1108.08, 180.4, 1276.33, 3033.4, 770.19, 0.0, 1225.75, 2781.21, 1264.43, 1630.19, 267.35, 4023.89, 854.03, 292.01, 2767.43, 4363.3, 1969.8, 4745.07, 1969.8, 3770.52, 1764.5, 2622.02, 3632.74, 3386.27, 438.1, 485.3, 1976.49, 723.91, 556.43, 98.2],
    [623.16, 716.43, 893.9, 2142.56, 732.57, 160.13, 886.03, 1538.76, 668.44, 1085.27, 502.01, 1747.24, 1988.01, 1225.75, 0.0, 985.29, 336.59, 371.17, 1314.41, 2861.18, 1955.01, 1406.11, 1173.14, 2912.69, 496.11, 2983.77, 496.11, 2426.52, 721.88, 1357.85, 2426.54, 2301.84, 1518.47, 1023.34, 1006.25, 708.45, 1590.49, 1091.83],
    [1615.55, 820.7, 535.44, 1548.97, 553.17, 956.12, 1195.6, 2539.58, 1602.83, 2064.31, 1359.76, 331.65, 3391.31, 2781.21, 985.29, 0.0, 1232.43, 533.26, 2717.0, 1363.96, 3433.02, 2659.68, 1173.61, 1524.94, 937.38, 1409.92, 937.38, 331.1, 828.57, 610.49, 274.48, 488.19, 2549.01, 2064.34, 1214.77, 1728.09, 3030.64, 2658.23],
    [648.54, 668.47, 952.77, 2102.65, 803.03, 496.41, 683.41, 1466.88, 377.13, 1079.82, 166.01, 1906.49, 2017.97, 1264.43, 336.59, 1232.43, 0.0, 590.91, 1254.36, 3326.67, 2199.5, 1473.39, 1369.6, 2795.88, 615.52, 2993.55, 615.52, 2381.22, 614.11, 1628.89, 2186.58, 1993.07, 1481.56, 931.95, 767.44, 426.0, 1681.71, 1255.95],
    [991.49, 528.0, 573.69, 1848.28, 421.31, 355.97, 836.25, 1911.56, 971.97, 1450.98, 746.01, 1405.78, 2490.43, 1630.19, 371.17, 533.26, 590.91, 0.0, 1651.88, 2590.41, 2538.46, 1875.96, 1021.18, 2489.1, 343.95, 2585.24, 343.95, 2005.62, 499.67, 954.68, 1612.88, 1407.34, 1902.74, 1307.82, 837.07, 550.74, 1950.62, 1461.77],
    [709.41, 1922.39, 2185.88, 3351.22, 2027.63, 1369.1, 1873.88, 216.91, 1020.0, 301.99, 1234.15, 3091.07, 364.02, 267.35, 1314.41, 2717.0, 1254.36, 1651.88, 0.0, 4065.02, 885.58, 314.62, 2736.22, 4289.77, 1873.88, 4593.75, 1873.88, 3578.53, 1851.05, 2719.1, 3750.79, 3515.27, 257.05, 531.22, 1950.62, 695.35, 410.47, 369.11],
    [3375.55, 2094.81, 1948.26, 675.87, 2099.66, 2860.68, 2099.02, 4173.95, 2958.69, 3817.18, 2736.95, 1419.38, 4811.54, 4023.89, 2861.18, 1363.96, 3326.67, 2590.41, 4065.02, 0.0, 4882.18, 4163.61, 2095.26, 1108.42, 2590.41, 942.09, 2590.41, 675.87, 2094.81, 1948.26, 1509.68, 1444.46, 4173.95, 3559.73, 2356.18, 3179.12, 4611.54, 4101.56],
    [1472.12, 2737.56, 2913.07, 4172.93, 2753.55, 1991.59, 2800.54, 1018.71, 2013.39, 1086.11, 2165.14, 4389.67, 600.71, 854.03, 1955.01, 3433.02, 2199.5, 2538.46, 885.58, 4882.18, 0.0, 834.36, 3578.53, 5199.83, 2934.16, 5553.72, 2934.16, 467.21, 2737.56, 2934.16, 4545.34, 4091.31, 1000.72, 1357.64, 2797.79, 1741.3, 770.19, 1125.95],
    [824.31, 2101.06, 2333.95, 3543.78, 2172.96, 1458.14, 2098.02, 314.09, 1266.1, 364.96, 1452.66, 3543.78, 314.22, 292.01, 1406.11, 2659.68, 1473.39, 1875.96, 314.62, 4163.61, 834.36, 0.0, 2963.4, 4684.88, 2064.34, 4993.23, 2064.34, 3962.49, 2101.06, 2800.54, 3887.81, 3642.43, 319.56, 695.35, 2098.02, 928.18, 435.11, 533.26],
    [1428.26, 597.08, 899.44, 1551.69, 862.01, 1196.99, 221.62, 2098.98, 890.05, 1808.66, 723.79, 1945.46, 3510.62, 2767.43, 1173.14, 1173.61, 1369.6, 1021.18, 2736.22, 2095.26, 3578.53, 2963.4, 0.0, 2276.54, 556.43, 2255.08, 556.43, 1768.45, 535.09, 899.44, 1848.28, 1561.41, 2101.06, 1764.5, 376.65, 1503.43, 3033.4, 2781.21],
    [3101.49, 1828.29, 1602.24, 467.21, 1762.96, 2522.15, 1936.74, 3962.49, 2775.62, 3559.35, 2531.06, 1234.81, 5139.63, 4363.3, 2912.69, 1524.94, 2795.88, 2489.1, 4289.77, 1108.42, 5199.83, 4684.88, 2276.54, 0.0, 2489.1, 720.18, 2489.1, 467.21, 1828.29, 1602.24, 1053.25, 904.14, 3962.49, 3288.91, 2199.2, 2839.39, 5033.89, 4101.56],
    [964.9, 344.95, 657.05, 1774.92, 524.06, 605.99, 413.0, 1792.84, 640.15, 1405.74, 381.59, 1530.71, 2750.04, 1969.8, 496.11, 937.38, 615.52, 343.95, 1873.88, 2590.41, 2934.16, 2064.34, 556.43, 2489.1, 0.0, 2281.65, 0.0, 1598.37, 358.77, 657.05, 1348.77, 1053.25, 1829.4, 1357.86, 508.6, 1156.3, 2381.23, 1969.8],
    [2979.71, 1696.42, 1504.49, 266.18, 1661.97, 2426.53, 1768.45, 3819.63, 2619.27, 3432.54, 2381.23, 1091.93, 5511.96, 4745.07, 2983.77, 1409.92, 2993.55, 2585.24, 4593.75, 942.09, 5553.72, 4993.23, 2255.08, 720.18, 2281.65, 0.0, 2281.65, 266.18, 1696.42, 1504.49, 937.38, 720.18, 3819.63, 3179.12, 2120.21, 2736.95, 5451.17, 3270.59],
    [964.9, 344.96, 657.06, 1774.93, 524.07, 606.0, 413.0, 1792.84, 640.14, 1405.74, 381.59, 1530.71, 2750.04, 1969.8, 496.11, 937.38, 615.52, 343.95, 1873.88, 2590.41, 2934.16, 2064.34, 556.43, 2489.1, 0.0, 2281.65, 0.0, 1598.37, 358.77, 657.06, 1348.77, 1053.25, 1829.4, 1357.86, 508.6, 1156.3, 2381.23, 1969.8],
    [2123.0, 838.55, 687.86, 606.68, 833.5, 1592.05, 939.01, 2963.4, 1771.44, 2574.37, 1527.96, 937.72, 467.21, 3770.52, 2426.52, 331.1, 2381.22, 2005.62, 3578.53, 675.87, 467.21, 3962.49, 1768.45, 467.21, 1598.37, 266.18, 1598.37, 0.0, 838.55, 687.86, 533.26, 488.19, 2963.4, 2574.37, 1493.69, 1940.52, 4298.03, 3033.4],
    [1253.08, 79.62, 424.8, 1480.47, 344.49, 806.14, 305.42, 2087.53, 916.49, 1698.94, 662.52, 1249.12, 2685.36, 1764.5, 721.88, 828.57, 614.11, 499.67, 1851.05, 2094.81, 2737.56, 2101.06, 535.09, 1828.29, 358.77, 1696.42, 358.77, 838.55, 0.0, 424.8, 899.44, 608.81, 2149.38, 1607.73, 376.65, 978.75, 2135.35, 1905.96],
    [1689.04, 451.89, 197.48, 1077.9, 352.14, 1116.77, 725.61, 2568.75, 1430.25, 2149.03, 1172.94, 846.78, 3644.74, 2622.02, 1357.85, 610.49, 1628.89, 954.68, 2719.1, 1948.26, 2934.16, 2800.54, 899.44, 1602.24, 657.05, 1504.49, 657.06, 687.86, 424.8, 0.0, 573.69, 197.48, 2410.16, 1874.12, 691.97, 1296.21, 2401.99, 2131.45],
    [2005.64, 954.68, 608.81, 1148.95, 730.97, 1357.86, 1280.28, 2924.63, 1885.76, 2464.39, 1628.89, 430.09, 4542.45, 3632.74, 2426.54, 274.48, 2186.58, 1612.88, 3750.79, 1509.68, 4545.34, 3887.81, 1848.28, 1053.25, 1348.77, 937.38, 1348.77, 533.26, 899.44, 573.69, 0.0, 197.48, 3145.97, 2717.0, 1493.69, 1906.49, 4298.03, 3091.07],
    [1763.5, 2149.38, 2410.16, 3578.53, 2251.37, 1579.0, 2099.31, 59.18, 1243.19, 477.05, 1460.88, 685.63, 4092.67, 3386.27, 2301.84, 488.19, 1993.07, 1407.34, 3515.27, 1444.46, 4091.31, 3642.43, 1561.41, 904.14, 1053.25, 720.18, 1053.25, 488.19, 2149.38, 197.48, 197.48, 0.0, 314.45, 477.05, 1243.19, 1460.88, 685.63, 3386.27],
    [921.08, 1607.73, 1874.12, 3037.37, 1716.66, 1082.84, 1565.55, 528.6, 720.18, 257.25, 922.89, 3306.16, 577.12, 438.1, 1518.47, 2549.01, 1481.56, 1902.74, 257.05, 4173.95, 1000.72, 319.56, 2101.06, 3962.49, 1829.4, 3819.63, 1829.4, 2549.01, 2149.38, 2410.16, 3145.97, 314.45, 0.0, 685.47, 1565.55, 922.89, 438.1, 257.25],
    [433.52, 531.82, 836.45, 1530.75, 796.94, 1144.34, 156.5, 2093.4, 879.2, 1789.89, 697.79, 2797.79, 1182.89, 485.3, 1023.34, 2064.34, 931.95, 1307.82, 531.22, 3559.73, 1357.64, 695.35, 1764.5, 3288.91, 1357.86, 3179.12, 1357.86, 2064.34, 1607.73, 1874.12, 2717.0, 477.05, 685.47, 0.0, 697.79, 1096.95, 1276.33, 485.3],
    [1399.64, 1198.27, 1497.54, 2600.1, 1348.84, 869.44, 1110.31, 964.92, 254.31, 685.47, 481.8, 1898.61, 2644.03, 1976.49, 1006.25, 1214.77, 767.44, 837.07, 1950.62, 2356.18, 2797.79, 2098.02, 376.65, 2199.2, 508.6, 2120.21, 508.6, 1493.69, 376.65, 691.97, 1493.69, 1243.19, 1565.55, 697.79, 0.0, 645.37, 1276.33, 981.63],
    [457.58, 2255.08, 2468.8, 3699.51, 2307.46, 1569.36, 2276.54, 491.8, 1460.52, 536.26, 1632.86, 2044.04, 1524.9, 723.91, 708.45, 1728.09, 426.0, 550.74, 695.35, 3179.12, 1741.3, 928.18, 1503.43, 2839.39, 1156.3, 2736.95, 1156.3, 1940.52, 978.75, 1296.21, 1906.49, 1460.88, 922.89, 1096.95, 645.37, 0.0, 1527.96, 1006.25],
    [970.3, 1829.4, 2025.6, 3270.59, 1864.52, 1117.7, 1887.81, 661.09, 1129.83, 279.06, 1257.6, 2934.16, 314.52, 556.43, 1590.49, 3030.64, 1681.71, 1950.62, 410.47, 4611.54, 770.19, 435.11, 3033.4, 5033.89, 2381.23, 5451.17, 2381.23, 4298.03, 2135.35, 2401.99, 4298.03, 3386.27, 438.1, 1276.33, 1276.33, 1527.96, 0.0, 770.19],
    [558.48, 659.06, 836.45, 3270.59, 1864.52, 1117.7, 1887.81, 661.09, 1129.83, 279.06, 1257.6, 2934.16, 1036.1, 98.2, 1091.83, 2658.23, 1255.95, 1461.77, 369.11, 4101.56, 1125.95, 533.26, 2781.21, 4101.56, 1969.8, 3270.59, 1969.8, 3033.4, 1905.96, 2131.45, 3091.07, 3386.27, 257.25, 485.3, 981.63, 1006.25, 770.19, 0.0]
]
df_matrix = pd.DataFrame(matrix_data, columns=ports_order, index=ports_order)
df_jarak_flat = df_matrix.stack().reset_index()
df_jarak_flat.columns = ['Asal', 'Tujuan', 'Jarak']

import pandas as pd

# data thc sesuai tabel
data_thc = {
    "Port": [
        "AMB","BPN","BMS","BTM","BLC","BAU","BRU","BIA","BIT","FAK","GTO","JKT","JYP",
        "KAI","KDR","KTG","LUW","MKS","MRI","BLW","MKE","NBR","NNK","PDG","PAL","PKB",
        "PRW","PNK","SDA","SPT","SMG","SRI","SRG","TRK","TTE","TIM","TUA","SBY"
    ],
    "FL": [
        1454732, 1035101, 688800, 566500, 722267, 724519, 617375, 2635218, 926200, 3656562, 991870, 872500, 1453639,
        445500, 758437, 213300, 1760000, 807904, 2182970, 1080024, 2750000, 2307171, 981747, 973500, 904775, 883589,
        883589, 879000, 940500, 535568, 758437, 1156111, 2132967, 915215, 1581270, 1139815, 2785640, 840215
    ],
    "MT": [
        740860, 716650, 490001, 381260, 403596, 318843, 320100, 1319825, 610060, 804856, 410073, 564400, 690372,
        136510, 363173, 130350, 440000, 437250, 789237, 503982, 664718, 880816, 585935, 566500, 334602, 577931,
        577931, 563850, 636900, 377300, 481800, 590615, 759008, 499934, 318010, 366112, 1193060, 584200
    ],
}
df_thc = pd.DataFrame(data_thc).set_index("Port")

# =========================
# Default TOS (Inbound/Outbound) - sesuai tabel
# =========================
data_tos = {
    "Port": [
        "AMB","BPN","BMS","BTM","BLC","BAU","BRU","BIA","BIT","FAK","GTO","JKT","JYP",
        "KAI","KDR","KTG","LUW","MKS","MRI","BLW","MKE","NBR","NNK","PDG","PAL","PKB",
        "PRW","PNK","SDA","SPT","SMG","SRI","SRG","TRK","TTE","TIM","TUA","SBY"
    ],  
    "Inbound": [
        "CY ( FIOST )","PORT","PORT","CY ( FIOST )","PORT","CY ( FIOST )","PORT","CY","PORT","CY ( FIOST )","PORT","PORT","PORT",
        "CY ( FIOST )","CY ( FIOST )","CY ( FIOST )","CY ( FIOST )","PORT","CY ( FIOST )","PORT","PORT","CY ( FIOST )","CY","CY ( FIOST )","CY",
        "PORT","PORT","CY ( FIOST )","PORT","PORT","CY","CY","PORT","PORT","PORT","CY ( FIOST )","CY ( FIOST )","PORT"
    ],
    "Outbound": [
        "CY ( FIOST )","PORT","PORT","CY ( FIOST )","PORT","CY ( FIOST )","PORT","CY","PORT","CY ( FIOST )","PORT","PORT","PORT",
        "CY","CY ( FIOST )","CY ( FIOST )","CY ( FIOST )","PORT","CY ( FIOST )","PORT","PORT","CY","CY","CY ( FIOST )","CY",
        "PORT","PORT","CY ( FIOST )","PORT","PORT","CY","CY","PORT","PORT","CY ( FIOST )","CY ( FIOST )","CY ( FIOST )","PORT"
    ],
}
df_tos = pd.DataFrame(data_tos).set_index("Port")

# HUBS tetap
HUBS = {"SBY", "JKT"}


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def get_distance(port_a, port_b):
    res = df_jarak_flat[(df_jarak_flat["Asal"] == port_a) & (df_jarak_flat["Tujuan"] == port_b)]
    if not res.empty: return res.iloc[0]["Jarak"]
    return -1

def format_rupiah_compact(x: float) -> str:
    sign = "-" if x < 0 else ""
    n = abs(x)
    if n >= 1_000_000_000:
        val = n / 1_000_000_000
        suffix = " M"
    elif n >= 1_000_000:
        val = n / 1_000_000
        suffix = " JT"
    else:
        return f"Rp {x:,.0f}"
    return f"Rp {sign}{val:,.0f}{suffix}"

def calculate_operational_cost(ship_name, route_str, ship_speed):
    # LOGIC BARU: VARIABLE COST BASED ON TIME
    
    kapal = df_kapal[df_kapal["Nama Kapal"] == ship_name].iloc[0]
    me_cons_daily = kapal["ME_Cons_L_Day"]
    ae_cons_daily = kapal["AE_Cons_L_Day"]
    doc_daily_rate = kapal["DOC_OH"] # Daily Rate

    route_clean = route_str.replace(" ", "").upper()
    ports = route_clean.split("-")
    if len(ports) < 2: return None, "Rute minimal 2 pelabuhan."

    # --- 1. Calculate Sailing Time ---
    total_dist = 0
    total_sailing_days = 0
    
    for i in range(len(ports)-1):
        if ports[i] not in ports_order or ports[i+1] not in ports_order:
            return None, f"Port tidak dikenal: {ports[i]} atau {ports[i+1]}"
        d = get_distance(ports[i], ports[i+1])
        if d < 0: return None, f"Jarak not found: {ports[i]}-{ports[i+1]}"
        
        total_dist += d
        total_sailing_days += (d / ship_speed) / 24

    # --- 2. Calculate Port Time (Based on Default 24 Hours) ---
    total_port_stay_hours = 0
    for p in ports:
        # Ambil durasi sandar dari database (Default 24 jam)
        p_data = df_port[df_port["Port"] == p]
        if not p_data.empty:
            stay_hours = p_data.iloc[0]["Port_Stay_Hours"]
        else:
            stay_hours = 24.0 # Safety default
        total_port_stay_hours += stay_hours

    total_port_days = total_port_stay_hours / 24.0

    # --- 3. Calculate Fuel Physical Units (Liter) ---
    # Sailing: ME + AE
    fuel_me_sailing = total_sailing_days * me_cons_daily
    fuel_ae_sailing = total_sailing_days * ae_cons_daily
    
    # Port: AE Only (ME = 0)
    fuel_me_port = 0
    fuel_ae_port = total_port_days * ae_cons_daily
    
    total_me = fuel_me_sailing + fuel_me_port
    total_ae = fuel_ae_sailing + fuel_ae_port

    # --- 4. Calculate DOC+OH (New Logic: Time Based) ---
    total_days_trip = total_sailing_days + total_port_days
    total_doc_cost = total_days_trip * doc_daily_rate

    # Port Cost dihapus (Rp 0)
    port_cost_rp = 0 

    return {
        "Jarak": total_dist,
        "Sailing_Days": total_sailing_days,
        "Port_Days": total_port_days,
        "Total_Days": total_days_trip,
        
        # Breakdown BBM Detail
        "ME_Sailing_L": fuel_me_sailing,
        "AE_Sailing_L": fuel_ae_sailing,
        "AE_Port_L": fuel_ae_port,
        "ME_L": total_me, # Total ME
        "AE_L": total_ae, # Total AE
        
        "DOC_Daily_Rate": doc_daily_rate, 
        "DOC_Total_Cost": total_doc_cost,
        "Port_Total_Cost": port_cost_rp
    }, None

def generate_revenue_template(route_str):
    ports = route_str.replace(" ", "").upper().split("-")
    if len(ports) < 2: return pd.DataFrame()
    seen_pairs = set()
    rows = []
    for i in range(len(ports)):
        for j in range(i + 1, len(ports)):
            asal, tujuan = ports[i], ports[j]
            if asal == tujuan: continue
            key = (asal, tujuan)
            if key in seen_pairs: continue
            seen_pairs.add(key)
            rows.append({
                "Kombinasi": f"{asal}-{tujuan}", "Port Asal": asal, "Port Tujuan": tujuan,
                "Jumlah Box": 0, "Harga/TEU (Rp)": 0, "Total Revenue (Rp)": 0
            })
    return pd.DataFrame(rows)

def recalculate_revenue():
    updates = st.session_state["editor_revenue"]
    for row_idx, col_dict in updates["edited_rows"].items():
        for col_name, new_val in col_dict.items():  
            st.session_state.df_revenue.at[int(row_idx), col_name] = new_val
    st.session_state.df_revenue["Total Revenue (Rp)"] = (
        st.session_state.df_revenue["Jumlah Box"] * st.session_state.df_revenue["Harga/TEU (Rp)"]
    )

from collections import defaultdict
import pandas as pd

def get_thc_rate(port, jenis, aksi):
    dir_col = "Outbound" if aksi == "L" else "Inbound"

    try:
        tos = str(df_tos.loc[port, dir_col]).strip().upper()
    except KeyError:
        return 0.0

    # FULL + TOS=PORT => THC 0
    if jenis == "FL" and tos == "PORT":
        return 0.0

    try:
        return float(df_thc.loc[port, jenis])
    except KeyError:
        return 0.0



def _build_full_flows(df_revenue):
    """Gabungkan jika ada duplicate leg (asal-tujuan) di df_revenue."""
    flows = defaultdict(float)
    for _, row in df_revenue.iterrows():
        asal  = str(row["Port Asal"]).strip().upper()
        tujuan = str(row["Port Tujuan"]).strip().upper()
        if asal == tujuan:
            continue
        q = float(row["Jumlah Box"])
        flows[(asal, tujuan)] += q
    return flows


def compute_empty_flows(df_revenue):
    """
    Logika baru:
    Untuk setiap pasangan port (a,b):
      net = FULL(a->b) - FULL(b->a)
      jika net > 0 => b surplus empty, kirim empty b->a sebesar net
      jika net < 0 => a surplus empty, kirim empty a->b sebesar -net
    Ini otomatis membuat total empty di suatu port = total inbound - total outbound (jika positif).
    """
    full_flows = _build_full_flows(df_revenue)

    ports = set()
    for a, b in full_flows.keys():
        ports.add(a); ports.add(b)

    empty_flow = defaultdict(float)

    # hitung net per pasangan tanpa syarat "dua arah harus ada"
    ports = sorted(ports)
    for i in range(len(ports)):
        for j in range(i + 1, len(ports)):
            a, b = ports[i], ports[j]
            q_ab = full_flows.get((a, b), 0.0)
            q_ba = full_flows.get((b, a), 0.0)
            net = q_ab - q_ba
            if net > 0:
                empty_flow[(b, a)] += net   # empty balik dari b ke a
            elif net < 0:
                empty_flow[(a, b)] += -net  # empty balik dari a ke b

    return empty_flow


def calculate_total_thc(df_revenue, route_str=None):
    """
    - THC FULL dihitung dari q_full pada leg
    - THC EMPTY dihitung dari q_empty pada leg (hasil net flow)
    - Leg empty yang tidak ada di df_revenue tetap dimasukkan (q_full=0)
    """
    full_flows  = _build_full_flows(df_revenue)
    empty_flows = compute_empty_flows(df_revenue)

    all_legs = set(full_flows.keys()) | set(empty_flows.keys())

    total = 0.0
    detail_rows = []

    for (asal, tujuan) in sorted(all_legs):
        q_full  = full_flows.get((asal, tujuan), 0.0)
        q_empty = empty_flows.get((asal, tujuan), 0.0)

        # kalau dua-duanya 0, skip
        if q_full == 0 and q_empty == 0:
            continue

        # jika HUB-HUB kamu memang tidak dikenakan THC per leg, pertahankan rule ini:
        if asal in HUBS and tujuan in HUBS:
            detail_rows.append([asal, tujuan, q_full, q_empty, 0.0, 0.0, 0.0])
            continue

        # FULL
        thc_full = q_full * (get_thc_rate(asal, "FL", "L") + get_thc_rate(tujuan, "FL", "D"))
        # EMPTY
        thc_empty = q_empty * (get_thc_rate(asal, "MT", "L") + get_thc_rate(tujuan, "MT", "D"))

        subtotal = thc_full + thc_empty
        total += subtotal

        detail_rows.append([asal, tujuan, q_full, q_empty, thc_full, thc_empty, subtotal])

    detail_df = pd.DataFrame(
        detail_rows,
        columns=["Asal", "Tujuan", "Q_full", "Q_empty", "THC_full", "THC_empty", "THC_leg"]
    )
    return total, detail_df

def calculate_total_thc_per_port(df_revenue):
    full_flows  = _build_full_flows(df_revenue)      # dari kode kamu sebelumnya
    empty_flows = compute_empty_flows(df_revenue)    # logika net-flow (yang sudah diperbaiki)

    # port ledger: akumulasi qty & biaya per port
    led = defaultdict(lambda: {
        "Q_full_L": 0.0, "Q_full_D": 0.0,
        "Q_empty_L": 0.0, "Q_empty_D": 0.0,
        "THC_full_L": 0.0, "THC_full_D": 0.0,
        "THC_empty_L": 0.0, "THC_empty_D": 0.0,
    })

    def add_full(asal, tujuan, q_full):
        # rule HUB-HUB => no THC (mengikuti rule kamu sebelumnya)
        if asal in HUBS and tujuan in HUBS:
            return

        # FULL loading di asal
        rate_L = get_thc_rate(asal, "FL", "L")
        led[asal]["Q_full_L"] += q_full
        led[asal]["THC_full_L"] += q_full * rate_L

        # FULL discharging di tujuan
        rate_D = get_thc_rate(tujuan, "FL", "D")
        led[tujuan]["Q_full_D"] += q_full
        led[tujuan]["THC_full_D"] += q_full * rate_D

    def add_empty(asal, tujuan, q_empty):
        if q_empty <= 0:
            return
        # rule HUB-HUB => no THC
        if asal in HUBS and tujuan in HUBS:
            return

        # EMPTY loading di asal
        rate_L = get_thc_rate(asal, "MT", "L")
        led[asal]["Q_empty_L"] += q_empty
        led[asal]["THC_empty_L"] += q_empty * rate_L

        # EMPTY discharging di tujuan
        rate_D = get_thc_rate(tujuan, "MT", "D")
        led[tujuan]["Q_empty_D"] += q_empty
        led[tujuan]["THC_empty_D"] += q_empty * rate_D

    # 1) FULL dari df_revenue (yang sudah digabung oleh _build_full_flows)
    for (asal, tujuan), q_full in full_flows.items():
        add_full(asal, tujuan, q_full)

    # 2) EMPTY dari hasil net-flow
    for (asal, tujuan), q_empty in empty_flows.items():
        add_empty(asal, tujuan, q_empty)

    # build dataframe per port
    rows = []
    total = 0.0
    for port, v in led.items():
        thc_total = (
            v["THC_full_L"] + v["THC_full_D"] +
            v["THC_empty_L"] + v["THC_empty_D"]
        )
        total += thc_total
        rows.append([
            port,
            v["Q_full_L"], v["Q_full_D"], v["Q_empty_L"], v["Q_empty_D"],
            v["THC_full_L"], v["THC_full_D"], v["THC_empty_L"], v["THC_empty_D"],
            thc_total
        ])

    df_port = pd.DataFrame(rows, columns=[
        "Port",
        "Q_full_L", "Q_full_D", "Q_empty_L", "Q_empty_D",
        "THC_full_L", "THC_full_D", "THC_empty_L", "THC_empty_D",
        "THC_port"
    ]).sort_values("THC_port", ascending=False).reset_index(drop=True)

    return total, df_port

# ==========================================
# 3. UI DASHBOARD
# ==========================================
st.title("🚢 Kalkulasi Operasional Kapal (Detail Fuel)")
st.markdown("---")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("1. Input Data Kapal & Rute")
    selected_ship = st.selectbox("Pilih Kapal", df_kapal["Nama Kapal"])
    input_route = st.text_input("Rute (ex: SBY-JKT-MKS)", "SBY-JKT-MKS")
    ship_speed = st.number_input("Kecepatan Kapal (knot)", 1.0, 30.0, 10.0, 1.0)
    
    st.markdown("---")
    st.header("2. Harga Bahan Bakar")
    
    fuel_options = ["MFO (Marine Fuel Oil)", "Biosolar"]
    fuel_prices = {"MFO (Marine Fuel Oil)": 12000, "Biosolar": 17000}
    
    # Dual Input BBM (Sesuai Request)
    fuel_type_me = st.selectbox("Jenis BBM Main Engine (ME)", fuel_options, index=0)
    fuel_type_ae = st.selectbox("Jenis BBM Aux Engine (AE)", fuel_options, index=1)
    
    price_me = fuel_prices[fuel_type_me]
    price_ae = fuel_prices[fuel_type_ae]
    
    st.caption(f"Harga ME: Rp {price_me:,.0f} | Harga AE: Rp {price_ae:,.0f}")
    
    if 'last_route' not in st.session_state: st.session_state.last_route = ""
    if input_route != st.session_state.last_route:
        st.session_state.df_revenue = generate_revenue_template(input_route)
        st.session_state.last_route = input_route

if 'df_revenue' not in st.session_state: st.session_state.df_revenue = pd.DataFrame()

col1, col2 = st.columns([1, 2])

# --- PANEL KIRI: COST CALCULATION ---
with col1:
    st.subheader("Estimasi Biaya Operasional")
    
    res, err = calculate_operational_cost(selected_ship, input_route, ship_speed)
    if err:
        st.error(err)
        total_cost_final = 0
        total_thc = 0
    else:
        # Kalkulasi Biaya Rupiah Per Komponen
        # 1. Sailing ME
        cost_me_sailing = res['ME_Sailing_L'] * price_me
        
        # 2. Sailing AE
        cost_ae_sailing = res['AE_Sailing_L'] * price_ae
        
        # 3. Port AE
        cost_ae_port = res['AE_Port_L'] * price_ae
        
        cost_bbm_total = cost_me_sailing + cost_ae_sailing + cost_ae_port
        
        # Total Variable Cost (BBM + DOC)
        total_cost_final = cost_bbm_total + res['DOC_Total_Cost']
        
        # --- SECTION 1: BBM ---
        st.markdown("#### A. Biaya Bahan Bakar (BBM)")
        with st.container():
            # Pecah 3 Kolom
            c1, c2, c3 = st.columns(3)
            
            # Kolom 1: Sailing ME
            c1.markdown("**Sailing ME**")
            c1.caption(f"Jenis: {fuel_type_me.split(' ')[0]}")
            c1.write(f"Vol: {res['ME_Sailing_L']:,.0f} L")
            c1.write(f"**{format_rupiah_compact(cost_me_sailing)}**")
            
            # Kolom 2: Sailing AE
            c2.markdown("**Sailing AE**")
            c2.caption(f"Jenis: {fuel_type_ae.split(' ')[0]}")
            c2.write(f"Vol: {res['AE_Sailing_L']:,.0f} L")
            c2.write(f"**{format_rupiah_compact(cost_ae_sailing)}**")
            
            # Kolom 3: Port AE
            c3.markdown("**Port AE**")
            c3.caption(f"Jenis: {fuel_type_ae.split(' ')[0]}")
            c3.write(f"Vol: {res['AE_Port_L']:,.0f} L")
            c3.write(f"**{format_rupiah_compact(cost_ae_port)}**")
            
            st.divider()
            st.info(f"Total Biaya BBM: **{format_rupiah_compact(cost_bbm_total)}**")

        # --- SECTION 2: DOC+OH ---
        st.markdown("#### B. Biaya Operasional (DOC+OH)")
        with st.container():
            st.write(f"Total Durasi Trip: **{res['Total_Days']:.1f} Hari**")
            st.caption(f"Daily Rate: {format_rupiah_compact(res['DOC_Daily_Rate'])}")
            st.info(f"Total DOC Cost: **{format_rupiah_compact(res['DOC_Total_Cost'])}**")
            
        # --- Total Cost ---
        st.success(f"### Total Est. Cost: {format_rupiah_compact(total_cost_final)}")
        st.caption("*Belum termasuk THC")

# --- PANEL KANAN: REVENUE & THC ---
with col2:
    st.subheader("Perencanaan Revenue & THC")
    if not st.session_state.df_revenue.empty:
        st.data_editor(
            st.session_state.df_revenue,
            column_config={
                "Kombinasi": st.column_config.TextColumn(disabled=True),
                "Port Asal": st.column_config.TextColumn(disabled=True),
                "Port Tujuan": st.column_config.TextColumn(disabled=True),
                "Jumlah Box": st.column_config.NumberColumn(required=True, min_value=0),
                "Harga/TEU (Rp)": st.column_config.NumberColumn(required=True, min_value=0, format="Rp %d"),
                "Total Revenue (Rp)": st.column_config.NumberColumn(disabled=True, format="Rp %d") 
            },
            hide_index=True, use_container_width=True, key="editor_revenue", on_change=recalculate_revenue
        )
        
        total_rev = st.session_state.df_revenue["Total Revenue (Rp)"].sum()
        total_box = st.session_state.df_revenue["Jumlah Box"].sum()
        
                # Hitung THC berdasarkan Revenue Table
        total_thc, df_thc_detail = calculate_total_thc_per_port(st.session_state.df_revenue)

        # =========================
        # (Opsional) tampilkan rincian THC tetap di sini
        # =========================
        st.markdown("#### Terminal Handling (THC)")
        t1, t2 = st.columns([1, 2])
        t1.metric("Total THC", format_rupiah_compact(total_thc))
        with t2:
            st.markdown("Rincian THC (per Port)")
            st.dataframe(df_thc_detail, use_container_width=True, hide_index=True)

        # =========================
        # HITUNG SEMUA ANGKA TOTAL
        # =========================
        profit = total_rev - total_cost_final - total_thc
        is_profit = profit >= 0

        # =========================
        # TOTAL & SUMMARY DI PALING BAWAH
        # =========================
        st.divider()
        st.markdown("### Ringkasan Akhir (Total)")

        # Baris total utama
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Box", f"{total_box:,.0f} TEUs")
        s2.metric("Total Revenue", format_rupiah_compact(total_rev))
        s3.metric("Total Cost (BBM+DOC)", format_rupiah_compact(total_cost_final))

        s4, s5 = st.columns(2)
        # Profit metric dengan warna hijau/merah via delta_color
        s5.metric(
            "NET PROFIT / (LOSS)",
            format_rupiah_compact(profit),
            delta=("PROFIT" if is_profit else "LOSS"),
            delta_color=("normal" if is_profit else "inverse"),
            help="Revenue - (BBM + DOC + THC)"
        )

        # Total THC ikut berwarna (via delta)
        s4.metric(
            "Total THC",
            format_rupiah_compact(total_thc),
            
            help="Terminal Handling Charges"
        )

