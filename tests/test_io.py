import pytest

from topiary import io
import numpy as np
import pandas as pd

import warnings, os


def test_read_dataframe(dataframe_good_files,test_dataframes):
    """
    Test read dataframe function.
    """

    ref_df = test_dataframes["good-df"]

    for f in dataframe_good_files:

        # Print f in case parsing dies... so we know which file causes failure.
        print(f)

        # Read file and make sure it does not throuw warning.
        with warnings.catch_warnings():
            warnings.simplefilter("error")

            df = io.read_dataframe(f)
            assert len(df) == len(ref_df)

            # Make sure expected columns are present
            df.uid
            df.keep

    # Check reading a dataframe
    df = io.read_dataframe(ref_df)
    assert len(df) == len(ref_df)
    assert df is not ref_df # make sure it's a copy
    df.uid
    df.keep

    # Make sure dies with useful error
    bad_inputs = [1,-1,1.5,None,False,pd.DataFrame]
    for b in bad_inputs:
        with pytest.raises(ValueError):
            io.read_dataframe(b)

    # Make sure raises file not found if a file is not passed
    with pytest.raises(FileNotFoundError):
        io.read_dataframe("not_really_a_file.txt")

def test_write_dataframe():
    pass




# def test_ncbi_blast_xml_to_df():
#
#     pass
#     #xml_files,
#     # aliases=None,
#     #phylo_context="All life"
#
# def test_write_fasta():
#     pass
#     #df,out_file,seq_column="sequence",seq_name="pretty",
#     #write_only_keepers=True,empty_char="X-?",clean_sequence=False)
#
# def test_write_phy():
#     pass
#     #df,out_file,seq_column="sequence",
#     #          write_only_keepers=True,
#     #          empty_char="X-?",
#     #          clean_sequence=False):
#
# def test_read_fasta():
#     pass
#     #df,fasta_file,load_into_column="alignment",empty_char="X-?",unkeep_missing=True):