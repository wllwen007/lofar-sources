#!/usr/bin/python

'''
get_intersecting_sources
find which sources in a catalogue intersect, enclose or are enclosed by another source...
'''

from lofar_source_sorter import Mask, Masks_disjoint_complete
import numpy as np
from matplotlib import patches
from astropy.table import Table
import astropy.coordinates as ac
import astropy.units as u
import os


path = '/local/wwilliams/projects/radio_imaging/lofar_surveys/LoTSS-DR1-July21-2017/'
lofarcat_file_srt = path+'LOFAR_HBA_T1_DR1_catalog_v0.9.srl.sorted.fits'






lofarcat = Table.read(lofarcat_file_srt)


## get 2MASX information (from 'fixed' catalgoue)
xsc_file = path+'2MASX_hetdex_fix.fits'
xsc = Table.read(xsc_file)

c = ac.SkyCoord(lofarcat['RA'], lofarcat['DEC'], unit="deg")
cxsc = ac.SkyCoord(xsc['ra'], xsc['dec'], unit="deg")
f_nn_idx,f_nn_sep2d,f_nn_dist3d = ac.match_coordinates_sky(c,cxsc,nthneighbor=1)

xsc_nn = xsc[f_nn_idx]




def accept_match_2mass(mask, lcat, xcat, plot=False, selname=None):

    
    if plot:
        f,ax = pp.paper_single_ax()
    if selname is not None:
        nn = lcat['Source_Name']==selname
        mask = mask & nn
        
    idx = np.arange(len(lcat))
    iinds = idx[mask]
    inellipse = np.zeros(len(lcat ), dtype=bool)
    for i in iinds:
        
        tl = lcat[i]
        tx = xcat[i]
            
        # assumning flat sky here...
        g_ell_center = (tx['ra'], tx['dec'])
        r_a = (tx['r_ext']+ tl['Maj'] )  / 3600. #to deg
        r_b = r_a*tx['k_ba']
        angle = 90.-tx['k_phi']  #(anticlockwise from x-axis)
        rangle = angle *np.pi/180.

        cos_angle = np.cos(np.radians(180.-angle))
        sin_angle = np.sin(np.radians(180.-angle))

        xc = tl['RA'] - g_ell_center[0]
        yc = tl['DEC'] - g_ell_center[1]

        xct = xc * cos_angle - yc * sin_angle
        yct = xc * sin_angle + yc * cos_angle 

        rad_cc = (xct/r_a)**2. + (yct/r_b)**2.
        
        if rad_cc <= 1:
            inellipse[i] = 1
            
        if plot:
            g_ellipse = patches.Ellipse(g_ell_center, 2*r_a, 2*r_b, angle=angle, fill=False, ec='green', linewidth=2)

            ax.plot(g_ell_center[0], g_ell_center[1], 'g.')
            ax.plot(tl['RA'], tl['DEC'], 'k.')
            ax.add_patch(g_ellipse)
            
            l_ellipse = patches.Ellipse((tl['RA'], tl['DEC']), 2*tl['Maj']/ 3600., 2*tl['Min']/ 3600., angle=90.-tl['PA'], fill=False, ec='blue', linewidth=2)
            ax.add_patch(l_ellipse)
            
            if rad_cc <= 1:
                ax.plot(tl['RA'], tl['DEC'], 'r+')
            
            mell = g_ellipse.contains_point((tl['RA'], tl['DEC']), radius=tl['Maj']/3600)
            if mell:
                ax.plot(tl['RA'], tl['DEC'], 'gx')
            
            ax.plot(g_ell_center[0], g_ell_center[1], 'g+')
            ax.plot(tl['RA'], tl['DEC'], 'b.')
    if plot:
        ax.set_xlabel('RA')
        ax.set_ylabel('DEC')
        ax.invert_xaxis()
        ax.axis('equal')
        
    return inellipse
        
xmatch0 = f_nn_sep2d.value*u.deg < np.array(xsc_nn['r_ext'])*u.arcsec
xmatch1 = f_nn_sep2d.value*u.deg < np.array(xsc_nn['r_ext'] + lofarcat['Maj'])*u.arcsec

inellipse = accept_match_2mass(xmatch1, lofarcat, xsc_nn)
xmatch = xmatch1 & inellipse

Xhuge =  xmatch & (xsc_nn['r_ext'] >= 240.)
XLarge =  xmatch & (xsc_nn['r_ext'] >= 60.) & (xsc_nn['r_ext'] < 240.)
Xlarge =  xmatch & (xsc_nn['r_ext'] >= 20.) & (xsc_nn['r_ext'] < 60.)
Xsmall =  xmatch0 & (xsc_nn['r_ext'] >= 0.) & (xsc_nn['r_ext'] < 20.)

# add the columns if we've not yet run this script
if '2MASX' not in lofarcat.colnames:
    lofarcat.add_column(Column(np.zeros(len(lofarcat),dtype=bool),'2MASX'))
    lofarcat.add_column(Column(np.zeros(len(lofarcat),dtype='S20'),'2MASX_name'))
    lofarcat.add_column(Column(np.zeros(len(lofarcat),dtype=float),'2MASX_ra'))
    lofarcat.add_column(Column(np.zeros(len(lofarcat),dtype=float),'2MASX_dec'))
    lofarcat.add_column(Column(np.zeros(len(lofarcat),dtype=float),'2MASX_size'))
    lofarcat.add_column(Column(np.zeros(len(lofarcat),dtype=bool),'2MASX_match_large'))
    lofarcat.add_column(Column(np.zeros(len(lofarcat),dtype=bool),'2MASX_match'))
    
for m in [Xhuge, XLarge, Xlarge, Xsmall]:
    lofarcat['2MASX'][m]  = m[m]
    lofarcat['2MASX_name'][m]  = xsc_nn['designation'][m]
    lofarcat['2MASX_ra'][m]  = xsc_nn['ra'][m]
    lofarcat['2MASX_dec'][m]  = xsc_nn['dec'][m]
    lofarcat['2MASX_size'][m]  = xsc_nn['r_ext'][m]
    
    
lofarcat['2MASX_match_large'] = XLarge|Xhuge
lofarcat['2MASX_match'] = Xlarge|Xsmall




#t=M_all.submask(huge , '2MASX_huge', '2MASX_huge')
#t.make_sample(lofarcat)
#t=M_all.submask(Large , '2MASX_Large', '2MASX_Large')
#t.make_sample(lofarcat)
#t=M_all.submask(large , '2MASX_large', '2MASX_large')
#t.make_sample(lofarcat)
#t=M_all.submask(small , '2MASX_small', '2MASX_small')
#t.make_sample(lofarcat)

#accept_match_2mass(xmatch1, lofarcat, xsc_nn, selname='ILTJ113935.922+555529.21', plot=True)


## write output file

if os.path.exists(lofarcat_file_srt):
    os.remove(lofarcat_file_srt)
lofarcat.write(lofarcat_file_srt)
