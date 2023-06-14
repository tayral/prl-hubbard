import numpy as np
import math
from scipy import optimize
from itertools import product
from matplotlib import pyplot as plt
from qat.fermion.hamiltonians import make_anderson_model
from qat.fermion.util import init_creation_ops


def creeHAIM(epsilons_t: list[float], v: list[float], U: float, mu: float, sparse=True):
    return make_anderson_model(u=U, mu=mu, v=v, epsilon=epsilons_t).get_matrix(sparse)


def diag_AIM(epsilons_t: list[float], v: list[float], U: float, mu: float) -> tuple[
    np.ndarray[float], np.ndarray[float]]:
    """Donne les valeurs propre et vecteurs propres du modele d'impurete  du modele d'impurete AIM"""
    HAIM = creeHAIM(epsilons_t, v, U, mu, sparse=False)
    # valeurs_prop, vecteurs_prop = sparse.linalg.eigs(HAIM, which="SR", k=HAIM.shape[0] - 2)
    #valeurs_prop, vecteurs_prop = sparse.linalg.eigsh(HAIM, which="SR", k=int(HAIM.shape[0]-2))
    valeurs_prop, vecteurs_prop = np.linalg.eigh(HAIM)
    return valeurs_prop, vecteurs_prop


def G_loc_base_lattice(omega: float, t: float, mu: float, p1: int, p2: int, sig_imp_omega) -> float:
    """ compute G_loc = sum_k 1/(i omega_n + mu - eps_k - sig_imp """
    S = 0
    for alpha1, alpha2 in product(range(p1), range(p2)):
        energie_k = -2*t * (
                np.cos(2 * np.pi * alpha1 / (p1)) 
                + np.cos(2 * np.pi * alpha2 / (p2))
                )
        S += 1 / (omega * 1j + mu - energie_k - sig_imp_omega)
    nk = p1 * p2
    return S / nk

def G_loc_base_semicirc(omega: float, D=1) -> float:
    """ return G_loc_0 for semicircular dos """
    semicircular = lambda eps, D: 2/np.pi *  np.sqrt(1 - (eps/D)**2) # semicircular DOS (integrates to 1)
    
    eps_list = np.linspace(-D, D, 100)
    return np.sum(semicircular(eps_list, D)/(omega - eps_list))*(eps_list[1]-eps_list[0])

def G_Lehmann(valeurs_prop: np.ndarray[float], vecteurs_prop: np.ndarray[float], beta: float, n_site_bain, omegas):
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
    Delta = np.array([np.sum(v ** 2 / (1j*om - epsilons_t)) for om in omega])
    return np.array(list(Delta.real) + list(Delta.imag))

def fit_curve(delta : list[float], omegas : list[float], n:int):

    x_in = np.array(list(omegas))
    y_in = np.array(list(delta.real) + list(delta.imag))

    init = np.ones(2 * n)
    popt, pcov = optimize.curve_fit(delta_appro, x_in, y_in, p0=init,maxfev=10000)

    return popt, pcov


def DMFT_lattice(precision: float, U: float, t: float, mu: float, beta: float,
                 p1: int, p2: int, n_site_bain: int,N:int, max_n_loops=10):
    """pave droit de cotes p1 p2
    Converge quand Gimp^n+1 - Gimp^n < precision
    Args:
        U (float): Hubbard U
        p1 : number of k points in x direction
        N : borne sup pour le calcul des frequences omega_n
    """
    omegas = [(2 * n + 1) * 2 * np.pi / beta for n in range(N)]
    sig_imp = mu*np.ones(N)  # initialize sig_imp

    g_imp_n = math.inf*np.ones(N)
    g_imp_nplus1 = np.zeros(N)
    
    data = {}

    eps, loop_ind = 0, 0  # eps: mixing factor
    diff  = precision + 1
    while diff > precision:
        
        print(f"=== DMFT loop {loop_ind} ===")

        G_loc = np.array([G_loc_base_lattice(omegas[n], t, mu, p1, p2, sig_imp[n]) for n in range(N)])
        G_ronde = np.array([1/(sig_imp[n] +  1 / G_loc[n]) for n in range(N)])
        delta = np.array([omegas[n] * 1j + mu - 1 / G_ronde[n] for n in range(N)])

        # fitting delta -> V, epsilon
        x, pcov = fit_curve(delta = delta,omegas = omegas, n=n_site_bain)
        delta_fit = delta_appro(omegas, *x)
        delta_fit = delta_fit[:len(delta_fit)//2] + 1j*delta_fit[len(delta_fit)//2:]

        G_ronde_fit = np.array([1/(omegas[n] * 1j + mu - delta_fit[n]) for n in range(N)])
        epsilons_t = x[:n_site_bain]
        v = x[n_site_bain:]
        # print("Hyb: ", epsilons_t, v)

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
        
        data[f"g_loc_{loop_ind}"] = G_loc
        data[f"g_ronde_{loop_ind}"] = G_ronde
        data[f"g_ronde_fit_{loop_ind}"] = G_ronde_fit
        data[f"delta_{loop_ind}"] = delta
        data[f"delta_fit_{loop_ind}"] = delta_fit
        data[f"g_imp_nplus1_{loop_ind}"] = g_imp_nplus1
        data[f"sig_imp_{loop_ind}"] = sig_imp
        
        if loop_ind >= max_n_loops: # not more than 10 loops
            break

    return sig_imp, g_imp_nplus1, valeurs_prop, vecteurs_prop, data

def DMFT_bethe(precision: float, U: float, t:float, mu: float, beta: float,
               n_site_bain: int,N:int, max_n_loops=10):
    """DMFT on Bethe lattice
    Converge quand Gimp^n+1 - Gimp^n < precision
    Args:
        U (float): Hubbard U
        p1 : number of k points in x direction
        N : borne sup pour le calcul des frequences omega_n
    """
    omegas = [(2 * n + 1) * 2 * np.pi / beta for n in range(N)]

    # g_imp_n = math.inf*np.ones(N)
    g_imp_nplus1 = np.array([G_loc_base_semicirc(omegas[n]) for n in range(N)])
    
    data = {}

    eps, loop_ind = 0, 0  # eps: mixing factor
    diff  = precision + 1
    while diff > precision:
        
        print(f"=== DMFT loop {loop_ind} ===")

        delta = t**2 * g_imp_nplus1

        # fitting delta -> V, epsilon
        x, pcov = fit_curve(delta = delta,omegas = omegas, n=n_site_bain)
        delta_fit = delta_appro(omegas, *x)
        delta_fit = delta_fit[:len(delta_fit)//2] + 1j*delta_fit[len(delta_fit)//2:]

        G_ronde_fit = np.array([1/(omegas[n] * 1j + mu - delta_fit[n]) for n in range(N)])
        epsilons_t = x[:n_site_bain]
        v = x[n_site_bain:]
        # print("Hyb: ", epsilons_t, v)

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
