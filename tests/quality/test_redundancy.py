
import pytest

import topiary
from topiary.quality import remove_redundancy
from topiary.quality.redundancy import _get_quality_scores
from topiary.quality.redundancy import _construct_args
from topiary.quality.redundancy import _compare_seqs
from topiary.quality.redundancy import _redundancy_thread_function
from topiary.quality.redundancy import _EXPECTED_COLUMNS

import numpy as np
import pandas as pd

def test__get_quality_scores(test_dataframes):

    # Get copy of the dataframe -- we're going to hack it
    df = test_dataframes["good-df"].copy()
    species_in_df = list(df.species)

    # Needs to be defined.
    df["diff_from_median"] = 0

    # Make sure that the key species encoding works as expected
    # No key_species passed in or key_species not in dataframe
    assert _get_quality_scores(df.loc[0,:])[1] == 1
    assert _get_quality_scores(df.loc[0,:],{"Not a species":None})[1] == 1

    # Key species
    assert _get_quality_scores(df.loc[0,:],{species_in_df[0]:None})[1] == 0

    # Make sure quality assignment doing what we think
    for i in df.index:
        row = df.loc[i,:]
        scores = _get_quality_scores(row)

        values_from_df = list(row[_EXPECTED_COLUMNS])
        values_from_df.append(1/len(row.sequence))
        values_from_df = np.array(values_from_df,dtype=float)

        assert np.array_equal(scores[2:],values_from_df)

    # Test always_keep
    # No always_keep in datafframe
    assert _get_quality_scores(df.loc[0,:])[0] == 1

    df["always_keep"] = False # always keep False
    assert _get_quality_scores(df.loc[0,:])[0] == 1

    df["always_keep"] = True # always keep True
    assert _get_quality_scores(df.loc[0,:])[0] == 0

def test__construct_args():

    sequence_array = np.array(["STARE" for _ in range(4)])
    quality_array = np.array([np.zeros(3,dtype=int) for _ in range(4)])
    keep_array = np.ones(4,dtype=bool)
    cutoff = 0.9
    discard_key = True

    kwargs_list, num_threads = _construct_args(sequence_array=sequence_array,
                                               quality_array=quality_array,
                                               keep_array=keep_array,
                                               cutoff=cutoff,
                                               discard_key=discard_key,
                                               num_threads=1)

    assert num_threads == 1
    assert np.array_equal(kwargs_list[0]["i_block"],(0,4))
    assert np.array_equal(kwargs_list[0]["j_block"],(0,4))

    out = []
    for a in kwargs_list:
        i_block = a["i_block"]
        j_block = a["j_block"]
        for i in range(i_block[0],i_block[1]):
            for j in range(j_block[0],j_block[1]):
                if i >= j:
                    continue
                out.append((i,j))

    out.sort()
    assert np.array_equal(out,((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)))


    # Not worth chopping up problem for this small of an array -- should set
    # number of threads to 1.
    kwargs_list, num_threads = _construct_args(sequence_array=sequence_array,
                                               quality_array=quality_array,
                                               keep_array=keep_array,
                                               cutoff=cutoff,
                                               discard_key=discard_key,
                                               num_threads=2)

    assert num_threads == 1
    assert np.array_equal(kwargs_list[0]["i_block"],(0,4))
    assert np.array_equal(kwargs_list[0]["j_block"],(0,4))

def test__compare_seqs(test_dataframes):

    A_seq = "TEST"
    B_seq = "TAST"

    # Identical quals
    A_qual = np.zeros(len(_EXPECTED_COLUMNS) + 2,dtype=float)
    B_qual = np.zeros(len(_EXPECTED_COLUMNS) + 2,dtype=float)

    # Neither are always keep sequences
    A_qual[0] = 1
    B_qual[0] = 1

    # Neither are key sequences
    A_qual[1] = 1
    B_qual[1] = 1

    # Keep both; below cutoff
    a1, a2 = _compare_seqs(A_seq,B_seq,A_qual,B_qual,0.9)
    assert a1 is True
    assert a2 is True

    # Keep A arbitrarily
    a1, a2 = _compare_seqs(A_seq,B_seq,A_qual,B_qual,0.5)
    assert a1 is True
    assert a2 is False

    # Now make A_qual score worse than B, so keep B
    A_qual[2] = 1
    a1, a2 = _compare_seqs(A_seq,B_seq,A_qual,B_qual,0.5)
    assert a1 is False
    assert a2 is True

    # Not set up qual scores so neither are key_species, B has earlier better
    # score than A
    A_qual = np.ones(len(_EXPECTED_COLUMNS) + 2,dtype=float)
    B_qual = np.ones(len(_EXPECTED_COLUMNS) + 2,dtype=float)
    A_qual[-1] = 0
    B_qual[-2] = 0

    a1, a2 = _compare_seqs(A_seq,B_seq,A_qual,B_qual,0.5)
    assert a1 is False
    assert a2 is True

    # both key species, A worse than B. No always_keep
    A_qual = np.zeros(len(_EXPECTED_COLUMNS) + 2,dtype=float)
    B_qual = np.zeros(len(_EXPECTED_COLUMNS) + 2,dtype=float)
    A_qual[0] = 1
    B_qual[0] = 1
    A_qual[2] = 1

    # implicit discard_key flag
    a1, a2 = _compare_seqs(A_seq,B_seq,A_qual,B_qual,0.5)
    assert a1 is True
    assert a2 is True

    # Explicit discard_key flag
    a1, a2 = _compare_seqs(A_seq,B_seq,A_qual,B_qual,0.5,discard_key=False)
    assert a1 is True
    assert a2 is True

    # Check discard_key flag
    a1, a2 = _compare_seqs(A_seq,B_seq,A_qual,B_qual,0.5,discard_key=True)
    assert a1 is False
    assert a2 is True

    # both always keep, but  beter. Should keep both
    A_qual = np.zeros(len(_EXPECTED_COLUMNS) + 2,dtype=float)
    B_qual = np.zeros(len(_EXPECTED_COLUMNS) + 2,dtype=float)
    A_qual[2] = 1
    a1, a2 = _compare_seqs(A_seq,B_seq,A_qual,B_qual,0.5)
    assert a1 is True
    assert a2 is True

def test__redundancy_thread_function():

    pass


def test_remove_redundancy(test_dataframes):

    df = test_dataframes["good-df"].copy()

    # -------------------------------------------------------------------------
    # Test argument parsing

    bad_df = [None,-1,1.1,"test",int,float,{"test":1},pd.DataFrame({"test":[1,2,3]})]
    for b in bad_df:
        with pytest.raises(ValueError):
            remove_redundancy(df=b)

    remove_redundancy(df=df)

    bad_cutoff = [None,-1,1.1,"test",int,float,{"test":1},pd.DataFrame({"test":[1,2,3]})]
    for b in bad_cutoff:
        with pytest.raises(ValueError):
            remove_redundancy(df=df,cutoff=b)

    good_cutoff = [0,0.5,1]
    for g in good_cutoff:
        remove_redundancy(df=df,cutoff=g)

    bad_silent = [None,"test",int,float,{"test":1}]
    for b in bad_silent:
        print(f"trying bad silent {b}")
        with pytest.raises(ValueError):
            remove_redundancy(df=df,silent=b)

    good_silent = [True,False,0,1]
    for g in good_silent:
        print(f"trying good silent {g}")
        remove_redundancy(df=df,silent=g)


    # -------------------------------------------------------------------------
    # Make sure dropping is happening a sane way that depends on cutoff and
    # key_species.

    df = test_dataframes["good-df"].copy()
    species_in_df = list(df.species)

    # sequences in this dataframe are between 0.9125 and 0.98125 identical.
    out_df = remove_redundancy(df=df,cutoff=0.99)
    assert np.sum(out_df.keep) == np.sum(df.keep)

    # Cut some
    out_df = remove_redundancy(df=df,cutoff=0.96)
    assert np.sum(out_df.keep) < np.sum(df.keep)

    # Cut basically all -- only one shoudl survive
    out_df = remove_redundancy(df=df,cutoff=0.50)
    assert np.sum(out_df.keep) == 1

    # All key species -- all should survive
    df["key_species"] = True
    out_df = remove_redundancy(df=df,cutoff=0.50)
    assert np.sum(out_df.keep) == np.sum(df.keep)

    # One isn't keep -- make sure it's dropped
    df.loc[0,"key_species"] = False
    out_df = remove_redundancy(df=df,cutoff=0.50)
    assert np.sum(out_df.keep) == 4
    assert out_df.loc[out_df["species"] == species_in_df[0],:].iloc[0].keep == False


    # -------------------------------------------------------------------------
    # Make sure it takes row with higher quality

    df = test_dataframes["good-df"].copy()
    df = df.iloc[2:4]
    out_df = remove_redundancy(df=df,cutoff=0.50)
    assert out_df.keep.iloc[0] == False
    assert out_df.keep.iloc[1] == True

    df = test_dataframes["good-df"].copy()
    df = df.iloc[1:3]
    out_df = remove_redundancy(df=df,cutoff=0.50)
    assert out_df.keep.iloc[0] == True
    assert out_df.keep.iloc[1] == False

    # Make sure length bit is being processed properly. Make first sequence short
    # so it gets dropped
    df = test_dataframes["good-df_only-required-columns"].copy()
    df.loc[0,"sequence"] = "MLPFLFFS"
    df.loc[:,"length"] = [len(s) for s in df.loc[:,"sequence"]]
    out_df = remove_redundancy(df=df,cutoff=0.50)
    assert out_df.keep.iloc[0] == False

    # -------------------------------------------------------------------------
    # Check input dataframe without quality information

    # Should work fine but cut nothing
    df = test_dataframes["good-df_only-required-columns"].copy()
    out_df = remove_redundancy(df=df,cutoff=0.99)
    assert np.sum(out_df.keep) == len(df.sequence)

    # Cut some
    out_df = remove_redundancy(df=df,cutoff=0.96)
    assert np.sum(out_df.keep) <= len(df.sequence)

    # Cut basically all -- only one should survive
    out_df = remove_redundancy(df=df,cutoff=0.2)
    assert np.sum(out_df.keep) == 1
