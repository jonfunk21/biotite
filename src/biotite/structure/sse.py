# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

"""
This module allows estimation of secondary structure elements in protein
structures.
"""

__name__ = "biotite.structure"
__author__ = "Patrick Kunzmann"
__all__ = ["annotate_sse"]

import numpy as np
from .celllist import CellList
from .geometry import distance, angle, dihedral
from .filter import filter_amino_acids


_r_helix = (np.deg2rad(89-12), np.deg2rad(89+12))
_a_helix = (np.deg2rad(50-20), np.deg2rad(50+20))
_d2_helix = ((5.5-0.5), (5.5+0.5)) # Not used in the algorithm description
_d3_helix = ((5.3-0.5), (5.3+0.5))
_d4_helix = ((6.4-0.6), (6.4+0.6))

_r_strand = (np.deg2rad(124-14), np.deg2rad(124+14))
_a_strand = (np.deg2rad(-180), np.deg2rad(-125),
             np.deg2rad(145), np.deg2rad(180))
_d2_strand = ((6.7-0.6), (6.7+0.6))
_d3_strand = ((9.9-0.9), (9.9+0.9))
_d4_strand = ((12.4-1.1), (12.4+1.1))


def annotate_sse(atom_array, chain_id=None):
    r"""
    Calculate the secondary structure elements (SSE) of a
    peptide chain based on the `P-SEA` algorithm.
    :footcite:`Labesse1997`
    
    The annotation is based CA coordinates only, specifically
    distances and dihedral angles.
    
    Parameters
    ----------
    atom_array : AtomArray
        The atom array to annotate for.
    chain_id : str, optional
        The atoms belonging to this chain are filtered and annotated.
        DEPRECATED: By now multiple chains can be annotated at once.
        To annotate only a certain chain, filter the `atom_array` before
        giving it as input to this function.

    
    Returns
    -------
    sse : ndarray
        An array containing the secondary structure elements,
        where the index corresponds to the index of the CA-filtered
        `atom_array`. 'a' means :math:`{\alpha}`-helix, 'b' means
        :math:`{\beta}`-strand/sheet, 'c' means coil.
    
    Notes
    -----
    Although this function is based on the original `P-SEA` algorithm,
    there are deviations compared to the official `P-SEA` software in
    some cases.
    Do not rely on getting the exact same results.
    
    References
    ----------

    .. footbibliography::
    
    Examples
    --------
    
    SSE of PDB 1L2Y:
    
    >>> sse = annotate_sse(atom_array, "A")
    >>> print(sse)
    ['c' 'a' 'a' 'a' 'a' 'a' 'a' 'a' 'a' 'c' 'c' 'c' 'c' 'c' 'c' 'c' 'c' 'c'
     'c' 'c']
    
    """
    # Filter all CA atoms in the relevant chain.
    mask = filter_amino_acids(atom_array) & (atom_array.atom_name == "CA")
    if chain_id is not None:
        mask &= atom_array.chain_id == chain_id
    ca_coord = atom_array[mask].coord
    length = len(ca_coord)


    # The distances and angles are not defined for the entire interval,
    # therefore the indices do not have the full range
    # Values that are not defined are NaN
    d2i = np.full(length, np.nan)
    d3i = np.full(length, np.nan)
    d4i = np.full(length, np.nan)
    ri  = np.full(length, np.nan)
    ai  = np.full(length, np.nan)

    d2i[1 : length-1] = distance(ca_coord[0 : length-2], ca_coord[2 : length])
    d3i[1 : length-2] = distance(ca_coord[0 : length-3], ca_coord[3 : length])
    d4i[1 : length-3] = distance(ca_coord[0 : length-4], ca_coord[4 : length])
    ri[1 : length-1]  = angle(
        ca_coord[0 : length-2],
        ca_coord[1 : length-1],
        ca_coord[2 : length]
    )
    ai[1 : length-2] = dihedral(
        ca_coord[0 : length-3],
        ca_coord[1 : length-2],
        ca_coord[2 : length-1],
        ca_coord[3 : length-0]
    )
    
    # Find CA that meet criteria for potential helices and strands
    relaxed_helix = (
        (d3i >= _d3_helix[0]) & (d3i <= _d3_helix[1])
    ) | (
        (ri  >= _r_helix[0] ) & ( ri <=  _r_helix[1])
    )
    strict_helix = (
        (d3i >= _d3_helix[0]) & (d3i <= _d3_helix[1]) &
        (d4i >= _d4_helix[0]) & (d4i <= _d4_helix[1])
    ) | (
        (ri  >= _r_helix[0] ) & ( ri <=  _r_helix[1]) &
        (ai  >= _a_helix[0] ) & ( ai <=  _a_helix[1])
    )

    relaxed_strand = (d3i >= _d3_strand[0]) & (d3i <= _d3_strand[1])
    strict_strand = (
        (d2i >= _d2_strand[0]) & (d2i <= _d2_strand[1]) &
        (d3i >= _d3_strand[0]) & (d3i <= _d3_strand[1]) &
        (d4i >= _d4_strand[0]) & (d4i <= _d4_strand[1])
    ) | (
        (ri  >= _r_strand[0] ) & ( ri <=  _r_strand[1]) &
        (
            # Account for periodic boundary of dihedral angle
            ((ai  >= _a_strand[0] ) & ( ai <=  _a_strand[1])) |
            ((ai  >= _a_strand[2] ) & ( ai <=  _a_strand[3]))
        )
    )


    print("".join(["a" if m else "." for m in strict_helix[:70]]))
    helix_mask = _mask_consecutive(strict_helix, 5)
    print("".join(["a" if m else "." for m in helix_mask[:70]]))
    helix_mask = _extend_region(helix_mask, relaxed_helix)
    print("".join(["a" if m else "." for m in helix_mask[:70]]))
    print()
    
    print("".join(["b" if m else "." for m in strict_strand[:70]]))
    strand_mask = _mask_consecutive(strict_strand, 4)
    short_strand_mask = _mask_regions_with_contacts(
        ca_coord,
        _mask_consecutive(strict_strand, 3),
        min_contacts=5, min_distance=4.2, max_distance=5.2
    )
    print("".join(["b" if m else "." for m in strand_mask[:70]]))
    strand_mask = _extend_region(
        strand_mask | short_strand_mask, relaxed_strand
    )
    print("".join(["b" if m else "." for m in strand_mask[:70]]))

    sse = np.full(length, "c", dtype="U1")
    sse[helix_mask] = "a"
    sse[strand_mask] = "b"

    print()
    return sse
            

def _mask_consecutive(mask, number):
    """
    Find all regions in a mask with `number` consecutive ``True``
    values.
    Return a mask that is ``True`` for all indices in such a region and
    ``False`` otherwise.
    """
    # An element is in a consecutive region,
    # if it and the following `number-1` elements are True
    # The elements `mask[-(number-1):]` cannot have the sufficient count
    # by this definition, as they are at the end of the array
    counts = np.zeros(len(mask) - (number-1), dtype=int)
    for i in range(number):
        counts[mask[i : i + len(counts)]] += 1
    consecutive_seed = (counts == number)
    
    # Not only that element, but also the
    # following `number-1` elements are in a consecutive region
    consecutive_mask = np.zeros(len(mask), dtype=bool)
    for i in range(number):
        consecutive_mask[i : i + len(consecutive_seed)] |= consecutive_seed
    
    return consecutive_mask


def _extend_region(base_condition_mask, extension_condition_mask):
    """
    Extend a ``True`` region in `base_condition_mask` by at maximum of
    one element at each side, if such element fulfills
    `extension_condition_mask.`
    """
    # This mask always marks the start
    # of either a 'True' or 'False' region
    # Prepend absent region to the start to capture the event,
    # that the first element is already the start of a region
    region_change_mask = np.diff(np.append([False], base_condition_mask))
    
    # These masks point to the first `False` element
    # left and right of a 'True' region
    # The left end is the element before the first element of a 'True' region
    left_end_mask = region_change_mask & base_condition_mask
    # Therefore the mask needs to be shifted to the left
    left_end_mask = np.append(left_end_mask[1:], [False])
    # The right end is first element of a 'False' region
    right_end_mask = region_change_mask & ~base_condition_mask

    print("".join(["E" if m else "." for m in (left_end_mask | right_end_mask)[:70]]))
    print("".join(["R" if m else "." for m in extension_condition_mask[:70]]))
    
    # The 'base_condition_mask' gets additional 'True' elements
    # at left or right ends, which meet the extension criterion
    return base_condition_mask | (
        (left_end_mask | right_end_mask) & extension_condition_mask
    )


def _mask_regions_with_contacts(coord, candidate_mask,
                               min_contacts, min_distance, max_distance):
    """
    Mask regions of `candidate_mask` that have at least `min_contacts`
    contacts with `coord` in the range `min_distance` to `max_distance`.
    """
    cell_list = CellList(coord, max_distance)
    # For each candidate position,
    # get all contacts within maximum distance
    all_within_max_dist_indices = cell_list.get_atoms(
        coord[candidate_mask], max_distance
    )
   
    contacts = np.zeros(len(coord), dtype=int)
    for i, atom_index in enumerate(np.where(candidate_mask)[0]):
        within_max_dist_indices = all_within_max_dist_indices[i]
        # Remove padding values
        within_max_dist_indices = within_max_dist_indices[
            within_max_dist_indices != -1
        ]
        # Now count all contacts within maximum distance 
        # that also satisfy the minimum distance
        contacts[atom_index] = np.count_nonzero(
            distance(
                coord[atom_index], coord[within_max_dist_indices]
            ) > min_distance
        )
    #!#
    assert np.all(contacts < 10)
    print("".join([f"{c}" for c in contacts[:70]]))
    #!#
    
    # Count the number of contacts per region
    # These indices mark the start of either a 'True' or 'False' region
    # Prepend absent region to the start to capture the event,
    # that the first element is already the start of a region
    region_change_indices = np.where(
        np.diff(np.append([False], candidate_mask))
    )[0]
    # Add exclusive stop
    region_change_indices = np.append(region_change_indices, [len(coord)])
    output_mask = np.zeros(len(candidate_mask), dtype=bool)
    for i in range(len(region_change_indices) - 1):
        start = region_change_indices[i]
        stop = region_change_indices[i+1]
        total_contacts = np.sum(contacts[start : stop])
        if total_contacts >= min_contacts:
            output_mask[start : stop] = True
    
    return output_mask