# H₂ Reform Lab — Streamlit PoC

Prueba de concepto interactiva para estudiar reformado de metano y producción de hidrógeno por **SMR**, **DRM** y **POX**. La aplicación combina un núcleo de equilibrio termodinámico reproducible, métricas técnico-ambientales, análisis de sensibilidad, carga de datos CSV/Aspen y exportación auditada.

## Qué demuestra

- Minimización de energía libre de Gibbs con restricciones de balance C/H/O.
- Propiedades de seis especies gaseosas mediante coeficientes de Shomate de NIST.
- Efectos de temperatura, presión y relación de alimentación.
- Conversión de CH₄, rendimiento de H₂, eficiencia LHV, carga térmica e intensidad potencial de CO₂e.
- Comparación contra datos experimentales o sensibilidad de Aspen mediante CSV.
- Exportación de resultados a CSV y paquete XLSX con entradas, supuestos y referencias.
- Hoja de ruta de cuatro fases para llevar el PoC a un estudio publicable.

## Ejecutar

```bash
cd h2_reform_poc
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

La configuración incluida escucha en `0.0.0.0`.

## Pruebas

```bash
pip install pytest
pytest -q
```

## Estructura

```text
h2_reform_poc/
├── app.py                       # interfaz y reporting
├── core/
│   ├── thermodynamics.py        # Shomate + Gibbs + balances
│   └── metrics.py               # KPIs técnico-ambientales
├── data/
│   ├── literature_matrix.csv    # referencias iniciales
│   └── demo_experimental.csv    # plantilla de validación
├── tests/
│   └── test_thermodynamics.py
├── .streamlit/config.toml
└── requirements.txt
```

## Modelo

Se resuelve:

\[
\min_{n_i} G = \sum_i n_i\left[g_i^\circ(T) + RT\ln(y_iP/P^\circ)\right]
\]

sujeto a conservación elemental y no negatividad. La base es 1 mol de CH₄. Las especies son CH₄, H₂O, CO, CO₂, H₂ y O₂.

### Definiciones clave

- **Eficiencia LHV:** LHV del H₂ recuperado / (LHV de CH₄ + calor endotérmico de reacción corregido por 90% de eficiencia del calentador).
- **Demanda térmica:** solo ΔH de reacción con alimentación y salida a la misma temperatura; no incluye precalentamiento ni vaporización.
- **Intensidad potencial:** carbono convertido como CO + CO₂ expresado como CO₂ aguas abajo, menos captura conceptual, más emisiones de la fuente de calor.
- **Recuperación H₂ y captura:** entradas de escenario, no predicciones del equilibrio.

## Límites importantes

Este repositorio es un **screening**, no una herramienta de diseño:

- Gas ideal, reactor isotérmico, equilibrio químico, sin caída de presión.
- No incluye cinética, tamaño de reactor, catalizador, transferencia, inertes, compresión o PSA detallada.
- No incluye C(s); por tanto **no predice coque**.
- La intensidad de carbono no es un ACV completo.
- Todo resultado debe validarse contra datos trazables o un simulador de proceso antes de usarse en ingeniería o publicación.

## Extensión recomendada

1. Curar matriz de literatura con DOI, catalizador, incertidumbre y dominio de operación.
2. Integrar Xu–Froment en un PFR con balances de energía y presión.
3. Añadir carbono sólido, criterios de deposición y no idealidad/fugacidad.
4. Validar contra experimentos/Aspen y añadir análisis de incertidumbre.
5. Preparar figuras/tablas versionadas para manuscrito o informe.
