#!/bin/bash -l
# spack load /u64kqpe /tymduoi gcc@9.3.0/hufzek && pip install -U datasets gdown Cython networkx xlwt pandas tqdm
# (cd lp_solve_5.5/lpsolve55 && sh ccc)
export LD_LIBRARY_PATH="/home/mac9908/clara/lp_solve_dev"
(cd lp_solve_5.5/extra/Python/ && python setup.py install --user)
# make
export PATH="$PATH:/home/mac9908/clara/bin/"