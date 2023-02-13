# syntax=docker/dockerfile:1
FROM ubuntu:20.04
# COPY . /clara
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y lp-solve liblpsolve55-dev python3 python3-pip git
ARG CACHEBUST=2
RUN git clone https://towhidabsar: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@github.com/towhidabsar/clara.git
RUN py_site_package=$(python3 -m site --user-site)
RUN cp -r /clara/lpsolve_python3.4/site-packages/* $py_site_package/
RUN pip3 install Cython networkx xlwt pandas tqdm
# RUN export LD_LIBRARY_PATH=/usr/lib/lp_solve/
ENV LD_LIBRARY_PATH "/usr/lib/lp_solve/"
ENV PATH "$PATH:/clara/bin/" 
WORKDIR "/clara"
RUN git pull
RUN make

# RUN clara=/clara/bin/clara
# RUN ./bin/clara repair eg/t1.py eg/t2.py --args "[[4], [5]]" --verbose 1 

# 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

# docker run --name=clara_container -v E:\code\Clara_Data\Output:/data -it clara

# docker build --name=

# spack load lp-solve /u64kqpe /tymduoi && pip install -U datasets gdown Cython networkx xlwt pandas tqdm
# sh lp_solve_5.5/lpsolve55/ccc
# export LD_LIBRARY_PATH="/home/mac9908/clara/lp_solve_dev"
# python lp_solve_5.5/extra/Python/setup.py install --user
# make