"""Indicadores de desempeño y ambiente para el PoC."""
from __future__ import annotations

from typing import Dict

import numpy as np

from .thermodynamics import EquilibriumResult, SPECIES, reaction_duty_kj_per_mol_ch4

MW_H2_KG_PER_MOL = 2.01588e-3
MW_CO2_KG_PER_MOL = 44.0095e-3
LHV_H2_KJ_PER_MOL = 241.826
LHV_CH4_KJ_PER_MOL = 802.34
HEATER_EFFICIENCY = 0.90


def calculate_metrics(
    result: EquilibriumResult,
    recovery: float = 0.90,
    capture_rate: float = 0.0,
    heat_emission_factor: float = 0.202,
) -> Dict[str, float]:
    """Calcula KPIs sobre base 1 mol CH4 alimentado.

    recovery y capture_rate se expresan como fracciones 0–1. El indicador de
    carbono es deliberadamente conservador: considera que CO termina convertido
    a CO2 aguas abajo (WGS/oxidación). El factor de calor está en kgCO2e/kWh_th.
    """
    idx = {name: i for i, name in enumerate(SPECIES)}
    feed_ch4 = result.feed[idx["CH4"]]
    out_ch4 = result.outlet[idx["CH4"]]
    h2_gross = result.outlet[idx["H2"]] / feed_ch4
    h2_recovered = h2_gross * recovery
    h2_mass = max(h2_recovered * MW_H2_KG_PER_MOL, 1e-12)

    conversion = np.clip((feed_ch4 - out_ch4) / feed_ch4 * 100.0, 0.0, 100.0)
    duty = reaction_duty_kj_per_mol_ch4(result)
    external_heat = max(duty, 0.0) / HEATER_EFFICIENCY
    efficiency = 100.0 * (h2_recovered * LHV_H2_KJ_PER_MOL) / (
        feed_ch4 * LHV_CH4_KJ_PER_MOL + external_heat
    )

    co = result.outlet[idx["CO"]]
    co2 = result.outlet[idx["CO2"]]
    direct_reactor = co2 * MW_CO2_KG_PER_MOL / h2_mass
    potential_process = (co + co2) * MW_CO2_KG_PER_MOL / h2_mass
    captured = potential_process * capture_rate
    residual_process = potential_process - captured
    heat_emissions = (max(duty, 0.0) / 3600.0) * heat_emission_factor / h2_mass
    carbon_intensity = residual_process + heat_emissions

    dry_total = max(result.total_moles - result.outlet[idx["H2O"]], 1e-12)
    h2_dry_fraction = result.outlet[idx["H2"]] / dry_total * 100.0
    h2_co_ratio = result.outlet[idx["H2"]] / max(co, 1e-12)

    return {
        "Conversión CH4 (%)": float(conversion),
        "Rendimiento H2 bruto (mol/mol CH4)": float(h2_gross),
        "Rendimiento H2 recuperado (mol/mol CH4)": float(h2_recovered),
        "Eficiencia energética LHV (%)": float(np.clip(efficiency, 0.0, 100.0)),
        "Demanda térmica (kJ/mol CH4)": float(duty),
        "Intensidad CO2e potencial (kg/kg H2)": float(carbon_intensity),
        "CO2 directo reactor (kg/kg H2)": float(direct_reactor),
        "CO2 potencial de proceso (kg/kg H2)": float(potential_process),
        "CO2 capturado (kg/kg H2)": float(captured),
        "CO2 asociado al calor (kg/kg H2)": float(heat_emissions),
        "H2 seco a la salida (%)": float(h2_dry_fraction),
        "Relación H2/CO": float(h2_co_ratio),
    }
