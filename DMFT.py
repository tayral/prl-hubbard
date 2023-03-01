from typing import Callable
from qat.fermion.hamiltonians import make_anderson_model

import numpy as np
from scipy import sparse
from scipy import optimize
import math

from matplotlib import pyplot as plt

# On définit n_site_bain le nombre de site de bains
# n_site = n_site_bain + 1
# Un nombre en binaire k  de base représente  un ket |n(1,up),n(1,down),...,n(n_site_bain,up),n(n_site_bain,down),n(atom,up),n(atom,down),>
# Le terme en 2k représente le k-eme signifie Par exemple le nombre 1001
# signifie qu'il y a un electron de spin down sur le site d'impureté, et 1 electron de spin up dans le bain
#

def k_eme_chiffre_bin(k: int, n: int) -> int:
    "Rend le terme en 2^k dans l'ecriture en binaire de n"
    return ((n & (1 << k)) >> k)


def creeHAIM(epsilons_t: list[float], v: list[float], U: float, mu: float):
    return make_anderson_model(u=U, mu=mu, v=v, epsilon=epsilons_t).get_matrix(True)


def diag_AIM(epsilons_t: list[float], v: list[float], U: float, mu: float) -> tuple[
    np.ndarray[float], np.ndarray[float]]:
    """Donne les valeurs propre et vecteurs propres du modele d'impurete  du modele d'impurete AIM"""
    HAIM = creeHAIM(epsilons_t, v, U, mu)
    # valeurs_prop, vecteurs_prop = sparse.linalg.eigs(HAIM, which="SR", k=HAIM.shape[0] - 2)
    valeurs_prop, vecteurs_prop = sparse.linalg.eigsh(HAIM, which="SR", k=int(HAIM.shape[0]-2))
    return (valeurs_prop, vecteurs_prop)


def G_loc_base(omega: float, t: float, mu: float, p1: int, p2: int, p3: int, sig_imp_omega) -> float:
    S = 0
    nk = p1 * p2 * p3

    for alpha1 in range(p1):
        for alpha2 in range(p2):
            for alpha3 in range(p3):
                energie_k = -2*t * (
                        np.cos(2 * np.pi * alpha1 / (p1)) + np.cos(2 * np.pi * alpha2 / (p2)) + np.cos(
                    2 * np.pi * alpha3 / (p3)))
                S += 1 / (omega * 1j + mu - energie_k - sig_imp_omega)
    return S / nk


def delta_appro(omega: float, *args) -> float:
    x = list(args)
    n = len(x) // 2
    epsilons_t = x[:n]
    v = x[n:]
    S = 0
    for l in range(len(epsilons_t)):
        S += (v[l] ** 2) / (omega * 1j - epsilons_t[l])
    return S.real


def G_Lehman(valeurs_prop: np.ndarray[float], vecteurs_prop: np.ndarray[float], beta: float, n_site_bain, omegas):
    n_site = n_site_bain + 1
    dim, nb_vp = np.shape(vecteurs_prop)
    N = len(omegas)
    valeurs_prop = valeurs_prop - valeurs_prop[0]
    resu = np.zeros(N,dtype = 'complex_')
    Z = np.sum(np.exp(-beta*(valeurs_prop)))
    S = 0
    somme_coef = 0
    for i in range(nb_vp):
        for j in range(nb_vp):
            prod_scal = 0
            for k in range(2**(2*n_site - 1)):
                sig_k = 2*k + 1
                prod_scal += vecteurs_prop[sig_k, j].conj() * vecteurs_prop[2*k, i]
            prod_scal = np.real(prod_scal)**2 + np.imag(prod_scal)** 2
            somme_coef += (np.exp(-beta*valeurs_prop[i]) + np.exp(-beta*valeurs_prop[j])) * prod_scal
            for n in range(N):
                resu[n] += ((np.exp(-beta*valeurs_prop[i]) + np.exp(-beta*valeurs_prop[j])) * prod_scal ) / (
                        valeurs_prop[j] - valeurs_prop[i] - 1j * omegas[n])
    return -resu/Z

def fit_curve(delta : list[float], omegas : list[float], n:int):

    init = np.ones(2 * n)
    x = omegas
    y_real = np.real(delta)

    popt, pcov = optimize.curve_fit(delta_appro, x, y_real, p0=init,maxfev=10000)

    epsilons_t = popt[:n]
    v = popt[n:]

    v = -np.abs(v)

    return np.concatenate((epsilons_t,v)),pcov




def DMFT(precision: float, U: float, t: float, mu: float, beta: float, p1: int, p2: int, p3: int, n_site_bain: int,N:int):
    """pave droit de cotes p1 p2 p3
    Converge quand Gimp^n+1 - Gimp^n < precision
    N : borne sup pour le calcul des frequences omega_n
    """

    omegas = [(2 * n + 1) * 2 * np.pi / beta for n in range(N)]

    sig_imp = np.zeros(N)

    g_imp_n = math.inf*np.ones(N)
    g_imp_nplus1 = np.zeros(N)

    eps = 0

    while np.sum(np.sum(np.real(g_imp_nplus1-g_imp_n)**2 + np.imag(g_imp_nplus1-g_imp_n)**2)) > precision:

        G_loc = np.array([G_loc_base(omegas[n], t, mu, p1, p2, p3, sig_imp[n]) for n in range(N)])

        """plt.plot(omegas,G_loc.real, "-o", label = 're')
        plt.plot(omegas,(G_loc.imag), '-o',label = 'im')
        plt.legend()
        plt.show()"""

        G_ronde = np.array([1/(sig_imp[n] +  1 / G_loc[n]) for n in range(N)])

        """"plt.plot(omegas,G_ronde.real, "-o", label = 're')
        plt.plot(omegas,G_ronde.imag, '-o',label = 'im')
        plt.legend()
        plt.show()"""

        delta = np.array([omegas[n] * 1j + mu - sig_imp[n] - 1 / G_loc[n] for n in range(N)])

        """plt.plot(omegas,delta.real, "-o", label = 're')
        plt.plot(omegas,delta.imag, '-o',label = 'im')
        plt.legend()
        plt.show()"""

        x = fit_curve(delta = delta,omegas = omegas, n=n_site_bain)[0]


        epsilons_t = x[:n_site_bain]
        v = x[n_site_bain:]

        valeurs_prop, vecteurs_prop = diag_AIM(epsilons_t, v, U, mu)

        g_imp_nplus1, g_imp_n = (1-eps) * G_Lehman(valeurs_prop, vecteurs_prop, beta, n_site_bain, omegas) + eps*g_imp_nplus1 ,g_imp_nplus1

        """plt.plot(omegas, (g_imp_nplus1).real, "-o", label='re')
        plt.plot(omegas, omegas*(g_imp_nplus1).imag, '-o', label='im')
        plt.legend()
        plt.show()"""

        sig_imp = np.array([sig_imp[n] + 1/G_loc[n] - 1 / g_imp_nplus1[n] for n in range(N)])

        """plt.plot(omegas, (sig_imp).real, "-o", label='re')
        plt.plot(omegas, (sig_imp).imag, '-o', label='im')
        plt.legend()
        plt.show()"""


        """print("valeurs propres:")

        print(valeurs_prop[1])


        print("erreur : ")
        print(np.sum(np.real(g_imp_nplus1-g_imp_n)**2 + np.imag(g_imp_nplus1-g_imp_n)**2))

        print("g_imp : ")
        print(g_imp_nplus1[0])

        print("sig_imp :")
        print(sig_imp[0])"""

    print("valeurs propres:")

    print(valeurs_prop[1])

    print("erreur : ")
    print(np.sum(np.real(g_imp_nplus1 - g_imp_n) ** 2 + np.imag(g_imp_nplus1 - g_imp_n) ** 2))

    print("g_imp : ")
    print(g_imp_nplus1[0])

    print("sig_imp :")
    print(sig_imp[0])

    """plt.plot(omegas, G_loc.real, "-o", label='re')
    plt.plot(omegas, (G_loc.imag), '-o', label='im')
    plt.legend()
    plt.title("G_loc(iomega)")
    plt.show()"""

    return sig_imp,g_imp_nplus1,valeurs_prop,vecteurs_prop


def nboccu_moyen_fonda(psi):
    site = 0
    #psi est un array où chaque coefficient est la proba de trouver psi dans un vecteur de base
    # Chacun de ces vecteurs de base est representé par un nombre entre 0 et 2**(2*(N**2))
    nb_moyen = 0
    for i_base in range(np.shape(psi)[0]): # pour chaque vecteur de la base, on regarde le nombre de fermion au site site
        nb_moyen += (abs(psi[i_base])**2) * (k_eme_chiffre_bin(2*site,i_base)*k_eme_chiffre_bin(2*site + 1,i_base))
    return(nb_moyen)




def print_DMFT(precision,t,U_list,beta,p1: int, p2: int, p3: int, n_site_bain: int,N:int):
    omegas = [(2 * n + 1) * 2 * np.pi / beta for n in range(N)]
    resu = []
    for U in U_list:
        mu = U/2
        print(U)
        sig_imp, g_imp_nplus1, valeurs_prop, vecteurs_prop = DMFT(precision = precision,U = U,t= t ,mu= mu,beta= beta,p1=p1,p2=p2,p3=p3,n_site_bain=n_site_bain,N=N)
        resu.append((U,sig_imp,vecteurs_prop[0]))


    for U,sig,etat_fond in resu :
        plt_real = plt.figure(1)
        plt.plot(omegas, sig.real, "-o", label='U='+ str(U)[:3])
        plt.xlim(0, omegas[100])
        plt.ylim(-100, 100)
        plt.legend()
        plt.title("Partie reelle de Sig_imp(omega)")


    for U,sig,etat_fond in resu :
        plt_imag = plt.figure(2)
        plt.plot(omegas, sig.imag, "-o", label='U='+ str(U)[:3])
        plt.xlim(0, omegas[30])
        plt.ylim(-60, 10)
        plt.legend()
        plt.title("Partie imaginaire de Sig_imp(omega)")

    NBMOY =[]

    plt_n_moy = plt.figure(3)

    for U,sig,etat_fond in resu :
        NBMOY.append(nboccu_moyen_fonda(etat_fond))
    plt.xlabel("U")
    plt.ylabel("Nb moyen de double occupation au site d'impureté")
    plt.scatter(U_list, np.array(NBMOY), label="lo", color="r")
    plt.legend()
    plt.show()

if __name__ == '__main__':

    print_DMFT(precision=1e-4, t=1, U_list = [0], beta=10, p1=3, p2=3, p3=3, n_site_bain=1,N=1000)











