from ast import parse, Expression, Module
from os.path import join
from typing import List, Any, MutableMapping

from pkg_resources import resource_listdir, resource_isdir, resource_stream
from public import public

from .formula import (Formula, EFDFormula, AdditionEFDFormula, DoublingEFDFormula,
                      TriplingEFDFormula,
                      DifferentialAdditionEFDFormula, LadderEFDFormula, ScalingEFDFormula,
                      NegationEFDFormula)


@public
class CoordinateModel(object):
    """A coordinate system for a particular model(form) of an elliptic curve."""
    name: str
    full_name: str
    curve_model: Any
    variables: List[str]
    satisfying: List[Module]
    parameters: List[str]
    assumptions: List[Module]
    formulas: MutableMapping[str, Formula]

    def __repr__(self):
        return f"{self.__class__.__name__}(\"{self.name}\" on {self.curve_model.name})"


@public
class AffineCoordinateModel(CoordinateModel):
    name = "affine"
    full_name = "Affine coordinates"

    def __init__(self, curve_model: Any):
        self.curve_model = curve_model
        self.variables = ["x", "y"]
        self.satisfying = []
        self.parameters = []
        self.assumptions = []
        self.formulas = {}

    def __eq__(self, other):
        if not isinstance(other, AffineCoordinateModel):
            return False
        return self.curve_model == other.curve_model


class EFDCoordinateModel(CoordinateModel):

    def __init__(self, dir_path: str, name: str, curve_model: Any):
        self.name = name
        self.curve_model = curve_model
        self.variables = []
        self.satisfying = []
        self.parameters = []
        self.assumptions = []
        self.formulas = {}
        for fname in resource_listdir(__name__, dir_path):
            file_path = join(dir_path, fname)
            if resource_isdir(__name__, file_path):
                self.__read_formula_dir(file_path, fname)
            else:
                self.__read_coordinates_file(file_path)

    def __read_formula_dir(self, dir_path, formula_type):
        for fname in resource_listdir(__name__, dir_path):
            if fname.endswith(".op3"):
                continue
            formula_types = {
                "addition": AdditionEFDFormula,
                "doubling": DoublingEFDFormula,
                "tripling": TriplingEFDFormula,
                "diffadd": DifferentialAdditionEFDFormula,
                "ladder": LadderEFDFormula,
                "scaling": ScalingEFDFormula,
                "negation": NegationEFDFormula
            }
            cls = formula_types.get(formula_type, EFDFormula)
            self.formulas[fname] = cls(join(dir_path, fname), fname, self)

    def __read_coordinates_file(self, file_path):
        with resource_stream(__name__, file_path) as f:
            line = f.readline().decode("ascii")
            while line:
                line = line[:-1]
                if line.startswith("name"):
                    self.full_name = line[5:]
                elif line.startswith("variable"):
                    self.variables.append(line[9:])
                elif line.startswith("satisfying"):
                    try:
                        code = parse(line[11:].replace("^", "**"), mode="exec")
                        self.satisfying.append(code)
                    except SyntaxError:
                        # code = parse(line[11:].replace("=", "==").replace("^", "**"), mode="eval")
                        pass
                elif line.startswith("parameter"):
                    self.parameters.append(line[10:])
                elif line.startswith("assume"):
                    self.assumptions.append(
                            parse(line[7:].replace("^", "**"), mode="exec"))
                line = f.readline().decode("ascii")

    def __eq__(self, other):
        if not isinstance(other, EFDCoordinateModel):
            return False
        return self.curve_model == other.curve_model and self.name == other.name

    def __hash__(self):
        return hash(self.curve_model) + hash(self.name)
