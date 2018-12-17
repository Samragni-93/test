import sys
import numpy as np
import time
from functools import reduce

def kernel(direct_adc):

    if (direct_adc.method != "adc(2)" and direct_adc.method != "adc(3)" and direct_adc.method != "adc(2)-e"):
        raise Exception("Method is unknown")

    np.set_printoptions(linewidth=150, edgeitems=10, suppress=True)

    print ("\nStarting spin-orbital direct ADC code..\n")
    print ("Number of electrons:         ", direct_adc.nelec)
    print ("Number of alpha electrons:         ", direct_adc.nelec_a)
    print ("Number of beta electrons:         ", direct_adc.nelec_b)
    print ("Number of basis functions:   ", direct_adc.nmo)
    print ("Number of alpha occupied orbitals: ", direct_adc.nocc_a)
    print ("Number of beta occupied orbitals: ", direct_adc.nocc_b)
    print ("Number of alpha virtual orbitals:  ", direct_adc.nvir_a)
    print ("Number of beta virtual orbitals:  ", direct_adc.nvir_b)
    print ("Nuclear repulsion energy:    ", direct_adc.enuc,"\n")
    

    print ("Number of states:            ", direct_adc.nstates)
    print ("Frequency step:              ", direct_adc.step)
    print ("Frequency range:             ", direct_adc.freq_range)
    print ("Broadening:                  ", direct_adc.broadening)
    print ("Tolerance:                   ", direct_adc.tol)
    print ("Maximum number of iterations:", direct_adc.maxiter, "\n")
    
    print ("SCF orbital energies(alpha):\n", direct_adc.mo_energy_a, "\n")
    print ("SCF orbital energies(beta):\n", direct_adc.mo_energy_b, "\n")

    t_start = time.time()

    # Compute amplitudes
    t_amp = compute_amplitudes(direct_adc)
     
    
    # Compute MP2 energy
    e_mp2 = compute_mp2_energy(direct_adc, t_amp)

     
    print ("MP2 correlation energy:  ", e_mp2)
    print ("MP2 total energy:        ", (direct_adc.e_scf + e_mp2), "\n")

    

    # Compute Green's functions directly
    dos = calc_density_of_states(direct_adc, t_amp)

    print ("Computation successfully finished")
    print ("Total time:", (time.time() - t_start, "sec"))

    # Save to a file or plot depeneding on user input
    # Plot     


    
    
def compute_amplitudes(direct_adc):

    t2_1, t2_2, t1_2, t1_3 = (None,) * 4

    nocc_a = direct_adc.nocc_a
    nocc_b = direct_adc.nocc_b
    nvir_a = direct_adc.nvir_a
    nvir_b = direct_adc.nvir_b

    v2e_oovv_a,v2e_oovv_ab,v2e_oovv_b  = direct_adc.v2e.oovv
    v2e_vvvv_a,v2e_vvvv_ab,v2e_vvvv_b  = direct_adc.v2e.vvvv
    v2e_oooo_a,v2e_oooo_ab,v2e_oooo_b  = direct_adc.v2e.oooo
    v2e_voov_a,v2e_voov_ab,v2e_voov_b  = direct_adc.v2e.voov
    v2e_ooov_a,v2e_ooov_ab,v2e_ooov_b  = direct_adc.v2e.ooov
    v2e_vovv_a,v2e_vovv_ab,v2e_vovv_b  = direct_adc.v2e.vovv
    v2e_vvoo_a,v2e_vvoo_ab,v2e_vvoo_b  = direct_adc.v2e.vvoo
    v2e_oovo_a,v2e_oovo_ab,v2e_oovo_b  = direct_adc.v2e.oovo
    v2e_ovov_a,v2e_ovov_ab,v2e_ovov_b  = direct_adc.v2e.ovov
    v2e_vovo_a,v2e_vovo_ab,v2e_vovo_b  = direct_adc.v2e.vovo
    
    e_a = direct_adc.mo_energy_a
    e_b = direct_adc.mo_energy_b

    d_ij_a = e_a[:nocc_a][:,None] + e_a[:nocc_a]
    d_ij_b = e_b[:nocc_b][:,None] + e_b[:nocc_b]
    d_ij_ab = e_a[:nocc_a][:,None] + e_b[:nocc_b]
    


    d_ab_a = e_a[nocc_a:][:,None] + e_a[nocc_a:]
    d_ab_b = e_b[nocc_b:][:,None] + e_b[nocc_b:]
    d_ab_ab = e_a[nocc_a:][:,None] + e_b[nocc_b:]
    
    D2_a = d_ij_a.reshape(-1,1) - d_ab_a.reshape(-1)
    D2_b = d_ij_b.reshape(-1,1) - d_ab_b.reshape(-1)
    D2_ab = d_ij_ab.reshape(-1,1) - d_ab_ab.reshape(-1)
    
    D2_a = D2_a.reshape((nocc_a,nocc_a,nvir_a,nvir_a))
    D2_b = D2_b.reshape((nocc_b,nocc_b,nvir_b,nvir_b))
    D2_ab = D2_ab.reshape((nocc_a,nocc_b,nvir_a,nvir_b))

        
    D1_a = e_a[:nocc_a][:None].reshape(-1,1) - e_a[nocc_a:].reshape(-1)
    D1_b = e_b[:nocc_b][:None].reshape(-1,1) - e_b[nocc_b:].reshape(-1)
    D1_a = D1_a.reshape((nocc_a,nvir_a))
    D1_b = D1_b.reshape((nocc_b,nvir_b))
    
    
    t2_1_a = v2e_oovv_a/D2_a
    t2_1_b = v2e_oovv_b/D2_b
    t2_1_ab = v2e_oovv_ab/D2_ab


    t2_1 = (t2_1_a , t2_1_ab, t2_1_b)    

    
    t1_2_a = 0.5*np.einsum('akcd,ikcd->ia',v2e_vovv_a,t2_1_a)
    t1_2_a -= 0.5*np.einsum('klic,klac->ia',v2e_ooov_a,t2_1_a)
    
    t1_2_a += np.einsum('akcd,ikcd->ia',v2e_vovv_ab,t2_1_ab)
    t1_2_a -= np.einsum('klic,klac->ia',v2e_ooov_ab,t2_1_ab)
    
    
    
    t1_2_b = 0.5*np.einsum('akcd,ikcd->ia',v2e_vovv_b,t2_1_b)
    t1_2_b -= 0.5*np.einsum('klic,klac->ia',v2e_ooov_b,t2_1_b)
    
    t1_2_b += np.einsum('akcd,ikcd->ia',v2e_vovv_ab,t2_1_ab)
    t1_2_b -= np.einsum('klic,klac->ia',v2e_ooov_ab,t2_1_ab)
    
    t1_2_a = t1_2_a/D1_a
    t1_2_b = t1_2_b/D1_b


    t1_2 = (t1_2_a , t1_2_b)


    if (direct_adc.method == "adc(2)-e" or direct_adc.method == "adc(3)"):

        #print("Calculating additional amplitudes for adc(2)-e and adc(3)")


        t2_2_a = 0.5*np.einsum('abcd,ijcd->ijab',v2e_vvvv_a,t2_1_a)
        t2_2_a += 0.5*np.einsum('klij,klab->ijab',v2e_oooo_a,t2_1_a)
        

        temp = np.einsum('bkjc,kica->ijab',v2e_voov_a,t2_1_a) 
        temp_1 = np.einsum('bkjc,kica->ijab',v2e_voov_ab,t2_1_ab) 
        
        t2_2_a += temp - temp.transpose(1,0,2,3) - temp.transpose(0,1,3,2) + temp.transpose(1,0,3,2)
        t2_2_a += temp_1 - temp_1.transpose(1,0,2,3) - temp_1.transpose(0,1,3,2) + temp_1.transpose(1,0,3,2)
        
    
        t2_2_b = 0.5*np.einsum('abcd,ijcd->ijab',v2e_vvvv_b,t2_1_b)
        t2_2_b += 0.5*np.einsum('klij,klab->ijab',v2e_oooo_b,t2_1_b)
        

        temp = np.einsum('bkjc,kica->ijab',v2e_voov_b,t2_1_b) 
        temp_1 = np.einsum('bkjc,kica->ijab',v2e_voov_ab,t2_1_ab) 
        
        t2_2_b += temp - temp.transpose(1,0,2,3) - temp.transpose(0,1,3,2) + temp.transpose(1,0,3,2)
        t2_2_b += temp_1 - temp_1.transpose(1,0,2,3) - temp_1.transpose(0,1,3,2) + temp_1.transpose(1,0,3,2)
   

        t2_2_ab = np.einsum('abcd,ijcd->ijab',v2e_vvvv_ab,t2_1_ab)
        t2_2_ab += np.einsum('klij,klab->ijab',v2e_oooo_ab,t2_1_ab)
        

        t2_2_ab += np.einsum('bkjc,kica->ijab',v2e_voov_ab,t2_1_a) 
        t2_2_ab += np.einsum('bkjc,kica->ijab',v2e_voov_b,t2_1_ab) 
        
        t2_2_ab -= np.einsum('kbic,kjac->ijab',v2e_ovov_ab,t2_1_ab) 
        
        t2_2_ab -= np.einsum('akcj,ikcb->ijab',v2e_vovo_ab,t2_1_ab) 

        t2_2_ab += np.einsum('akic,kjcb->ijab',v2e_voov_ab,t2_1_b)
        t2_2_ab += np.einsum('akic,kjcb->ijab',v2e_voov_a,t2_1_ab)

        
        t2_2_a = t2_2_a/D2_a
        t2_2_b = t2_2_b/D2_b
        t2_2_ab = t2_2_ab/D2_ab
        

        t2_2 = (t2_2_a , t2_2_ab, t2_2_b)    

    if (direct_adc.method == "adc(3)"):
         
        #print("Calculating additional amplitudes for adc(3)")
        

        t1_3_a = np.einsum('d,ilad,ld->ia',e_a[nocc_a:],t2_2_a,t1_2_a)
        t1_3_a += np.einsum('d,ilad,ld->ia',e_b[nocc_b:],t2_2_ab,t1_2_b)
        
        t1_3_a -= np.einsum('l,ilad,ld->ia',e_a[:nocc_a],t2_2_a,t1_2_a)
        t1_3_a -= np.einsum('l,ilad,ld->ia',e_b[:nocc_b],t2_2_ab,t1_2_b)
        
        t1_3_a += 0.5*np.einsum('a,ilad,ld->ia',e_a[nocc_a:],t2_2_a,t1_2_a)
        t1_3_a += 0.5*np.einsum('a,ilad,ld->ia',e_a[nocc_a:],t2_2_ab,t1_2_b)
        
        t1_3_a -= 0.5*np.einsum('i,ilad,ld->ia',e_a[:nocc_a],t2_2_a,t1_2_a)
        t1_3_a -= 0.5*np.einsum('i,ilad,ld->ia',e_a[:nocc_a],t2_2_ab,t1_2_b)
        
        t1_3_a += np.einsum('ld,adil->ia',t1_2_a,v2e_vvoo_a)
        t1_3_a += np.einsum('ld,adil->ia',t1_2_b,v2e_vvoo_ab)
        
        t1_3_a += np.einsum('ld,alid->ia',t1_2_a,v2e_voov_a)
        t1_3_a += np.einsum('ld,alid->ia',t1_2_b,v2e_voov_ab)

        t1_3_a -= 0.5*np.einsum('lmad,lmid->ia',t2_2_a,v2e_ooov_a)
        t1_3_a -= np.einsum('lmad,lmid->ia',t2_2_ab,v2e_ooov_ab)
        
        t1_3_a += 0.5*np.einsum('ilde,alde->ia',t2_2_a,v2e_vovv_a)
        t1_3_a += np.einsum('ilde,alde->ia',t2_2_ab,v2e_vovv_ab)
        
        t1_3_b = np.einsum('d,ilad,ld->ia',e_b[nocc_b:],t2_2_b,t1_2_b)
        t1_3_b += np.einsum('d,ilad,ld->ia',e_a[nocc_a:],t2_2_ab,t1_2_a)
        
        t1_3_b -= np.einsum('l,ilad,ld->ia',e_b[:nocc_b],t2_2_b,t1_2_b)
        t1_3_b -= np.einsum('l,ilad,ld->ia',e_a[:nocc_a],t2_2_ab,t1_2_a)
        
        t1_3_b += 0.5*np.einsum('a,ilad,ld->ia',e_b[nocc_b:],t2_2_b,t1_2_b)
        t1_3_b += 0.5*np.einsum('a,ilad,ld->ia',e_b[nocc_b:],t2_2_ab,t1_2_a)
        
        t1_3_b -= 0.5*np.einsum('i,ilad,ld->ia',e_b[:nocc_b],t2_2_b,t1_2_b)
        t1_3_b -= 0.5*np.einsum('i,ilad,ld->ia',e_b[:nocc_b],t2_2_ab,t1_2_a)
        
        t1_3_b += np.einsum('ld,adil->ia',t1_2_b,v2e_vvoo_b)
        t1_3_b += np.einsum('ld,adil->ia',t1_2_a,v2e_vvoo_ab)
        
        t1_3_b += np.einsum('ld,alid->ia',t1_2_b,v2e_voov_b)
        t1_3_b += np.einsum('ld,alid->ia',t1_2_a,v2e_voov_ab)

        t1_3_b -= 0.5*np.einsum('lmad,lmid->ia',t2_2_b,v2e_ooov_b)
        t1_3_b -= np.einsum('lmad,lmid->ia',t2_2_ab,v2e_ooov_ab)
        
        t1_3_b += 0.5*np.einsum('ilde,alde->ia',t2_2_b,v2e_vovv_b)
        t1_3_b += np.einsum('ilde,alde->ia',t2_2_ab,v2e_vovv_ab)
        
        t1_3_a = t1_3_a/D1_a
        t1_3_b = t1_3_b/D1_b
    
    
        t1_3 = (t1_3_a , t1_3_b)    


    t_amp = (t2_1, t2_2, t1_2, t1_3)

    return t_amp

def compute_mp2_energy(direct_adc, t_amp):

    nocc_so = direct_adc.nocc_so
    nvir_so = direct_adc.nvir_so
    v2e_so_oovv = direct_adc.v2e_so[:nocc_so,:nocc_so,nocc_so:,nocc_so:]
    t2_1 = t_amp[0]
    
    e_mp2 = 0.25 * np.einsum('ijab,ijab', t2_1, v2e_so_oovv)

    return e_mp2


def calc_density_of_states(direct_adc,t_amp):

	nmo_so = direct_adc.nmo_so
	freq_range = direct_adc.freq_range	
	broadening = direct_adc.broadening
	step = direct_adc.step

	freq_range = np.arange(freq_range[0],freq_range[1],step)


	k = np.zeros((nmo_so,nmo_so))
	gf = np.array(k,dtype = complex)
	gf.imag = k

	gf_trace= []
	gf_im_trace = [] 

	for freq in freq_range:
       
		omega = freq
		iomega = freq + broadening*1j


		for orb in range(nmo_so):

			T = calculate_T(direct_adc, t_amp, orb)
			apply_H = define_H(direct_adc, t_amp, omega)
			gf[orb,orb] = calculate_GF(direct_adc,apply_H,omega,orb,T)

		gf_trace = -(1/(np.pi))*np.trace(gf.imag)
		gf_im_trace.append(gf_trace)
        

	return gf_im_trace         


def calculate_T(direct_adc, t_amp, orb):

    method = direct_adc.method

    t2_1, t2_2, t1_2, t1_3 = t_amp

    nocc_so = direct_adc.nocc_so
    nvir_so = direct_adc.nvir_so
    ij_ind = np.tril_indices(nocc_so, k=-1)

    n_singles = nocc_so
    n_doubles = nocc_so * (nocc_so - 1) * nvir_so // 2
    dim = n_singles+n_doubles

    idn_occ = np.identity(nocc_so)
    idn_vir = np.identity(nvir_so)
    
    v2e_so_oovv = direct_adc.v2e_so[:nocc_so, :nocc_so, nocc_so:, nocc_so:]
    v2e_so_vvvo = direct_adc.v2e_so[nocc_so:, nocc_so:, nocc_so:, :nocc_so]
    v2e_so_ovoo = direct_adc.v2e_so[:nocc_so, nocc_so:, :nocc_so:,:nocc_so]
    v2e_so_voov = direct_adc.v2e_so[nocc_so:, :nocc_so, :nocc_so, nocc_so:]
    v2e_so_ovov = direct_adc.v2e_so[:nocc_so, nocc_so:, :nocc_so, nocc_so:]
    v2e_so_vovv = direct_adc.v2e_so[nocc_so:, :nocc_so, nocc_so:, nocc_so:]
    v2e_so_ooov = direct_adc.v2e_so[:nocc_so, :nocc_so, :nocc_so, nocc_so:]
    
    T = np.zeros((dim))
    T1 = T[:n_singles]
    T2 = T[n_singles:] 

    ij_ind = np.tril_indices(nocc_so,k=-1)
    
    t2_1_t = t2_1[ij_ind[0],ij_ind[1],:,:].copy()
    
    #ADC(2) 1h part
   
    if orb < nocc_so:
        
        T1 = idn_occ[orb, :]
        T1 += 0.25*np.einsum('kdc,ikdc->i',t2_1[:,orb,:,:], t2_1,optimize = True)
    
    else :
        
        T1 += t1_2[:,(orb-nocc_so)]

        T2 = t2_1_t[:,:,(orb-nocc_so)].T.reshape(-1)
         
       
        

     
    if(method=='adc(2)-e'):
      
        
        t2_2_t = t2_2[ij_ind[0],ij_ind[1],:,:].copy()
    
    #ADC(3) 2h-1p part 
        
        if orb >= nocc_so:
    
            T2 += t2_2_t[:,:,(orb-nocc_so)].T.reshape(-1)
    



    if(method=='adc3'):
    	
        t2_2_t = t2_2[ij_ind[0],ij_ind[1],:,:].copy()
    
    #ADC(3) 1h part 
        
        if orb < nocc_so:
            T1 += 0.25*np.einsum('kdc,ikdc->i',t2_1[:,orb,:,:], t2_2, optimize = True) 
            T1 += 0.25*np.einsum('ikdc,kdc->i',t2_1, t2_2[:,orb,:,:],optimize = True) 
 
        else: 
    
            T1 += 0.5*np.einsum('ikc,kc->i',t2_1[:,:,(orb-nocc_so),:], t1_2,optimize = True)
            T1 += t1_3[:,(orb-nocc_so)]

    #ADC(3) 2h-1p part 
            
            T2 += t2_2_t[:,:,(orb-nocc_so)].T.reshape(-1)

    T = np.concatenate((T1,T2))

    return T







def define_H(direct_adc,t_amp,omega):

    method = direct_adc.method

    iomega = omega + direct_adc.broadening*1j

    t2_1, t2_2, t1_2, t1_3 = t_amp

    nocc_so = direct_adc.nocc_so
    nvir_so = direct_adc.nvir_so
    ij_ind = np.tril_indices(nocc_so, k=-1)

    n_singles = nocc_so
    n_doubles = nocc_so * (nocc_so - 1) * nvir_so // 2

    e_occ_so = direct_adc.mo_energy_so[:nocc_so]
    e_vir_so = direct_adc.mo_energy_so[nocc_so:]

    idn_occ = np.identity(nocc_so)
    idn_vir = np.identity(nvir_so)

    v2e_so_oovv = direct_adc.v2e_so[:nocc_so,:nocc_so,nocc_so:,nocc_so:]
    v2e_so_vooo = direct_adc.v2e_so[nocc_so:,:nocc_so,:nocc_so,:nocc_so]
    v2e_so_oovo = direct_adc.v2e_so[:nocc_so,:nocc_so,nocc_so:,:nocc_so]
    v2e_so_vvoo = direct_adc.v2e_so[nocc_so:,nocc_so:,:nocc_so,:nocc_so]
    v2e_so_ooov = direct_adc.v2e_so[:nocc_so,:nocc_so,:nocc_so,nocc_so:]
    v2e_so_ovoo = direct_adc.v2e_so[:nocc_so,nocc_so:,:nocc_so,:nocc_so]
    v2e_so_vovv = direct_adc.v2e_so[nocc_so:,:nocc_so,nocc_so:,nocc_so:]
    v2e_so_vovo = direct_adc.v2e_so[nocc_so:,:nocc_so,nocc_so:,:nocc_so]
    v2e_so_oooo = direct_adc.v2e_so[:nocc_so,:nocc_so,:nocc_so,:nocc_so]
    v2e_so_vvvo = direct_adc.v2e_so[nocc_so:,nocc_so:,nocc_so:,:nocc_so]

    v2e_vooo_1 = v2e_so_vooo[:,:,ij_ind[0],ij_ind[1]].transpose(1,0,2).reshape(nocc_so, -1)
    v2e_oovo_1 = v2e_so_oovo[ij_ind[0],ij_ind[1],:,:].transpose(1,0,2)

    d_ij = e_occ_so[:,None] + e_occ_so
    d_a = e_vir_so[:,None]
    D_n = -d_a + d_ij.reshape(-1)
    D_n = D_n.reshape((nvir_so,nocc_so,nocc_so))
    D_aij = D_n.copy()[:,ij_ind[0],ij_ind[1]].reshape(-1)

    def sigma_(r):
        r1 = r[:n_singles]
        r2 = r[n_singles:]

        # ADC(2) ij block
        s1 = np.einsum('i,ij,j->i', e_occ_so, idn_occ, r1, optimize = True)
        s1 += np.einsum('d,ilde,jlde,j->i', e_vir_so, t2_1, t2_1, r1, optimize=True)
        s1 -= 0.5 *  np.einsum('l,ilde,jlde,j->i', e_occ_so, t2_1, t2_1, r1,optimize = True)
        s1 -= 0.25 *  np.einsum('i,ilde,jlde,j->i', e_occ_so, t2_1, t2_1, r1, optimize = True)
        s1 -= 0.25 *  np.einsum('j,ilde,jlde,j->i', e_occ_so, t2_1, t2_1, r1, optimize = True)
        s1 += 0.5 *  np.einsum('ilde,jlde,j->i', t2_1, v2e_so_oovv, r1, optimize = True)
        s1 += 0.5 *  np.einsum('jlde,ilde,j->i', t2_1, v2e_so_oovv, r1, optimize = True)

        # ADC(2) i - kja block
        s1 += np.einsum('jp,p->j', v2e_vooo_1, r2, optimize = True)

        # ADC(2) ajk - i block
        s2 = np.einsum('api,i->ap', v2e_oovo_1, r1, optimize = True).reshape(-1)
        
        # ADC(2) ajk - bil block

        s2 += D_aij * r2

        if (method == "adc(2)-e"):
        	
                #print("Calculating additional terms for adc(2)-e")	
        
                temp = np.einsum('ab,xywv->axybvw',idn_vir,v2e_so_oooo,optimize = True)
                
                temp_1 = -np.einsum('wx,byav->axybvw',idn_occ, v2e_so_vovo, optimize = True)
                temp_1 -= temp_1.transpose(0,2,1,3,4,5).copy()
                
                temp_2 = np.einsum('vx,byaw->axybvw',idn_occ, v2e_so_vovo, optimize=True)
                temp_2 -= temp_2.transpose(0,2,1,3,4,5).copy()

                temp += temp_1+temp_2

                temp = temp[:,ij_ind[0],ij_ind[1],:,:,:]
                temp = temp[:,:,:,ij_ind[0],ij_ind[1]].reshape(n_doubles,n_doubles)
                

                s2  += np.einsum('pq,q->p',temp, r2, optimize = True)

        if (method == "adc(3)"):
        	
                #print("Calculating additional terms for adc(3)")	
                 
                # ADC(3) ij block
                
                s1 += np.einsum('ld,jlid,j->i',t1_2,v2e_so_ooov,r1,optimize = True)
                s1 += np.einsum('ld,jdil,j->i',t1_2,v2e_so_ovoo,r1,optimize = True)
                s1 += 0.5* np.einsum('ilde,jlde,j->i',t2_2, v2e_so_oovv, r1 ,optimize = True)
                s1 += 0.5* np.einsum('jlde,deil,j->i',t2_2, v2e_so_vvoo, r1 ,optimize = True)
                s1 += np.einsum('d,ilde,jlde,j->i',e_vir_so, t2_1, t2_2, r1, optimize = True)
                s1 += np.einsum('d,jlde,ilde,j->i',e_vir_so, t2_1, t2_2, r1, optimize = True)
                s1 -= 0.5*np.einsum('l,ilde,jlde,j->i',e_occ_so, t2_1, t2_2, r1,optimize = True)
                s1 -= 0.5*np.einsum('l,jlde,ilde,j->i',e_occ_so, t2_1, t2_2, r1, optimize = True)
                s1 -= 0.25*np.einsum('i,ilde,jlde,j->i',e_occ_so, t2_1, t2_2, r1, optimize = True)
                s1 -= 0.25*np.einsum('i,jlde,ilde,j->i',e_occ_so, t2_1, t2_2, r1, optimize = True)
                s1 -= 0.25*np.einsum('j,jlde,ilde,j->i',e_occ_so, t2_1, t2_2, r1, optimize = True)
                s1 -= 0.25*np.einsum('j,ilde,jlde,j->i',e_occ_so, t2_1, t2_2, r1, optimize = True)

               
                # ADC(3) i - kja block




                temp = 0.5*np.einsum('vwde,bjde->jbvw',t2_1,v2e_so_vovv)
                temp = temp[:,:,ij_ind[0],ij_ind[1]].reshape(nocc_so,-1)
                
                temp_1 = np.einsum('vlbd,jlwd->jbvw',t2_1,v2e_so_ooov)
                temp_2 = temp_1.transpose(0,1,3,2).copy()    

                temp_1 = temp_1[:,:,ij_ind[0],ij_ind[1]].reshape(nocc_so,-1)
                temp_2 = temp_2[:,:,ij_ind[0],ij_ind[1]].reshape(nocc_so,-1)


                s1 += np.einsum('jp,p->j',temp, r2, optimize=True)
                s1 += np.einsum('jp,p->j',temp_1, r2, optimize=True)
                s1 -= np.einsum('jp,p->j',temp_2, r2, optimize=True)


                # ADC(3) ajk - i block
                
                temp =  0.5*np.einsum('xyde,deai->axyi',t2_1, v2e_so_vvvo)
                temp = temp[:,ij_ind[0],ij_ind[1],:]
                
                temp_1 = np.einsum('xlad,ydil->axyi',t2_1, v2e_so_ovoo)
                temp_2 = temp_1.transpose(0,2,1,3).copy()
                
                temp_1 = temp_1[:,ij_ind[0],ij_ind[1],:]
                temp_2 = temp_2[:,ij_ind[0],ij_ind[1],:]

                s2 += np.einsum('api,i->ap',temp, r1 ,optimize = True).reshape(-1)
                s2 += np.einsum('api,i->ap',temp_1, r1 ,optimize = True).reshape(-1)
                s2 -= np.einsum('api,i->ap',temp_2, r1 ,optimize = True).reshape(-1)
        
        

                # ADC(3) ajk - bil block

                temp = np.einsum('ab,xywv->axybvw',idn_vir, v2e_so_oooo, optimize =True)
                

                temp_1 = -np.einsum('wx,byav->axybvw',idn_occ, v2e_so_vovo, optimize = True)
                temp_1 -= temp_1.transpose(0,2,1,3,4,5).copy()
                
                temp_2 = np.einsum('vx,byaw->axybvw',idn_occ, v2e_so_vovo, optimize=True)
                temp_2 -= temp_2.transpose(0,2,1,3,4,5).copy()

                temp += temp_1+temp_2

                temp = temp[:,ij_ind[0],ij_ind[1],:,:,:]
                temp = temp[:,:,:,ij_ind[0],ij_ind[1]].reshape(n_doubles,n_doubles)
                

                s2  += np.einsum('pq,q->p',temp, r2, optimize = True)

        s = np.concatenate((s1,s2))
        omega_s = iomega*r - s
                
        return omega_s

    return sigma_



def calculate_GF(direct_adc,apply_H,omega,orb,T):


    broadening = direct_adc.broadening
    nocc_so = direct_adc.nocc_so
    nvir_so = direct_adc.nvir_so

    iomega = omega + broadening*1j
    
    imag_r = -(np.real(T))/broadening


    sigma = iomega*imag_r - apply_H(imag_r) 
    
    real_r =  (-omega*imag_r  + np.real(sigma))/broadening

    n_singles = nocc_so
    n_doubles = nocc_so * (nocc_so - 1) * nvir_so//2


    dim = n_singles + n_doubles


    z = np.zeros((dim))
    new_r = np.array(z,dtype = complex)
    new_r.imag = z

    new_r.real = real_r.copy()
    new_r.imag = imag_r.copy()

    new_r = solve_conjugate_gradients(direct_adc,apply_H,T,new_r,omega)

    gf = np.dot(T,new_r)

    return gf




def solve_conjugate_gradients(direct_adc,apply_H,T,r,omega):
    
    maxiter = direct_adc.maxiter

    iomega = omega + direct_adc.broadening*1j
    
    # Compute residual
    
    res = T - apply_H(r)

    rms = np.linalg.norm(res)/np.sqrt(res.size)

    if rms < 1e-8:
        return r

    d = res

    delta_new = np.dot(np.ravel(res), np.ravel(res))

    conv = False

    for imacro in range(maxiter):

        
        Ad = apply_H(d)

        # q = A * d
        q = Ad

        # alpha = delta_new / d . q
        alpha = delta_new / (np.dot(np.ravel(d), np.ravel(q)))

        # x = x + alpha * d
        r = r + alpha * d
 
        res = res - alpha * q 

        delta_old = delta_new
        delta_new = np.dot(np.ravel(res), np.ravel(res))

        beta = delta_new/delta_old

        d = res + beta * d

        # Compute RMS of the residual
        rms = np.linalg.norm(res)/np.sqrt(res.size)
        
        print ("freq","   ",iomega,"   ","Iteration ", imacro, ": RMS = %8.4e" % rms)

        if abs(rms) < direct_adc.tol:
            conv = True
            break

    if conv:
        print ("Iterations converged")
    else:
        raise Exception("Iterations did not converge")

    return r
