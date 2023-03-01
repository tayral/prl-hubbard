from qat.lang.AQASM import Program, RY, CNOT
from qat.qpus import get_default_qpu
from qat.plugins import ScipyMinimizePlugin


import numpy as np

import qat.fermion

from qat.fermion.transforms import transform_to_jw_basis

import itertools

U = 1
t = 1
mu = 0
p1 = 1
p2 = 2
p3 = 2

n_sites = p1*p2*p3



def H_hubbard(U,t,mu,p1,p2,p3):
    """"fe"""
    n_sites = p1*p2*p3
    grid = [v for v in itertools.product(range(p1),range(p2),range(p3))]

    grid_inv = {

    }

    for n in range(n_sites):
        grid_inv[grid[n]] = n

    voisins = []

    for a,b,c in itertools.product(range(p1),range(p2),range(p3)):
        voisins.append([grid_inv[(a%p1,b%p2,c%p3)],grid_inv[((a+1)%p1,b%p2,c%p3)]])
        voisins.append([grid_inv[(a%p1,b%p2,c%p3)],grid_inv[(a%p1,(b+1)%p2,c%p3)]])
        voisins.append([grid_inv[(a%p1,b%p2,c%p3)],grid_inv[(a%p1,b%p2,(c+1)%p3)]])

    # Convention : i = 2*k_site + sigma

    t_mat = np.zeros((n_sites,n_sites))

    for voisin in voisins :
        t_mat[voisin[0],voisin[1]] = -t/2
    print("ok")

    H = qat.fermion.hamiltonians.make_hubbard_model(t_mat=t_mat, U= U, mu = mu)


    return transform_to_jw_basis(H)

def creeHAIM_q(epsilons_t: list[float], v: list[float], U: float, mu: float):
    return(qat.fermion.hamiltonians.make_anderson_model(u=U, mu=mu, v=v, epsilon=epsilons_t).get_matrix(True))

hamiltonian = H_hubbard(U = U,t = t,mu = mu,p1 = p1,p2 = p2, p3=p3)
matrice = hamiltonian.get_matrix()
print(np.linalg.eig(matrice))

""".get_matrix pour obtenir la matrice 
Calculer le c aavec """

# we construct the variational circuit (ansatz)
prog = Program()
reg = prog.qalloc(2*n_sites)
theta = [prog.new_var(float, '\\theta_%s'%i) for i in range(2*n_sites)]
RY(theta[0])(reg[0])
RY(theta[1])(reg[1])
CNOT(reg[0], reg[1])
circ = prog.to_circ()

# construct a (variational) job with the variational circuit and the observable
job = circ.to_job(observable=hamiltonian)

# we now build a stack that can handle variational jobs
qpu = get_default_qpu()
optimizer_scipy = ScipyMinimizePlugin(method="COBYLA",
                                      tol=1e-6,
                                      options={"maxiter": 200},
                                      x0=[0, 0])
stack = optimizer_scipy | qpu

# we submit the job and print the optimized variational energy (the exact GS energy is -3)
result = stack.submit(job)
print(f"Minimum VQE energy ={result.value}")

# Create a Program
qprog = Program()
# Number of qbits
nbqbits = 2
# Allocate some qbits
qbits = qprog.qalloc(nbqbits)


"chercher adiabatic pour Q (HVA)"


