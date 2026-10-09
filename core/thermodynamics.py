"""Núcleo termodinámico para el PoC de reformado de metano.

El modelo minimiza la energía libre de Gibbs de una mezcla gaseosa ideal sujeta a
balances elementales de C, H y O. Los coeficientes de Shomate provienen de NIST
Chemistry WebBook (SRD 69). El modelo es deliberadamente transparente y no
sustituye una simulación de diseño en Aspen Plus/Cantera.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, Mapping

import numpy as np
import pandas as pd
from scipy.optimize import minimize

R_KJ = 8.314462618e-3  # kJ mol-1 K-1
P_STD_BAR = 1.0
SPECIES = ("CH4", "H2O", "CO", "CO2", "H2", "O2")

# Matriz elemental: filas C/H/O; columnas según SPECIES.
ELEMENT_MATRIX = np.array(
    [
        [1.0, 0.0, 1.0, 1.0, 0.0, 0.0],
        [4.0, 2.0, 0.0, 0.0, 2.0, 0.0],
        [0.0, 1.0, 1.0, 2.0, 0.0, 2.0],
    ]
)

# Reacciones independientes usadas únicamente para construir puntos iniciales
# factibles: SMR, WGS y combustión completa.
REACTION_MATRIX = np.array(
    [
        [-1.0, 0.0, -1.0],  # CH4
        [-1.0, -1.0, 2.0],  # H2O
        [1.0, -1.0, 0.0],   # CO
        [0.0, 1.0, 1.0],    # CO2
        [3.0, 1.0, 0.0],    # H2
        [0.0, 0.0, -2.0],   # O2
    ]
)

# (Tmin K, Tmax K, A, B, C, D, E, F, G, H)
# Shomate: Cp [J/mol/K], H-H298 [kJ/mol], S [J/mol/K].
SHOMATE: Dict[str, tuple] = {
    "CH4": (
        (298.0, 1300.0, -0.703029, 108.4773, -42.52157, 5.862788, 0.678565, -76.84376, 158.7163, -74.87310),
        (1300.0, 6000.0, 85.81217, 11.26467, -2.114146, 0.138190, -26.42221, -153.5327, 224.4143, -74.87310),
    ),
    "H2O": (
        (500.0, 1700.0, 30.09200, 6.832514, 6.793435, -2.534480, 0.082139, -250.8810, 223.3967, -241.8264),
        (1700.0, 6000.0, 41.96426, 8.622053, -1.499780, 0.098119, -11.15764, -272.1797, 219.7809, -241.8264),
    ),
    "CO": (
        (298.0, 1300.0, 25.56759, 6.096130, 4.054656, -2.671301, 0.131021, -118.0089, 227.3665, -110.5271),
        (1300.0, 6000.0, 35.15070, 1.300095, -0.205921, 0.013550, -3.282780, -127.8375, 231.7120, -110.5271),
    ),
    "CO2": (
        (298.0, 1200.0, 24.99735, 55.18696, -33.69137, 7.948387, -0.136638, -403.6075, 228.2431, -393.5224),
        (1200.0, 6000.0, 58.16639, 2.720074, -0.492289, 0.038844, -6.447293, -425.9186, 263.6125, -393.5224),
    ),
    "H2": (
        (298.0, 1000.0, 33.066178, -11.363417, 11.432816, -2.772874, -0.158558, -9.980797, 172.707974, 0.0),
        (1000.0, 2500.0, 18.563083, 12.257357, -2.859786, 0.268238, 1.977990, -1.147438, 156.288133, 0.0),
    ),
    "O2": (
        (100.0, 700.0, 31.32234, -20.23531, 57.86644, -36.50624, -0.007374, -8.903471, 246.7945, 0.0),
        (700.0, 2000.0, 30.03235, 8.772972, -3.988133, 0.788313, -0.741599, -11.32468, 236.1663, 0.0),
    ),
}

ROUTE_META = {
    "SMR": {
        "name": "Reformado con vapor",
        "reaction": "CH₄ + H₂O ⇌ CO + 3H₂",
        "ratio_label": "Relación vapor/carbono (S/C)",
        "ratio_short": "S/C",
        "ratio_range": (1.0, 5.0),
        "ratio_default": 3.0,
        "ratio_step": 0.25,
        "accent": "#2EE6A6",
        "description": "Ruta endotérmica de referencia para maximizar H₂; se acopla con la reacción WGS.",
    },
    "DRM": {
        "name": "Reformado seco",
        "reaction": "CH₄ + CO₂ ⇌ 2CO + 2H₂",
        "ratio_label": "Relación CO₂/CH₄",
        "ratio_short": "CO₂/C",
        "ratio_range": (0.5, 3.0),
        "ratio_default": 1.0,
        "ratio_step": 0.1,
        "accent": "#56B4FF",
        "description": "Valoriza CO₂ y produce syngas; requiere evaluar coque y destino del CO por separado.",
    },
    "POX": {
        "name": "Oxidación parcial",
        "reaction": "CH₄ + ½O₂ → CO + 2H₂",
        "ratio_label": "Relación O₂/CH₄",
        "ratio_short": "O₂/C",
        "ratio_range": (0.2, 1.0),
        "ratio_default": 0.5,
        "ratio_step": 0.05,
        "accent": "#FFB86B",
        "description": "Ruta compacta y exotérmica; el PoC asume alimentación de O₂ puro, sin N₂ inerte.",
    },
}


@dataclass(frozen=True)
class EquilibriumResult:
    route: str
    temperature_c: float
    pressure_bar: float
    ratio: float
    feed: np.ndarray
    outlet: np.ndarray
    success: bool
    message: str
    objective: float
    atom_residual: float

    @property
    def total_moles(self) -> float:
        return float(np.sum(self.outlet))

    @property
    def mole_fractions(self) -> np.ndarray:
        total = self.total_moles
        return self.outlet / total if total > 0 else np.zeros_like(self.outlet)

    def composition_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Especie": SPECIES,
                "Alimentación (mol)": self.feed,
                "Salida equilibrio (mol)": self.outlet,
                "Fracción molar salida": self.mole_fractions,
            }
        )


def build_feed(route: str, ratio: float) -> np.ndarray:
    """Base de cálculo: 1 mol de CH4 alimentado."""
    if route not in ROUTE_META:
        raise ValueError(f"Ruta no reconocida: {route}")
    feed = np.zeros(len(SPECIES), dtype=float)
    feed[0] = 1.0
    if route == "SMR":
        feed[1] = ratio
    elif route == "DRM":
        feed[3] = ratio
    else:  # POX
        feed[5] = ratio
    return feed


def _coefficients(species: str, temperature_k: float) -> np.ndarray:
    ranges = SHOMATE[species]
    for row in ranges:
        if row[0] <= temperature_k <= row[1]:
            return np.asarray(row[2:], dtype=float)
    # La UI restringe el intervalo a la región validada. Este fallback evita
    # discontinuidades numéricas si se llama la función directamente.
    return np.asarray(ranges[0][2:] if temperature_k < ranges[0][0] else ranges[-1][2:], dtype=float)


def species_enthalpy(species: str, temperature_k: float) -> float:
    """Entalpía molar estándar relativa a elementos a 298 K [kJ/mol]."""
    a, b, c, d, e, f, _g, h = _coefficients(species, temperature_k)
    t = temperature_k / 1000.0
    sensible = a * t + b * t**2 / 2 + c * t**3 / 3 + d * t**4 / 4 - e / t + f - h
    return float(h + sensible)


def species_entropy(species: str, temperature_k: float) -> float:
    """Entropía molar estándar [kJ/mol/K]."""
    a, b, c, d, e, _f, g, _h = _coefficients(species, temperature_k)
    t = temperature_k / 1000.0
    entropy_j = a * np.log(t) + b * t + c * t**2 / 2 + d * t**3 / 3 - e / (2 * t**2) + g
    return float(entropy_j / 1000.0)


def species_gibbs(species: str, temperature_k: float) -> float:
    return species_enthalpy(species, temperature_k) - temperature_k * species_entropy(species, temperature_k)


def _initial_guess(route: str, feed: np.ndarray, ratio: float) -> np.ndarray:
    """Construye un vector de moles factible para estabilizar SLSQP."""
    if route == "SMR":
        xi_smr = min(0.55, max(0.15, 0.35 * ratio))
        xi_wgs = min(0.15, 0.25 * xi_smr)
        extents = np.array([xi_smr, xi_wgs, 0.0])
    elif route == "DRM":
        progress = min(0.55, 0.55 * ratio)
        # DRM = SMR - WGS
        extents = np.array([progress, -progress, 0.0])
    else:
        progress = min(0.70, 1.35 * ratio)
        # POX = 0.75 SMR - 0.25 WGS + 0.25 combustión
        extents = np.array([0.75 * progress, -0.25 * progress, 0.25 * progress])
    guess = feed + REACTION_MATRIX @ extents
    return np.maximum(guess, 0.0)


@lru_cache(maxsize=8192)
def solve_equilibrium(route: str, temperature_c: float, pressure_bar: float, ratio: float) -> EquilibriumResult:
    """Minimiza G para una mezcla ideal a T y P constantes.

    Los argumentos se redondean en el llamador cuando se usa un barrido para
    aumentar la tasa de aciertos de la caché.
    """
    if not (400.0 <= temperature_c <= 1100.0):
        raise ValueError("Temperatura fuera del dominio del PoC (400–1100 °C).")
    if not (0.1 <= pressure_bar <= 60.0):
        raise ValueError("Presión fuera del dominio del PoC (0.1–60 bar).")

    feed = build_feed(route, ratio)
    temperature_k = temperature_c + 273.15
    g0 = np.array([species_gibbs(s, temperature_k) for s in SPECIES])
    atom_feed = ELEMENT_MATRIX @ feed

    def objective(moles: np.ndarray) -> float:
        safe = np.clip(moles, 1e-24, None)
        total = float(np.sum(safe))
        y = safe / total
        activity = np.clip(y * pressure_bar / P_STD_BAR, 1e-24, None)
        gibbs = np.sum(safe * (g0 + R_KJ * temperature_k * np.log(activity)))
        return float(gibbs / 1000.0)  # escalado numérico

    constraints = {
        "type": "eq",
        "fun": lambda n: ELEMENT_MATRIX @ n - atom_feed,
        "jac": lambda _n: ELEMENT_MATRIX,
    }
    x0 = _initial_guess(route, feed, ratio)
    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=[(0.0, None)] * len(SPECIES),
        constraints=[constraints],
        options={"ftol": 1e-11, "maxiter": 1000, "disp": False},
    )
    outlet = np.maximum(result.x, 0.0)
    residual = float(np.max(np.abs(ELEMENT_MATRIX @ outlet - atom_feed)))
    success = bool(result.success and residual < 1e-7)

    return EquilibriumResult(
        route=route,
        temperature_c=float(temperature_c),
        pressure_bar=float(pressure_bar),
        ratio=float(ratio),
        feed=feed,
        outlet=outlet,
        success=success,
        message=str(result.message),
        objective=float(result.fun),
        atom_residual=residual,
    )


def reaction_duty_kj_per_mol_ch4(result: EquilibriumResult) -> float:
    """Diferencia de entalpía salida-alimentación a la misma T [kJ/mol CH4]."""
    temperature_k = result.temperature_c + 273.15
    h = np.array([species_enthalpy(s, temperature_k) for s in SPECIES])
    return float(np.dot(result.outlet - result.feed, h) / result.feed[0])


def run_temperature_sweep(
    route: str,
    temperatures_c: Iterable[float],
    pressure_bar: float,
    ratio: float,
    recovery: float,
    capture_rate: float,
    heat_emission_factor: float,
) -> pd.DataFrame:
    """Ejecuta un barrido y agrega métricas de desempeño."""
    from .metrics import calculate_metrics

    records = []
    for temperature_c in temperatures_c:
        result = solve_equilibrium(
            route,
            round(float(temperature_c), 4),
            round(float(pressure_bar), 4),
            round(float(ratio), 4),
        )
        metrics = calculate_metrics(result, recovery, capture_rate, heat_emission_factor)
        records.append(
            {
                "Ruta": route,
                "Temperatura (°C)": float(temperature_c),
                "Presión (bar)": float(pressure_bar),
                "Relación de alimentación": float(ratio),
                **metrics,
                "Convergencia": result.success,
                "Residual atómico": result.atom_residual,
            }
        )
    return pd.DataFrame(records)
