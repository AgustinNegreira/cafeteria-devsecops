# Jenkins con lo que necesita el pipeline de la cafeteria:
#   - python3 para correr los tests
#   - docker-cli para construir y subir la imagen (usa el Docker de la
#     maquina a traves del socket: "Docker outside of Docker")
#   - kubectl para desplegar en el cluster
# Plugins y configuracion vienen ya cargados: no hay asistente web.

FROM jenkins/jenkins:lts

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends docker-cli python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Misma version menor que el cluster de la UCU (v1.29).
ARG KUBECTL_VERSION=v1.29.5
RUN curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod +x /usr/local/bin/kubectl

# El socket de Docker es root:root 660: jenkins necesita el grupo root para usarlo.
RUN usermod -aG root jenkins

# El repo se monta en /proyecto y su dueno no es jenkins: git lo bloquea
# ("dubious ownership") si no lo marcamos como confiable.
RUN git config --system --add safe.directory /proyecto \
    && git config --system --add safe.directory /proyecto/.git

USER jenkins

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# runSetupWizard=false: la configuracion sale de casc.yaml, no de clicks.
# ALLOW_LOCAL_CHECKOUT: el job clona desde la carpeta montada, no desde GitHub.
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true"
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/casc.yaml
