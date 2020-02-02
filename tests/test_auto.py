import pytest

from utils import get_full_data_filename, parse_file

from clara.interpreter import getlanginter
from clara.matching import Matching
from clara.parser import getlangparser

def matching_helper(f1, f2, lang, ins=None, args=None, entryfnc="main"):
    f1 = get_full_data_filename(f1)
    f2 = get_full_data_filename(f2)
    
    parser = getlangparser(lang)
    inter = getlanginter(lang)

    m1 = parse_file(f1, parser)
    m2 = parse_file(f2, parser)

    M = Matching(ignoreio=not ins, ignoreret=not args)
    return not not M.match_programs(m1, m2, inter, ins=ins,
                                    args=args, entryfnc=entryfnc)

testdata_c = [
    ('p1.c', 'p2.c', [[4]], True)
]

@pytest.mark.parametrize(
    ('f1', 'f2', 'ins', 'should_match'),
    testdata_c)
def test_match_c(f1, f2, ins, should_match):
    """
    Tests whether the C files `f1` and `f2` match with the inputs `ins`.
    `should_match` indicates whether the files should match.
    """
    match = matching_helper(f1, f2, 'c', ins=ins)
    assert match == should_match

    # If f1 (not) matches f2, then f2 should also (not) match f1
    match = matching_helper(f2, f1, 'c', ins=ins)
    assert match == should_match
