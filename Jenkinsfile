pipeline {
    agent any
    options {
        disableConcurrentBuilds()
        skipDefaultCheckout()
    }
    triggers { pollSCM('H/2 * * * *') }
    environment {
        IMAGE_REPO = 'localhost:5001/cafeteria'
        LAB_NAMESPACE = 'cafeteria-lab4'
    }
    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
                sh 'mkdir -p reports && find reports -maxdepth 1 -type f -delete'
                script {
                    env.SOURCE_REVISION = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "build-${env.BUILD_NUMBER}-${env.SOURCE_REVISION.take(12)}"
                    env.LOCAL_IMAGE = "cafeteria:lab4-${env.IMAGE_TAG}"
                }
            }
        }
        stage('Semgrep') {
            steps { sh 'python3 scripts/security/scan.py --image "$LOCAL_IMAGE" --checks lab4-semgrep' }
        }
        stage('Snyk') {
            steps {
                withCredentials([string(credentialsId: 'lab4-snyk', variable: 'SNYK_TOKEN')]) {
                    sh '''#!/bin/sh
                        set -eu
                        if [ -z "$SNYK_TOKEN" ] || [ "$SNYK_TOKEN" = "SIN_CONFIGURAR" ]; then
                            echo 'Configurar la credencial de Snyk para habilitar el escaneo.' | tee reports/snyk-report.txt
                            exit 1
                        fi
                        python3 -m venv .venv
                        .venv/bin/pip install --quiet -r requirements.lock
                        status=0
                        snyk test --file=requirements.lock --package-manager=pip \
                            --command="$PWD/.venv/bin/python" --json-file-output=reports/snyk-report.json \
                            > reports/snyk-report.txt 2>&1 || status=$?
                        cat reports/snyk-report.txt
                        python3 scripts/lab4/check-snyk.py "$status" reports/snyk-report.json
                    '''
                }
            }
        }
        stage('Build y tests') {
            steps {
                sh '''
                    .venv/bin/pip install --quiet -r requirements-dev.txt
                    .venv/bin/python -m compileall -q app
                    .venv/bin/python -m pytest -q --junitxml=reports/pytest.xml
                '''
            }
            post { always { junit allowEmptyResults: true, testResults: 'reports/pytest.xml' } }
        }
        stage('Imagen y Trivy') {
            steps {
                sh '''
                    docker build --label org.opencontainers.image.revision="$SOURCE_REVISION" -t "$LOCAL_IMAGE" .
                    python3 scripts/security/scan.py --image "$LOCAL_IMAGE" --checks trivy
                '''
            }
        }
        stage('Publicar') {
            steps {
                sh '''
                    docker tag "$LOCAL_IMAGE" "$IMAGE_REPO:$IMAGE_TAG"
                    docker push "$IMAGE_REPO:$IMAGE_TAG"
                '''
            }
        }
        stage('Desplegar con Helm') {
            steps {
                withCredentials([file(credentialsId: 'lab4-kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        helm upgrade --install cafeteria ./helm-chart -n "$LAB_NAMESPACE" \
                            -f helm-chart/values-dev.yaml --set-string "image.repository=$IMAGE_REPO" \
                            --set-string "image.tag=$IMAGE_TAG" --wait=legacy --timeout 4m
                        kubectl -n "$LAB_NAMESPACE" rollout status deployment/cafeteria --timeout=90s
                        curl -fsS --retry 5 --retry-all-errors http://cafeteria-lab4-control-plane:30081/healthz
                    '''
                }
            }
        }
    }
    post {
        always { archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true }
    }
}
