# syntax=docker/dockerfile:1
FROM ubuntu:18.04
COPY . /clara
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y lp-solve liblpsolve55-dev python3 python3-pip 
RUN py_site_package=$(python3 -m site --user-site)
RUN cp -r /clara/lpsolve_python3.4/* $py_site_package/
RUN pip3 install Cython networkx
RUN export LD_LIBRARY_PATH=/usr/lib/lp_solve/
RUN make /clara
# RUN clara=/clara/bin/clara
# RUN ./bin/clara repair eg/t1.py eg/t2.py --args "[[4], [5]]" --verbose 1 

