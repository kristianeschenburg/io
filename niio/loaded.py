# -*- coding: utf-8 -*-
"""
Created on Thu Mar  2 10:43:58 2017

@author: kristianeschenburg
"""

import numpy as np
import nibabel as nb
import scipy.io as sio

import os
import h5py
import pickle


def load(datafile, **kwargs):

    """
    Wrapper method to load common neuroimaging data.
    """

    assert os.path.exists(datafile)

    filename, file_extension = os.path.splitext(datafile)

    function_map = {'.mat': loadMat,
                    '.gii': loadGii,
                    '.h5': loadH5,
                    '.p': loadPick}

    return function_map[file_extension](datafile, **kwargs)


def loadMat(infile, datasets=None):
    """
    Method to load .mat files.

    Parameters:
    - - - - -
        matFile : input .mat file
        datasets : if you know the specific key, provide key name.  Otherwise,
                    returns first non-private key data array.
    """

    try:
        matData = h5py.File(infile, mode='r')
    except OSError:
        try:
            matData = sio.loadmat(infile)
        except FileNotFoundError:
            err = 'Cannot read with h5py or scipy.io.'
            raise Warning(err)

    # if key name is known
    if datasets:
        try:
            mat = np.asarray(matData[datasets]).squeeze()
        except KeyError:
            pass
        else:
            if type(matData) == h5py._hl.files.File:
                mat = mat.T

    # otherwise, parse through keys, and select first non-private key name
    # and data array
    else:

        # remove private keys
        keys = [k for k in matData.keys() if k.startswith('_')]
        matData = {k: matData[k] for k in matData.keys() if k not in keys}

        # get first non-private key
        key = list(matData.keys())[0]
        mat = np.asarray(matData[key]).squeeze()

        if type(matData) == h5py._hl.files.File:
                mat = mat.T

    # if h5py, close object
    if type(matData) == h5py._hl.files.File:
        matData.close()

    return mat


def loadGii(infile, datasets=[], group=None):
    """
    Method to load Gifti files.

    Parameters:
    - - - - -
        infile : input gifti file
        darrayID : if array is .gii, often comes with multiple arrays
                    you can choose to specify which one
    """

    try:
        gii = nb.load(infile)
    except IOError:
        raise Warning('{} cannot be read.'.format(infile))

    if isinstance(datasets, int):
        datasets = [datasets]
    elif isinstance(datasets, np.ndarray):
        datasets = list(datasets)
    elif datasets == []:
        datasets = list(np.arange(len(gii.darrays)))

    if isinstance(gii, nb.gifti.GiftiImage):
        darray = []
        for j in datasets:
            darray.append(np.asarray(gii.darrays[j].data).squeeze())
        darray = np.column_stack(darray).squeeze()
    elif isinstance(gii, nb.nifti2.Nifti2Image):
        darray = np.asarray(gii.get_data()).squeeze()
    else:
        raise IOError('Cannot access array data.')

    return darray


def loadH5(infile, datasets=None, group=None):
    """
    Method to load hdf5 files.

    Parameters:
    - - - - -
        inFile : input file name
        datasets : attributes in file to be extracted.  Otherwise, returns
                dictionary of all key-value pairs in file.
        group : group in which datasets are contained.  Otherwise, datasets
                assumed to exist at top level of file structure.
    """

    assert os.path.exists(infile)

    try:
        h5 = h5py.File(infile, 'r')
    except IOError:
        raise Warning('File cannot be loaded.')

    # If user specifies an object group containing data
    data = {}
    if group:
        try:
            h5Lower = h5[group]
            h5.close()
        except KeyError:
            raise Warning('File does not have group {}.'.format(group))
    else:
        h5Lower = h5

    # If User specifies specific object datasets
    if not datasets:
        datasets = h5Lower.keys()

    for k in datasets:
        try:
            data[k] = np.asarray(h5Lower[k])
        except KeyError:
            raise Warning('File does not have attribute {}.'.format(k))

    h5Lower.close()

    return data


def loadPick(infile, datasets=None, group=None):
    """
    Method to load pickle file.  Not part of a specific class.

    Parameters:
    - - - - -
        pickleFile : input pickle file
    """

    assert os.path.exists(infile)

    try:
        with open(infile, "rb") as inPickle:
            pick = pickle.load(inPickle)
    except IOError:
        raise Warning('File cannot be loaded.')

    return pick

def loadSurf(inFile, gifti=True):

    """
    Method to load gifti surface file.

    Parameters:
    - - - - -
    inFile: str
        path to surface file
    
    Returns:
    - - - -
    vertices: float, array
        array of mesh vertices
    faces: int, array
        array of mesh triangles
    """

    if gifti:
        surf = nb.load(inFile)
        vertices = surf.darrays[0].data
        faces = surf.darrays[1].data
    else:
        surf = nb.freesurfer.read_geometry(inFile)
        vertices = surf[0]
        faces = surf[1]

    return [vertices, faces]