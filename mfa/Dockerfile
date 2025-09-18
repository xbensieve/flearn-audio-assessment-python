FROM continuumio/miniconda3
WORKDIR /mfa
RUN conda create -n mfa -c conda-forge montreal-forced-aligner=2.2.15 flask praatio -y \
    && conda install -n mfa -c conda-forge joblib=1.3.2 -y
SHELL ["conda", "run", "-n", "mfa", "/bin/bash", "-c"]
ENV MFA_ROOT_DIR=/mfa/models
RUN mkdir -p $MFA_ROOT_DIR
RUN mfa model download dictionary english_us_mfa \
    && mfa model download acoustic english_mfa \
    && mfa model download dictionary mandarin_mfa \
    && mfa model download acoustic mandarin_mfa \
    && mfa model download dictionary japanese_mfa \
    && mfa model download acoustic japanese_mfa

# Copy Flask server
COPY mfa_server.py .
EXPOSE 5000
CMD ["conda", "run", "--no-capture-output", "-n", "mfa", "python", "mfa_server.py"]