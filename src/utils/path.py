# -*- coding: utf-8 -*-
# @Time    : 2024/7/15 14:05
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : path.py


import os

import pandas as pd

print("Current Working Directory:", os.getcwd())


if os.path.exists('../../data/time_series.csv'):
    time_df = pd.read_csv('../../data/time_series.csv')
    print(time_df.head())
else:
    print('File does not exist')
