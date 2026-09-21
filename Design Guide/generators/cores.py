# -*- coding: utf-8 -*-
"""Ferrite core candidates, as printed in the manufacturer's datasheet.

Nothing in this file is remembered or estimated.  Every number in CORES is
copied from the TDK Electronics datasheet named beside it, and everything
else here is arithmetic on those numbers and on the design.

The two candidates are the ones the design has to choose between: both
clear the flux requirement, and the choice is made on the winding window,
because a single-stage tank needs a leakage that only a physically
separated winding can give.

    PQ 32/30   core B65879B, coil former B65880E, October 2022
    PQ 40/40   core B65883A, coil former B65884E, October 2022

Window symbols follow the datasheets: A_N is the winding cross-section of
the coil former and l_N its mean turn length.
"""
from math import pi

MU0 = 4e-7 * pi

CORES = {
    'PQ 32/30': dict(
        core='B65879B', former='B65880E',
        le=67.80, Ae=153.8, Amin=127.5, Ve=10440.0, mass=57.4,
        AN=104.0, lN=62.0,
        AL_ungapped=6100.0, material='N95'),        # +30/-20 %
    'PQ 40/40': dict(
        core='B65883A', former='B65884E',
        le=93.0, Ae=189.0, Amin=174.0, Ve=17580.0, mass=90.0,
        AN=309.0, lN=87.0,
        AL_ungapped=5500.0, material='N95'),
}

#  Assumptions, stated here so that they are in one place and can be
#  changed in one place.  Neither is a constant of nature.
J_CU = 4.5          # A/mm^2, natural convection, transformer of this size
K_U = 0.30          # window utilisation with Litz, insulation and margins
B_MAX = 0.20        # T, the flux ceiling this note designs to


def flux(V, Ae_mm2):
    """Peak flux density [mT] on a core of this cross-section.

    B_pk = V_o,eff / (4 f_r N_s A_e) - the secondary volt-seconds, so it
    does not contain N_p.  f_r is carried in kHz.
    """
    return 1e3 * V['Vout'] / (4.0 * V['fr'] * 1e3 * V['Ns'] * Ae_mm2 * 1e-6)


def turns_needed(V, Ae_mm2, bmax=B_MAX):
    """The smallest secondary turn count that keeps B_pk under bmax."""
    return V['Vout'] / (4.0 * V['fr'] * 1e3 * bmax * Ae_mm2 * 1e-6)


def gap(V, Ae_mm2):
    """First-estimate centre-leg gap [mm] for the A_L the design needs.

    Assumes the gap carries the whole reluctance and ignores fringing, so
    the real gap always comes out larger.  It is here to show the order,
    not to be put on a drawing - the drawing carries A_L.
    """
    return 1e3 * MU0 * Ae_mm2 * 1e-6 / (V['AL'] * 1e-9)


def copper(V):
    """-> list of (name, turns, I_rms per unit [A], area per turn [mm^2]).

    Primaries in series, secondaries in parallel: every unit carries the
    WHOLE primary current and its share of the secondary current.
    """
    nx = V['nser']
    return [('primary', V['Np'], V['Iprilc'], V['Iprilc'] / J_CU),
            ('secondary, each half', V['Ns'], V['Idio'] / nx,
             V['Idio'] / nx / J_CU)]


def window(V):
    """-> bare copper area [mm^2] for one unit, counting both halves."""
    rows = copper(V)
    a = rows[0][1] * rows[0][3]              # primary
    a += 2 * rows[1][1] * rows[1][3]         # two secondary halves
    return a
