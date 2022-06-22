# syntax=docker/dockerfile:1
FROM ubuntu:18.04
COPY .
RUN apt-get install lp-solve liblpsolve55-dev python3 python3-pip
RUN py_site_package=$(python3 -m site --user-site)
RUN cp -r ./lpsolve_python3.4 $py_site_package
RUN pip3 install Cython
RUN make
RUN clara=./bin/clara
RUN clara repair eg/t1.py eg/t2.py \
    --args "[[4], [5]]" \
    --verbose 1 

