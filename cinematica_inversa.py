import numpy as np
import sympy as sp


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


# Cinematica Inversa por método numerico
# Variables simbólicas
q00, q11, q22, q33 = sp.symbols("q0 q1 q2 q3")
l00, l11, l22, l33, l44 = sp.symbols("l0 l1 l2 l3 l4")

l0 = 43.5
l1 = 175
l2 = 175
l3 = 66
l4 = 53

cos = np.cos
sin = np.sin
atan2 = np.arctan2
sqrt = np.sqrt


def fkine(q):
    # Expresiones para las variables articulares
    x1 = (l0 + l1 * sin(q[1]) + l2 * cos(q[2]) + l3) * cos(q[0])
    y1 = (l0 + l1 * sin(q[1]) + l2 * cos(q[2]) + l3) * sin(q[0])
    z1 = l1 * cos(q[1]) - l2 * sin(q[2]) - l4
    yaw1 = np.rad2deg(q[0] + q[3])

    return np.array([x1, y1, z1, yaw1])


delta = 0.001

epsilon = 1e-3

max_iter = 1000  # Maximo numero de iteraciones


def calcular_cinematica_inversa(xd, q):
    # Iteraciones: Metodo de Newton
    for i in range(max_iter):
        q0 = q[0]
        q1 = q[1]
        q2 = q[2]
        q3 = q[3]
        # Calcular la posición actual del efector final
        f = fkine([q0, q1, q2, q3])
        e = xd - f

        JT = 1 / delta * np.array([
            fkine([q0 + delta, q1, q2, q3]) - fkine([q0, q1, q2, q3]),
            fkine([q0, q1 + delta, q2, q3]) - fkine([q0, q1, q2, q3]),
            fkine([q0, q1, q2 + delta, q3]) - fkine([q0, q1, q2, q3]),
            fkine([q0, q1, q2, q3 + delta]) - fkine([q0, q1, q2, q3])
        ])

        J = JT.transpose()

        q = q + np.dot(np.linalg.inv(J), e)

        if q[0] < np.deg2rad(-160):
            q[0] = np.deg2rad(160)
        elif q[0] > np.deg2rad(160):
            q[0] = np.deg2rad(-160)

        if q[1] < np.deg2rad(-25):
            q[1] = np.deg2rad(85)
        elif q[1] > np.deg2rad(85):
            q[1] = np.deg2rad(-25)

        if q[2] < np.deg2rad(-25):
            q[2] = np.deg2rad(105)
        elif q[2] > np.deg2rad(105):
            q[2] = np.deg2rad(-25)

        if q[3] < np.deg2rad(-180):
            q[3] = np.deg2rad(180)
        elif q[3] > np.deg2rad(180):
            q[3] = np.deg2rad(-180)

        # Condición para terminar
        if np.linalg.norm(e) < epsilon:
            print("Los puntos se encuentran dentro del espacio de trabajo")
            break

    return q
