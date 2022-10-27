# syntax=docker/dockerfile:1
FROM ubuntu:18.04
# COPY . /clara
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y lp-solve liblpsolve55-dev python3 python3-pip git
ARG CACHEBUST=1
RUN git clone https://towhidabsar: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@github.com/towhidabsar/clara.git
RUN py_site_package=$(python3 -m site --user-site)
RUN cp -r /clara/lpsolve_python3.4/* $py_site_package/
RUN pip3 install Cython networkx xlwt
# RUN export LD_LIBRARY_PATH=/usr/lib/lp_solve/
ENV LD_LIBRARY_PATH "/usr/lib/lp_solve/"
ENV PATH "$PATH:/clara/bin/" 
WORKDIR "/clara"
RUN make
# RUN clara=/clara/bin/clara
# RUN ./bin/clara repair eg/t1.py eg/t2.py --args "[[4], [5]]" --verbose 1 

# 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
# docker run --name=nginx -d -v ~/nginxlogs:/var/log/nginx -p 5000:80 nginx
# docker run --name=clara_container -d -v ~/eg:/test clara repair /test/t1.py /test/t2.py --args "[[4], [5]]" --verbose 1 >> /test/out.txt 
# docker run --name=clara_container -v E:\code\Clara_Data\Sample\1A:/data -it clara
