// CI/CD de la cafeteria: cada commit en main termina publicado en el cluster.
//
//   Tests -> Build -> Push a Docker Hub -> Deploy al cluster -> Verificacion
//
// Si un stage falla, los siguientes no corren: si los tests fallan, la imagen
// no se construye y el cluster sigue con la version anterior.

pipeline {
    agent any

    options {
        // Dos despliegues a la vez sobre el mismo Deployment se pisarian.
        disableConcurrentBuilds()
    }

    environment {
        IMAGEN = 'agustinnegreira/cafeteria'
        // Cada build produce una imagen con su propio numero: se sabe
        // exactamente que version corre y se puede volver a una anterior.
        TAG = "${env.BUILD_NUMBER}"
        DEPLOYMENT = 'cafeteria-agustin'
        NAMESPACE = 'alumno-team10'
        URL_PUBLICA = 'https://cafeteria-agustin-team4.reto-ucu.net'
    }

    stages {

        stage('Tests') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --quiet --disable-pip-version-check -r requirements-dev.txt
                    .venv/bin/python -m pytest -v --junitxml=resultados-tests.xml
                '''
            }
            post {
                always {
                    junit 'resultados-tests.xml'
                }
            }
        }

        stage('Build') {
            steps {
                sh 'docker build -t $IMAGEN:$TAG .'
            }
        }

        stage('Push') {
            steps {
                // El token de Docker Hub vive en las credenciales de Jenkins,
                // nunca en el repo. tr limpia un salto de linea que pueda
                // haber quedado al guardar el archivo del token.
                withCredentials([usernamePassword(credentialsId: 'dockerhub',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_TOKEN')]) {
                    sh '''
                        printf '%s' "$DH_TOKEN" | tr -d '\\r\\n' | docker login -u "$DH_USER" --password-stdin
                        docker push $IMAGEN:$TAG
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                // withCredentials deja el kubeconfig en un archivo temporal y
                // apunta KUBECONFIG ahi solo durante este bloque.
                withCredentials([file(credentialsId: 'kubeconfig-ucu', variable: 'KUBECONFIG')]) {
                    sh '''
                        for f in k8s/*.yaml; do
                            sed "s|image: IMAGEN|image: $IMAGEN:$TAG|" "$f"
                            echo "---"
                        done | kubectl -n "$NAMESPACE" apply -f -

                        # Si el pod nuevo no llega a estar listo, volvemos a
                        # la version anterior y el pipeline queda en rojo.
                        if ! kubectl -n "$NAMESPACE" rollout status deployment/$DEPLOYMENT --timeout=180s; then
                            kubectl -n "$NAMESPACE" rollout undo deployment/$DEPLOYMENT
                            exit 1
                        fi
                    '''
                }
            }
        }

        stage('Verificacion') {
            steps {
                // Entramos por la URL publica, como un alumno desde el celular.
                // -k porque el certificado del cluster esta vencido.
                sh 'curl -fsSk --retry 5 --retry-delay 3 --retry-all-errors $URL_PUBLICA/healthz'
            }
        }
    }

    post {
        success {
            echo "Version ${TAG} publicada en ${URL_PUBLICA}"
        }
        failure {
            echo 'Pipeline fallido: revisar la etapa y los logs para confirmar el estado del despliegue.'
        }
    }
}
