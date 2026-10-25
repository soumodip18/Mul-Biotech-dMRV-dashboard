"""Allometric equations as plain Python functions.

Each function is registered under the equation_id used in
factors/biomass_factors/allometric_equations.json. Equations are written as code
(not evaluated from text) so they are safe and easy to test.
"""


def chave_2014_pantropical(wood_density, dbh, height):
    """EQ-001. Above ground biomass per tree in kg dry matter.

    0.0673 * (wood_density * dbh^2 * height) ^ 0.976
    wood_density in g/cm3, dbh in cm, height in m.
    """
    return 0.0673 * (wood_density * dbh ** 2 * height) ** 0.976


EQUATIONS = {
    "EQ-001": chave_2014_pantropical,
}