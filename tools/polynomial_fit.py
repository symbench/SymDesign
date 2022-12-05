#!/usr/bin/env python3
# Copyright (C) 2022, Will Hedgecock
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pandas as pd

max_degree = 10
filename = 'battery_data.csv'

data = pd.read_csv(filename)
X, y = data[list(data.keys()[:-1])], data[str(data.keys()[-1])]
X, y = X.to_numpy(), y.to_numpy()

def polynom_fit(inp, *args):
    x=inp[:,0]
    y=inp[:,1]
    res=0
    for order in range(len(args)):
        print(14,order,args[order],x)
        res+=args[order] * x**order
    return res +y

inpDataStr=['({:.1f},{:.1f})'.format(a,b) for a,b in X]
fig, ax = plt.subplots()
ax.plot(np.arange(X.shape[0]), y, label='measuered', marker='o', linestyle='none')

for order in range(5):
    print(27,X)
    print(28,y)
    popt, pcov = curve_fit(polynom_fit, xdata=X, ydata=y, p0=[0]*(order+1) )
    fitData=polynom_fit(X,*popt)
    ax.plot(np.arange(X.shape[0]), fitData, label='polyn. fit, order '+str(order), linestyle='--' )
    ax.legend( loc='upper left', bbox_to_anchor=(1.05, 1))
    print(order, popt)

ax.set_xticklabels(inpDataStr, rotation=90)
plt.show()


# from sklearn.preprocessing import PolynomialFeatures
# from sklearn.linear_model import LinearRegression
# from sklearn.metrics import mean_squared_error
# from sklearn import model_selection
# for i in range(1, 1 + max_degree):
#     linear_regression = LinearRegression()
#     polynomial_features = PolynomialFeatures(degree=i, include_bias=False)
#     features = polynomial_features.fit_transform(X)
#     X_train, X_test, y_train, y_test = model_selection.train_test_split(features, y, test_size=0.01, random_state=42)
#     linear_regression.fit(X_train, y_train)
#     coef_table = pd.DataFrame(list(X.columns)).copy()
#     coef_table.insert(len(coef_table.columns),"Coefs", linear_regression.coef_.transpose())
#     #print(list(zip(linear_regression.coef_, X_train)))
#     print(coef_table)

#     predicted = linear_regression.predict(X_test)
#     rmse = np.sqrt(mean_squared_error(y_test, predicted))
#     print(rmse)
