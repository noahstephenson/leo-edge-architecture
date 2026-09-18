"""Architecture metrics: complexity, coupling, interfaces, SWaP, sensitivity."""

from typing import Dict, List, Tuple


def architecture_complexity(arch: Dict) -> int:
    """Complexity as number of blocks plus interfaces.
    arch: dict with 'blocks' list and 'interfaces' list.
    """
    blocks = arch.get("blocks", [])
    interfaces = arch.get("interfaces", [])
    return len(blocks) + len(interfaces)


def coupling(arch: Dict) -> float:
    """Average interfaces per block. 0 if no blocks."""
    blocks = arch.get("blocks", [])
    interfaces = arch.get("interfaces", [])
    if not blocks:
        return 0.0
    # count distinct blocks involved in interfaces
    involved = set()
    for src, dst in interfaces:
        involved.add(src)
        involved.add(dst)
    # average degree
    total_degree = 0
    for b in blocks:
        # count interfaces where block is src or dst
        degree = sum(1 for s, d in interfaces if s == b or d == b)
        total_degree += degree
    return total_degree / len(blocks)


def interface_count(arch: Dict) -> int:
    """Number of interfaces."""
    return len(arch.get("interfaces", []))


def swap_allocation_per_block(swap: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """Normalize SWaP allocation per block.
    Input: {block: {mass_kg, power_w, volume_l}}
    Returns dict with totals and per-block fractions.
    """
    totals = {"mass_kg": 0.0, "power_w": 0.0, "volume_l": 0.0}
    for b, vals in swap.items():
        totals["mass_kg"] += float(vals.get("mass_kg", 0.0))
        totals["power_w"] += float(vals.get("power_w", 0.0))
        totals["volume_l"] += float(vals.get("volume_l", 0.0))

    result = {}
    for b, vals in swap.items():
        mass = float(vals.get("mass_kg", 0.0))
        power = float(vals.get("power_w", 0.0))
        vol = float(vals.get("volume_l", 0.0))
        result[b] = {
            "mass_kg": mass,
            "power_w": power,
            "volume_l": vol,
            "mass_frac": mass / totals["mass_kg"] if totals["mass_kg"] else 0.0,
            "power_frac": power / totals["power_w"] if totals["power_w"] else 0.0,
            "volume_frac": vol / totals["volume_l"] if totals["volume_l"] else 0.0,
        }
    # add totals entry
    result["_totals"] = totals
    return result


def sweep_processor_power(
    processor_power_values: List[float],
    base_energy_j: float = 1000.0,
    contact_window_s: float = 300.0,
    lead_time_s: float = 0.0,
) -> List[Tuple[float, float, float]]:
    """Sweep processor power and compute contact margin alpha and TFUP.

    Processing time = energy / power.
    Exposed processing time = max(0, processing_time - lead_time).
    Contact margin alpha = 1 - exposed_time / contact_window, clipped to [0,1].
    TFUP approximated as processing_time (first product available after processing).

    Returns list of (power_w, alpha, tfup_s).
    """
    results = []
    for p in processor_power_values:
        if p <= 0:
            processing_time_s = float("inf")
        else:
            processing_time_s = base_energy_j / p
        exposed = max(0.0, processing_time_s - lead_time_s)
        alpha = 1.0 - exposed / contact_window_s
        alpha = max(0.0, min(1.0, alpha))
        tfup_s = processing_time_s
        results.append((float(p), alpha, tfup_s))
    return results
