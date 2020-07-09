# This file is part of sunflower package. radio
# This module contains core functions.

from sunflower.core.descriptors import PersistentAttribute


def check_obj_integrity(obj):
    """Perfom several checks in order to prevent some runtime errors."""
    
    errors = []

    # 1. If obj has PersistentAttribute attributes, check if this object
    #    has the 'data_type' and 'endpoint' attributes.

    for attr in vars(type(obj)).values():
        if not isinstance(attr, PersistentAttribute):
            continue
        if not hasattr(obj, "endpoint"):
            errors.append(f"Missing 'endpoint' attribute in {obj} which contains PersistentAttribute descriptor.")
        if not hasattr(obj, "data_type"):
            errors.append(f"Missing 'data_type' attribute in {obj} which contains PersistentAttribute descriptor.")

    return errors
