# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 13:42
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : chain_example.py


for i in range(1,numOrbitPlanes+1):
    sat_chain = scenario.Children.New(AgESTKObjectType.eChain, "tg_Chain"+ str(i).zfill(2))
    for j in range(1, numSatsPerPlane+1):
        m = (i - 1) * (numSatsPerPlane) + j + 1
        sat = stkRoot.GetObjectFromPath(satPaths[m-2])
        sat_chain.Objects.AddObject(sat)
    n = (i-1) * (numSatsPerPlane)
    sat_last = stkRoot.GetObjectFromPath(satPaths[n])
    sat_chain.Objects.AddObject(sat_last)
    sat_chain.Objects.AddObject(sat_first)
    sat_chain.Propagate()
    sat_chain.Graphics.PassData = True
    sat_chain.Graphics.Line.Width = 1

for i in range(1,numSatsPerPlane+1):
    sat_chain = scenario.Children.New(AgESTKObjectType.eChain, "yg_Chain"+ str(i).zfill(2))
    for j in range(1, numOrbitPlanes+1):
        m = (j - 1) * (numSatsPerPlane) + i + 1
        sat = stkRoot.GetObjectFromPath(satPaths[m-2])
        sat_chain.Objects.AddObject(sat)