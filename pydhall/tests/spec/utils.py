import os

import pytest

from . import FAILURES

def make_test_file_pairs(dir, b_ext=".dhall"):
    pairs = []
    files = os.listdir(dir)
    for name1 in files:
        path1 = dir.joinpath(name1)
        if os.path.isdir(path1):
            print(path1)
            pairs.extend(make_test_file_pairs(path1, b_ext))
            continue
        name2 = name1.replace("A.", "B.")
        name2 = name2.replace(".dhall", b_ext)
        path2 = dir.joinpath(name2)
        if (name1 != name2) and (name2 in files):
            if str(path1).replace("A.dhall", "") in FAILURES:
                pairs.append(
                    pytest.param(
                        path1,
                        path2,
                        marks=pytest.mark.xfail(strict=True)))
            else:
                pairs.append((path1, path2))
    return pairs


def collect_test_files(dir):
    result = []
    files = os.listdir(dir)
    for name in files:
        if "README" in name:
            continue
        path = dir.joinpath(name)
        if os.path.isdir(path):
            result.extend(collect_test_files(path))
            continue
        if str(path).replace(".dhall", "") in FAILURES:
            print(path)
            result.append(
                pytest.param(
                    path,
                    marks=pytest.mark.xfail(strict=True)))
        else:
            result.append(path)
    return result


