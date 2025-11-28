pipeline {
    agent any

    environment {
        IMAGE = "nexa-bot:v1"
        CONTAINER = "Nexa"
        ENV_FILE = "/home/envs/nexa.env"
    }

    stages {

        stage('Pull Code') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/ihazratummar/Nexa',
                        credentialsId: 'github-creds'
                    ]]
                ])
                echo "✅ Code pulled successfully"
            }
        }

        stage('Verify ENV File') {
            steps {
                sh """
                    if [ ! -f ${ENV_FILE} ]; then
                        echo "❌ Missing nexa.env at ${ENV_FILE}"
                        exit 1
                    fi
                    echo "✅ ENV file verified"
                """
            }
        }

        stage('Deploy with Docker Compose') {
            steps {
                sh """
                    docker version
                    docker compose version || echo "docker compose not found"
                    docker compose build
                    docker compose up --detach --remove-orphans
                """
                echo "🚀 Nexa Bot & Redis deployed successfully"
            }
        }
    }

    post {
        success {
            echo "🎉 Nexa Bot deployed successfully!"
        }
        failure {
            echo "❌ Deployment failed — fetching logs..."
            sh "docker logs ${CONTAINER} || true"
        }
        always {
            echo "✔ Pipeline complete."
        }
    }
}
