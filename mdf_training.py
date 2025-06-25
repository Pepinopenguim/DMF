"""
source: https://pythonnumericalmethods.studentorg.berkeley.edu/notebooks/chapter23.03-Finite-Difference-Method.html

EXAMPLE: Solve the rocket problem in the previous section using the finite difference method, plot the altitude of the rocket after launching. The ODE is

d²y/dt² = -g

y(0) = 0
y(5) = 50

use n = 10

well, we have
y0 = 0
y(i-1) -2y(i) + y(i+1) = -g*h²
y10 = 50

"""

import numpy as np
import matplotlib.pyplot as plt
plt.style.use("Solarize_Light2")
#%matplotlinb inline

x0, x1 = 0, 5

g = 9.81

n = 10
h = (x1 - x0)/n

# get matrix
A = np.zeros((n+1, n+1))
A[0, 0] = 1
A[n, n] = 1

for i in range(1, n):
    A[i, i-1] = 1
    A[i, i] = -2
    A[i, i+1] = 1

# get B
B = np.zeros(n+1)
for i in range(0, n+1):
    if i == 0:
        B[i] = 0
    elif i == n:
        B[i] = 50
    else:
        B[i] = -g*h**2

print(B)

y = np.linalg.solve(A, B)
t = np.linspace(x0, x1, n+1)


plt.figure(figsize=(10, 8))
plt.plot(t, y)
#plt.plot(5, 50, "ro")
plt.show()