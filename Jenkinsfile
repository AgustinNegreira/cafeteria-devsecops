pipeline {
    agent any
    options { disableConcurrentBuilds() }
    environment { IMAGEN = "cafeteria:devsecops-build-${env.BUILD_NUMBER}" }
    stages {
        stage('Tests') {
            steps {
                sh '''
                    mkdir -p reports
                    find reports -maxdepth 1 -type f -delete
                    python3 -m venv .venv
                    .venv/bin/pip install --quiet --disable-pip-version-check -r requirements-dev.txt
                    .venv/bin/python -m pytest -q --junitxml=reports/pytest.xml
                '''
            }
            post { always { junit allowEmptyResults: true, testResults: 'reports/pytest.xml' } }
        }
        stage('Codigo y manifiestos') {
            steps { sh 'python3 scripts/security/scan.py --image "$IMAGEN" --checks npm,pip,semgrep,kubelinter' }
        }
        stage('Build') {
            steps { sh 'docker build --label org.opencontainers.image.revision="$GIT_COMMIT" --label org.opencontainers.image.version="$IMAGEN" -t "$IMAGEN" .' }
        }
        stage('Trivy') {
            steps { sh 'python3 scripts/security/scan.py --image "$IMAGEN" --checks trivy' }
        }
        stage('Deploy local - Kyverno') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-local', variable: 'KUBECONFIG')]) {
                    sh 'python3 scripts/local/deploy.py --image "$IMAGEN" --kubeconfig "$KUBECONFIG"'
                }
            }
        }
        stage('Verificacion') {
            steps { sh 'curl -fsS --retry 5 --retry-delay 2 --retry-all-errors http://cafeteria-devsecops-control-plane:30080/healthz' }
        }
    }
    post {
        always { archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true }
        success { echo 'Controles y despliegue local completados.' }
        failure { echo 'Ver la etapa fallida y los reportes archivados.' }
    }
}
