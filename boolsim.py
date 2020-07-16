"""
This Python module is an interface to the software tools boolSim
(https://www.vital-it.ch/research/software/boolSim) for the computation of
attractors in synchronous and asynchronous Boolean Networks.

Examples can be found at
https://nbviewer.jupyter.org/github/pauleve/boolSim-python/tree/main/examples/.
"""
import os
import shutil
import subprocess
import tempfile
import sys

import pandas as pd

from colomoto.minibn import BooleanNetwork
from colomoto.types import *
from colomoto_jupyter import import_colomoto_tool

def execute(model, update_mode, output):
    if isinstance(model, BooleanNetwork):
        model = model.to_biolqm()

    def biolqm_import(biolqm, model):
        netfile = os.path.join(output, "network.txt")
        assert biolqm.save(model, netfile, "boolsim")
        return netfile

    if "biolqm" in sys.modules:
        biolqm = sys.modules["biolqm"]
        if biolqm.is_biolqm_object(model):
            model = biolqm_import(biolqm, model)
    if "ginsim" in sys.modules:
        ginsim = sys.modules["ginsim"]
        if ginsim.is_ginsim_object(model):
            biolqm = import_colomoto_tool("biolqm")
            model = ginsim.to_biolqm(model)
            model = biolqm_import(biolqm, model)
    assert isinstance(model, str), "unsupported type of model input"

    update_mode = "3" if update_mode.startswith("async") else "1"
    args = ["boolSim", "-f", model,
                "-p", update_mode,
                "-o", os.path.join(output, "out")]
    subprocess.check_call(args)

def parse_attractor(filename):
    with open(filename) as fp:
        fp.readline() # skip header
        df = pd.read_fwf(fp, index_col=0, header=None)
        df = df.replace(2, "*")
    tps = []
    for col in df.columns:
        tp = df[col].to_dict()
        if "*" in tp.values():
            tp = TrapSpaceAttractor(tp)
        else:
            tp = State(tp)
        tps.append(tp)
    if len(tps) > 1:
        return TrapSpacesAttractor(tps)
    return tps[0]

def attractors(bn, update_mode="asynchronous"):
    """
    Compute the attractors of the given Boolean network `bn` using the
    `update_mode` (either ``"asynchronous"`` or ``"synchronous"``).

    `bn` can be either:
        - ``colomoto.minibn.BooleanNetwork``, ``biolqm``, or ``ginsim`` object
        - filename in SBML-qual or boolSim format.

    Returns a list of ``colomoto.types.State``,
        ``colomoto.types.TrapSpaceAttractor``, or
        ``colomoto.types.TrapSpacesAttractor``, depending on the kind of
        attractors.
    """
    output = tempfile.mkdtemp(prefix="BoolSim-")
    try:
        execute(bn, update_mode, output)
        return [parse_attractor(os.path.join(output, out))\
                    for out in os.listdir(output) if out.startswith("out_")]
    finally:
        shutil.rmtree(output)

