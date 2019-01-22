# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

__author__ = "Patrick Kunzmann"
__all__ = ["mass"]

import json
from os.path import join, dirname, realpath
from ..atoms import Atom, AtomArray, AtomArrayStack


_info_dir = dirname(realpath(__file__))
# Masses are taken from http://www.sbcs.qmul.ac.uk/iupac/AtWt/ (2018/03/01)
with open(join(_info_dir, "atom_masses.json")) as file:
    _atom_masses = json.load(file)
_res_masses = {}

def mass(item, is_residue=None):
    if isinstance(item, str):
        if is_residue is None:
            result_mass = _atom_masses.get(item.upper())
            if result_mass is None:
                result_mass = _res_masses.get(item.upper())
        elif not is_residue:
            result_mass = _atom_masses.get(item.upper())
        else:
            result_mass = _res_masses.get(item.upper())
    
    elif isinstance(item, Atom):
        result_mass = mass(item.element, is_residue=False)
    elif isinstance(item, AtomArray) or isinstance(item, AtomArrayStack):
        result_mass = sum(
            (mass(element, is_residue=False) for element in item.element)
        )
    
    else:
        raise TypeError(
            f"Cannot calculate mass for {type(item).__name__} objects"
        )
    
    if result_mass is None:
        raise KeyError(f"{item} is not known")
    return result_mass