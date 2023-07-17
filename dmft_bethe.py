import numpy as np
import math
from scipy import optimize
import scipy.sparse
from itertools import product
from matplotlib import pyplot as plt
from qat.fermion.hamiltonians import make_anderson_model
from qat.fermion.util import init_creation_ops


def diag_AIM(epsilons_t: list[float], v: list[float], U: float, mu: float, sparse=True) -> tuple[
    np.ndarray[float], np.ndarray[float]]:
    """Donne les valeurs propres et vecteurs propres du modele d'impurete  du modele d'impurete AIM"""

    HAIM = make_anderson_model(u=U, mu=mu, v=v, epsilon=epsilons_t).get_matrix(sparse=sparse)

    if sparse:
        valeurs_prop, vecteurs_prop = scipy.sparse.linalg.eigs(HAIM, which="SR", k=30)
        #valeurs_prop, vecteurs_prop = scipy.sparse.linalg.eigsh(HAIM, which="SR", k=int(HAIM.shape[0]-2))
    else:
        valeurs_prop, vecteurs_prop = np.linalg.eigh(HAIM)
    return valeurs_prop, vecteurs_prop

def G_loc_base_semicirc(omega: float, t=1) -> float:
    """ return G_loc_0 for semicircular dos
    Args:
        t (float): hopping (total bandwidth is 4t)
    """
    semicircular = lambda eps, t: 1/(t*np.pi) *  np.sqrt(1 - (eps/(2*t))**2) # semicircular DOS (integrates to 1)
    
    eps_list = np.linspace(-2*t, 2*t, 100)
    return np.sum(semicircular(eps_list, t)/(omega - eps_list))*(eps_list[1]-eps_list[0])

def G_Lehmann(valeurs_prop: np.ndarray[float], vecteurs_prop: np.ndarray[float],
              beta: float, n_site_bain, omegas):
    n_site = n_site_bain + 1
    dim, nb_vp = np.shape(vecteurs_prop)
    
    valeurs_prop = valeurs_prop - min(valeurs_prop)
    Z = np.sum(np.exp(-beta*valeurs_prop))
    cdag = init_creation_ops(n_site*2)
    
    # checking occupancy
    n_imp = cdag[0].dot(cdag[0].T.conj())
    n_imp += cdag[1].dot(cdag[1].T.conj())
    occ = np.sum([np.exp(-beta*valeurs_prop[i])*vecteurs_prop[: ,i].conj().dot(n_imp.dot(vecteurs_prop[:, i]))
                  for i in range(nb_vp)])/Z
    print("occ = ", occ)
    
    N = len(omegas)
    resu = np.zeros(N,dtype = 'complex_')
    for i, j in product(range(nb_vp), repeat=2):
        prod_scal = abs(vecteurs_prop[:, j].conj().dot(cdag[0].dot(vecteurs_prop[:, i])))**2
        for n in range(N):
            resu[n] += ((np.exp(-beta*valeurs_prop[i]) + np.exp(-beta*valeurs_prop[j])) * prod_scal ) / (
                    valeurs_prop[j] - valeurs_prop[i] - 1j * omegas[n])
    return -resu/Z


def delta_appro(omega: float, *args) -> float:
    x = list(args)
    n = len(x) // 2
    epsilons_t = np.array(x[:n])
    v = np.array(x[n:])
    Delta = np.array([np.sum(v ** 2 / (om*1j - epsilons_t)) for om in omega])
    return np.array(list(Delta.real) + list(Delta.imag))


def fit_curve(delta : list[float], omegas : list[float], n:int):
    x_in = np.array(list(omegas))
    y_in = np.array(list(delta.real) + list(delta.imag))
    init = np.hstack([np.ones(n//2), -np.ones(n//2), np.ones(n)]) + np.random.randn(2*n) # eps, V 
    popt, pcov = optimize.curve_fit(delta_appro, x_in, y_in, p0=init)

    return popt, pcov

def DMFT_bethe(precision: float, U: float, t:float, mu: float, beta: float,
               n_site_bain: int,N:int, max_n_loops=10):
    """DMFT on Bethe lattice
    Converge quand Gimp^n+1 - Gimp^n < precision
    Args:
        U (float): Hubbard U
        t (float): hopping
        N : borne sup pour le calcul des frequences omega_n
    """
    omegas = np.array([(2 * n + 1) * np.pi / beta  for n in range(N)]) # matsubara freqs
    g_imp_nplus1 = np.array([G_loc_base_semicirc(omegas[n]* 1j, t) for n in range(N)])
    
    data = {}
    eps, loop_ind = 0, 0  # eps: mixing factor
    diff  = precision + 1
    while diff > precision:
        
        print(f"=== DMFT loop {loop_ind} ===")

        delta = t**2 * g_imp_nplus1

        # fitting delta -> V, epsilon
        try:
            x, pcov = fit_curve(delta = delta,omegas = omegas, n=n_site_bain)
        except:
            print("Delta:", delta)
            np.save("delta.npy", delta)
            raise
        delta_fit = delta_appro(omegas, *x)
        delta_fit = delta_fit[:len(delta_fit)//2] + 1j*delta_fit[len(delta_fit)//2:]

        G_ronde_fit = np.array([1/(omegas[n] * 1j + mu - delta_fit[n]) for n in range(N)])
        epsilons_t = x[:n_site_bain]
        v = x[n_site_bain:]
        # print("Hyb: ", epsilons_t, v)
        data[f"fit_params_{loop_ind}"] = x 

        # diagonalizing AIM (ED)
        valeurs_prop, vecteurs_prop = diag_AIM(epsilons_t, v, U, mu)
       
        # computing GF
        g_imp_n = g_imp_nplus1
        g_imp_nplus1 = (1-eps) * G_Lehmann(valeurs_prop, vecteurs_prop, beta, n_site_bain, omegas) + eps*g_imp_nplus1

        # computing self-energy
        sig_imp = np.array([1/G_ronde_fit[n] - 1 / g_imp_nplus1[n] for n in range(N)])
        
        diff = np.linalg.norm(g_imp_nplus1-g_imp_n)
        print(f" => diff: {diff}")
        loop_ind += 1
        
        data[f"g_ronde_fit_{loop_ind}"] = G_ronde_fit
        data[f"delta_{loop_ind}"] = delta
        data[f"delta_fit_{loop_ind}"] = delta_fit
        data[f"g_imp_nplus1_{loop_ind}"] = g_imp_nplus1
        data[f"sig_imp_{loop_ind}"] = sig_imp
        
        if loop_ind >= max_n_loops: # not more than 10 loops
            break

    return sig_imp, g_imp_nplus1, valeurs_prop, vecteurs_prop, data
