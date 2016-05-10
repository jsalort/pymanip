#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
   A        B        E        M
A  x        694      428      390
B           x        403      974
E                    x        707
M                             x

"""

import numpy as np
from scipy.optimize import fsolve

row_format = "{:>15}" * 5

def bridge_function(R1, R2, R3, R4):
    """
    Calcule les résistances des branches EA, AM, MB, BE en fonction
    des résistances du pont R1, R2, R3, R4.
    """
    
    S = R1+R2+R3+R4
    EA=R1*(R2+R3+R4)/S
    AM=R2*(R1+R3+R4)/S
    MB=R3*(R1+R2+R4)/S
    BE=R4*(R1+R2+R3)/S
    
    return (EA, AM, MB, BE)

def bridge_revert(EA, AM, MB, BE):
    """
    Inverse l'équation (EA, AM, MB, BE) = bridge_function(R1, R2, R3, R4).
    """
    
    Y = np.array([EA, AM, MB, BE])
    func = lambda X : np.array(bridge_function(X[0], X[1], X[2], X[3])) - Y
    m = (EA+AM+MB+BE)/4.0
    X0 = np.array([m, m, m, m])
    Xr = fsolve(func,  X0)
    
    return (Xr[0], Xr[1], Xr[2], Xr[3])

def print_tableau(tableau):
    print row_format.format('', 'A', 'B', 'E', 'M')
    print row_format.format('A', 'x', tableau[0,1], tableau[0,2], tableau[0,3])
    print row_format.format('B', 'x', 'x', tableau[1,2], tableau[1,3])
    print row_format.format('E', 'x', 'x', 'x', tableau[2,3])
    print row_format.format('M', 'x', 'x', 'x', 'x')
    
def compute_bridge(tableau, verbose=True):
    """
    Calcule les résistances du pont à partir du tableau de résistances
    Exemple:
       A        B        E        M
    A  x        694      428      390
    B           x        403      974
    E                    x        707
    M                             x
    
    x = np.nan
    tableau = np.array([[x, 694.0,  428.0,  390.0],
                        [x, x,      403.0,  974.0],
                        [x, x,      x,      707.0],
                        [x, x,      x,      x    ]])
    """
    
    
    
    if verbose:
        print 'Tableau de départ:'
        print_tableau(tableau)
        
    EA = tableau[0, 2]
    AM = tableau[0, 3]
    MB = tableau[1, 3]
    BE = tableau[1, 2]
    
    (R1, R2, R3, R4) = bridge_revert(EA, AM, MB, BE)
    
    if verbose:
        print 'Résistances des jauges:'
        print 'R1 =', R1, ' ohm'
        print 'R2 =', R2, ' ohm'
        print 'R3 =', R3, ' ohm'
        print 'R4 =', R4, ' ohm'
        
        (EA, AM, MB, BE) = bridge_function(R1, R2, R3, R4)
        S = R1+R2+R3+R4
        EM = (R1+R2)*(R3+R4)/S
        AB = (R1+R4)*(R2+R3)/S
        
        print 'Tableau reconstruit à partir de R1, R2, R3, R4:'
        x = np.nan
        tableau = np.array([[x, AB, EA, AM],
                            [x,  x, BE, MB],
                            [x,  x,  x, EM],
                            [x,  x,  x,  x]])
        print_tableau(tableau)
        
    
    return (R1, R2, R3, R4)
    
if __name__ == '__main__':
    x = np.nan
    tableau = np.array([[x, 694.0,  428.0,  390.0],
                        [x, x,      403.0,  974.0],
                        [x, x,      x,      707.0],
                        [x, x,      x,      x    ]])

    compute_bridge(tableau)