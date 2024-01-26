import numpy as np
from os.path import *
import yaml
import json 
from .utils import get_extinction

DEFAULT_MBAR_CALIB = join(dirname(abspath(__file__)), "params", "mbar_calibrations.yml")
DEFAULT_MBAR_PARAM = join(dirname(abspath(__file__)), "params", "mbar_params.yml")


def get_Mbar(Mbar_filter = "F110W",
             color_camera = "PS",
             calib_mode = "linear",
             calib_color = "g_z",
             color_json = "",
             calib_yaml = DEFAULT_MBAR_CALIB,
             param_yaml = DEFAULT_MBAR_PARAM,
             verbose = False,
             ):
    
    with open(param_yaml, 'r') as file:
        params = yaml.safe_load(file)

    with open(calib_yaml, 'r') as file:
        calibs = yaml.safe_load(file)

    
    with open(color_json, 'r') as f:
        colors = json.load(f)

    
    ext_sig = params["ext_sig"]
    Prsig = params["Prsig"]
    LMC_correction = params["LMC_correction"]

    ext_1 = colors["extinctions"][0]    # extinction
    ext_2 = colors["extinctions"][1]
    color_0 = colors["MEDC0"]
    color_1 = colors["MEDC1"]
    color_2 = colors["MEDC2"]
    color_5 = colors["MEDC5"]

    Mbar_params = calibs["mbarfilter"][calib_color][Mbar_filter][calib_mode]
    Mbar_curvature = Mbar_params["curvature"]
    Mbar_slope = Mbar_params["slope"]
    Mbar_zp = Mbar_params["zp"]
    Mbar_rms = Mbar_params["rms"]
    Mbar_offset = calibs["mbarfilter"][calib_color]["offset"]
    ra = colors["RA"]
    dec = colors["Dec"]

    df_extinction = get_extinction(ra, dec)
    df_extinction.set_index("Bandpass", inplace=True)

    ext_110 = df_extinction.loc["WFC3 F110W"]['The Galactic extinction']
    ext_160 = df_extinction.loc["WFC3 F160W"]['The Galactic extinction']


    camera_calib_params = calibs["color_conversion"][calib_color]["source"][color_camera]
    rms_c0 = camera_calib_params["rms_c0"]
    rms_c1 = camera_calib_params["rms_c1"]
    rms_c2 = camera_calib_params["rms_c2"]
    rms_c5 = camera_calib_params["rms_c5"]
    color_slope = camera_calib_params["slope"]
    color_zp = camera_calib_params["zp"]


    c0_sig = np.sqrt((ext_sig*(ext_1-ext_2))**2 + rms_c0**2)  # uncertainties
    c1_sig = np.sqrt((ext_sig*(ext_1-ext_2))**2 + rms_c1**2)
    c2_sig = np.sqrt((ext_sig*(ext_1-ext_2))**2 + rms_c2**2)
    c5_sig = np.sqrt((ext_sig*(ext_1-ext_2))**2 + rms_c5**2)

    ############################################################

    # Compute Mbar
    # This works for g-z but not tested for J-H yet.

    if calib_color=="j_h": 
        # Use J-H if necessary; we don't have other options yet.
        # note that 2MASS photometry is in Vega mags, the -0.4919 converts to AB
        color_0 -= 0.4919
        color_1 -= 0.4919
        color_2 -= 0.4919
        color_5 -= 0.4919


    c0 = color_0 * (1 + color_slope) + color_zp
    c1 = color_1 * (1 + color_slope) + color_zp
    c2 = color_2 * (1 + color_slope) + color_zp
    c5 = color_5 * (1 + color_slope) + color_zp

        
    Mbar_c0 = Mbar_zp + ((c0 + Mbar_offset) * Mbar_slope) - LMC_correction
    Mbar_c1 = Mbar_zp + ((c1 + Mbar_offset) * Mbar_slope) - LMC_correction
    Mbar_c2 = Mbar_zp + ((c2 + Mbar_offset) * Mbar_slope) - LMC_correction
    Mbar_c5 = Mbar_zp + ((c5 + Mbar_offset) * Mbar_slope) - LMC_correction


    Mbar_c0_sig = np.sqrt(Mbar_rms**2 + (Mbar_slope*c0_sig)**2)
    Mbar_c1_sig = np.sqrt(Mbar_rms**2 + (Mbar_slope*c1_sig)**2)
    Mbar_c2_sig = np.sqrt(Mbar_rms**2 + (Mbar_slope*c2_sig)**2)
    Mbar_c5_sig = np.sqrt(Mbar_rms**2 + (Mbar_slope*c5_sig)**2)

    if verbose:
        print(f"c0: ({calib_color}) =","{:.4}".format(c0),"+/-","{:.3}".format(c0_sig),"  Mbar =","{:.4}".format(Mbar_c0),"+/-","{:.3}".format(Mbar_c0_sig))
        print(f"c1: ({calib_color}) =","{:.4}".format(c1),"+/-","{:.3}".format(c1_sig),"  Mbar =","{:.4}".format(Mbar_c1),"+/-","{:.3}".format(Mbar_c1_sig))
        print(f"c2: ({calib_color}) =","{:.4}".format(c2),"+/-","{:.3}".format(c2_sig),"  Mbar =","{:.4}".format(Mbar_c2),"+/-","{:.3}".format(Mbar_c2_sig))
        print(f"c5: ({calib_color}) =","{:.4}".format(c5),"+/-","{:.3}".format(c5_sig),"  Mbar =","{:.4}".format(Mbar_c5),"+/-","{:.3}".format(Mbar_c5_sig))
 

        output = {}

        output["c0"] = {}
        output["c0"][calib_color] = (c0, c0_sig)
        output["c0"]["Mbar"] = (Mbar_c0, Mbar_c0_sig)

        output["c1"] = {}
        output["c1"][calib_color] = (c1, c1_sig)
        output["c1"]["Mbar"] = (Mbar_c1, Mbar_c1_sig)

        output["c2"] = {}
        output["c2"][calib_color] = (c2, c2_sig)
        output["c2"]["Mbar"] = (Mbar_c2, Mbar_c2_sig)

        output["c5"] = {}
        output["c5"][calib_color] = (c5, c5_sig)
        output["c5"]["Mbar"] = (Mbar_c5, Mbar_c5_sig)


        return output
        








