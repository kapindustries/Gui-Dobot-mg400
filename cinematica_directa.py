import sympy as sp
import numpy as np
import matplotlib.pyplot as plt


class RobotManipulator:
    # Longitudes de los eslabones
    lengths = [43.5, 175, 175, 66, 53]

    def __init__(self, q):
        self.q = q

    def forward_kinematics(self):
        # Transformaciones homogéneas
        T01 = self.sTdh(0, self.q[0], self.lengths[0], -sp.pi / 2)
        T12 = self.sTdh(0, self.q[1] - sp.pi / 2, self.lengths[1], 0)
        T23 = self.sTdh(0, self.q[2] - self.q[1] + sp.pi / 2, self.lengths[2], 0)
        T34 = self.sTdh(0, -self.q[2], self.lengths[3], -sp.pi / 2)
        T45 = self.sTdh(self.lengths[4], self.q[3], 0, 0)

        T02 = sp.simplify(T01 * T12)
        T03 = sp.simplify(T02 * T23)
        T04 = sp.simplify(T03 * T34)

        # Transformación homogénea final
        T05 = sp.simplify(T01 * T12 * T23 * T34 * T45)

        return T01, T02, T03, T04, T05

    @staticmethod
    def sTdh(d, th, a, alpha):
        cth = sp.cos(th)
        sth = sp.sin(th)
        ca = sp.cos(alpha)
        sa = sp.sin(alpha)
        Tdh = sp.Matrix([[cth, -ca * sth, sa * sth, a * cth],
                         [sth, ca * cth, -sa * cth, a * sth],
                         [0, sa, ca, d],
                         [0, 0, 0, 1]])
        return Tdh




