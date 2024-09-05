import numpy as np
import subprocess
import os

def convert_imf(imf_input, imf_output):
    f_convert = 1
    # convert input imf to salpeter
    if imf_input == "Salpeter":
        pass
    elif imf_input == "Chabrier":
        f_convert = 1.7
    elif imf_input == "Kroupa":
        f_convert = 2.0 # for Salpeter IMF with a cut-off at 0.1 Msun (Kauffmann+ 2003)
    else:
        raise Exception("imf_input does not match")
    
    #convert from salpeter to output imf
    if imf_output == "Salpeter":
        pass
    elif imf_output == "Chabrier":
        f_convert /= 1.7
    elif imf_output == "Kroupa":
        f_convert /= 2.0
    else:
        raise Exception("imf_output does not match")
    
    return f_convert

def load_obsdata(key, z1, z2, IMF="Chabrier", ratio="undef", verbose=False):
    """
    returns observational data points

    Parameters
    ----------
    key: string
      which statistics to load, SMF, SFMS, ...
    z1: double
      minimum redshift of data to load
    z2: double
      maximum redshift of data to load
    IMF: string
      correct stellar mass for the IMF
    ratio: string
      necessary when key is MZR. select the abundance ratio to output
    verbose: bool
      output details when true

    Returns
    -------
    out: list of dictionary
      list of dictionaries containing data points and labels
      out[i]["x"]: x-axis
      out[i]["y"]: y-axis (average)
      out[i]["y1"]: y-axis (average - sigma)
      out[i]["y2"]: y-axis (average + sigma)
      out[i]["label"]: label in format of e.g., Oku+ 21 (z=0)
      out[i]["author"]: author
      out[i]["z"]: redshift
      out[i]["year"]: published year

    Examples
    --------
    >>> load_obsdata("SMF", 0, 2)
    
    >>> load_obsdata("MZR", 2, 3, IMF="Kroupa", ratio="O/H")
    """

    def pprint(txt):
        if verbose == True:
            print(txt)
        else:
            pass

    # sanity check of input parameters
    if IMF != "Chabrier" and IMF != "Salpeter" and IMF != "Kroupa":
        raise ValueError("Choose IMF from Chabrier, Salpeter, or Kroupa")
    
    if key == "MZR":
        if ratio == "undef":
            raise ValueError("Select which abundance ratio to output")

    # check if data directory is accessible
    rootdir = os.getenv("OBSDATA_DIR")
    if rootdir == None:
        raise Exception("ERROR: environment variable OBSDATA_DIR is not set")
    
    # get file names
    if key != "MZR":
        cmd = "ls -v1 "+rootdir+"/data/"+key+"/*.csv"
    else:
        if ratio == "O/H":
            cmd = "ls -v1 "+rootdir+"/data/"+key+"/O_H/*.csv"
        elif ratio == "N/H":
            cmd = "ls -v1 "+rootdir+"/data/"+key+"/N_H/*.csv"
        elif ratio == "Fe/H":
            cmd = "ls -v1 "+rootdir+"/data/"+key+"/Fe_H/*.csv"
        elif ratio == "N/O":
            cmd = "ls -v1 "+rootdir+"/data/"+key+"/N_O/*.csv"
        else:
            raise ValueError("Available data of abundance ratio are O/H or N/O")
    cp = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    fname = cp.stdout.split("\n")
    out = []
    for f in fname:
        if f == "":
            continue
        pprint("\nReading "+f)
        x = []  # x-axis
        y = []  # y-axis
        sm = []  # sigma minus
        sp = []  # sigma plus

        with open(f, "r") as fp:
            while 1:
                line = fp.readline()
                if not line:
                    break  # EOF
                line.rstrip(os.linesep)

                word = [w.strip() for w in line.split(",")]
                if word[0] == "#REF":
                    ref = word[1]
                if word[0] == "#AUTHOR":
                    author = word[1]
                if word[0] == "#YEAR":
                    year = word[1]
                if word[0] == "#REDSHIFT":
                    z = word[1]
                if word[0] == "#COLUMN1":
                    xaxis = word[1]
                if word[0] == "#COLUMN2":
                    yaxis = word[1]
                if word[0] == "#NOTE":
                    note = line.lstrip("#")
                if word[0] == "#IMF":
                    data_imf = word[1]

                # skip header
                if word[0][0] == "#":
                    continue

                for i in range(4):
                    if word[i] == "inf":
                        word[i] = np.inf
                    else:
                        word[i] = float(word[i])

                x.append(word[0])
                y.append(word[1])
                sm.append(word[2])
                sp.append(word[3])
            # end while
        # end file open

        # skip data if out of redshift range
        if float(z) < z1 or float(z) > z2:
            pprint("Out of redshift range. skipping...")
            continue

        # IMF correction
        if data_imf != "Chabrier" and data_imf != "Salpeter" and data_imf != "Kroupa":
            raise Exception("IMF not found in the header")

        log_conversion_factor = np.log10(convert_imf(data_imf, IMF))
        if key == "SMF":
            x += log_conversion_factor
        elif key == "SHMR":
            y += log_conversion_factor
        elif key == "SFRF":
            x += log_conversion_factor # same conversion factor for SFR?
        elif key == "SFMS":
            x += log_conversion_factor
            y += log_conversion_factor # ?
        elif key == "MZR":
            x += log_conversion_factor
        

        pprint("Loading data of "+author.replace("+",
              " et al.")+" ("+year+") at z="+z)
        pprint("X-axis: "+xaxis+", Y-axis: "+yaxis)
        pprint("Reference: "+ref)
        pprint(note)
        if(year[-1]=="a" or year[-1]=="b"):
            data = {
                "x": np.array(x),
                "y": np.array(y),
                "y1": np.array(y) - np.array(sm),
                "y2": np.array(y) + np.array(sp),
                "label": author+" "+year[-3:]+" (z="+z+")",
                "author": author,
                "z": z,
                "year": year,
            }
        else:
            data = {
                "x": np.array(x),
                "y": np.array(y),
                "y1": np.array(y) - np.array(sm),
                "y2": np.array(y) + np.array(sp),
                "label": author+" "+year[-2:]+" (z="+z+")",
                "author": author,
                "z": z,
                "year": year,
            }

        out.append(data)
    # end loop over files

    return out


def load_target_obsdata(key, target, IMF="Chabrier", ratio="undef", verbose=False):
    """
    returns targeted observational data points

    Parameters
    ----------
    key: string
      which statistics to load, SMF, SFMS, ...
    target: string
      data name
    IMF: string
      correct stellar mass for the IMF
    ratio: string
      necessary when key is MZR. select the abundance ratio to output
    verbose: bool
      output details when true

    Returns
    -------
    out: list of dictionary
      list of dictionaries containing data points and labels
      out[i]["x"]: x-axis
      out[i]["y"]: y-axis (average)
      out[i]["y1"]: y-axis (average - sigma)
      out[i]["y2"]: y-axis (average + sigma)
      out[i]["label"]: label in format of e.g., Oku+ 21 (z=0)
      out[i]["author"]: author
      out[i]["z"]: redshift
      out[i]["year"]: published year

    Examples
    --------
    >>> load_obsdata("SMF", "davidzon2017_z1.05")
    
    >>> load_obsdata("MZR", "andrews2013_z0.1", IMF="Kroupa", ratio="O/H")
    """

    def pprint(txt):
        if verbose == True:
            print(txt)
        else:
            pass

    # sanity check of input parameters
    if IMF != "Chabrier" and IMF != "Salpeter" and IMF != "Kroupa":
        raise ValueError("Choose IMF from Chabrier, Salpeter, or Kroupa")
    
    if key == "MZR":
        if ratio == "undef":
            raise ValueError("Select which abundance ratio to output")

    # check if data directory is accessible
    rootdir = os.getenv("OBSDATA_DIR")
    if rootdir == None:
        raise Exception("ERROR: environment variable OBSDATA_DIR is not set\nPlease set the path to observational-data in the environment variable OBSDATA_DIR")
    
    # get file names
    if key != "MZR":
        f = rootdir+"/data/"+key+"/"+target+".csv"
    else:
        if ratio == "O/H":
            f = rootdir+"/data/"+key+"/O_H/"+target+".csv"
        elif ratio == "N/H":
            f = rootdir+"/data/"+key+"/N_H/"+target+".csv"
        elif ratio == "Fe/H":
            f = rootdir+"/data/"+key+"/Fe_H/"+target+".csv"
        elif ratio == "N/O":
            f = rootdir+"/data/"+key+"/N_O/"+target+".csv"
        else:
            raise ValueError("Available data of abundance ratio are O/H or N/O")
    
    pprint("\nReading "+f)
    x = []  # x-axis
    y = []  # y-axis
    sm = []  # sigma minus
    sp = []  # sigma plus
    with open(f, "r") as fp:
        while 1:
            line = fp.readline()
            if not line:
                break  # EOF
            line.rstrip(os.linesep)
            word = [w.strip() for w in line.split(",")]
            if word[0] == "#REF":
                ref = word[1]
            if word[0] == "#AUTHOR":
                author = word[1]
            if word[0] == "#YEAR":
                year = word[1]
            if word[0] == "#REDSHIFT":
                z = word[1]
            if word[0] == "#COLUMN1":
                xaxis = word[1]
            if word[0] == "#COLUMN2":
                yaxis = word[1]
            if word[0] == "#NOTE":
                note = line.lstrip("#")
            if word[0] == "#IMF":
                data_imf = word[1]
            # skip header
            if word[0][0] == "#":
                continue
            for i in range(4):
                if word[i] == "inf":
                    word[i] = np.inf
                else:
                    word[i] = float(word[i])
            x.append(word[0])
            y.append(word[1])
            sm.append(word[2])
            sp.append(word[3])
        # end while
    # end file open

    # IMF correction
    if data_imf != "Chabrier" and data_imf != "Salpeter" and data_imf != "Kroupa":
        raise Exception("IMF not found in the header")
    log_conversion_factor = np.log10(convert_imf(data_imf, IMF))
    if key == "SMF":
        x += log_conversion_factor
    elif key == "SHMR":
        y += log_conversion_factor
    elif key == "SFRF":
        x += log_conversion_factor # same conversion factor for SFR?
    elif key == "SFMS":
        x += log_conversion_factor
        y += log_conversion_factor # ?
    elif key == "MZR":
        x += log_conversion_factor
        
    pprint("Loading data of "+author.replace("+",
          " et al.")+" ("+year+") at z="+z)
    pprint("X-axis: "+xaxis+", Y-axis: "+yaxis)
    pprint("Reference: "+ref)
    pprint(note)
    data = {
        "x": np.array(x),
        "y": np.array(y),
        "y1": np.array(y) - np.array(sm),
        "y2": np.array(y) + np.array(sp),
        "label": author+" "+year[-2:]+" (z="+z+")",
        "author": author,
        "z": z,
        "year": year,
    }

    return data

