FROM jupyter/scipy-notebook

RUN pip install pip-tools
COPY jupyter/requirements.in requirements.in
RUN pip-compile
RUN pip install -r requirements.txt
