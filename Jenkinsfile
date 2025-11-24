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
                        url: 'https://github.com/ihazratummar/your-discord-bot-repo.git',
                        credentialsId: 'github-creds'
                    ]]
                ])
                echo "✅ Code pulled successfully"
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                    docker build -t ${IMAGE} .
                """
                echo "🐳 Docker image built"
            }
        }

        stage('Stop Old Container') {
            steps {
                sh """
                    if docker ps -aq -f name=^${CONTAINER}\$; then
                        docker stop ${CONTAINER} || true
                        docker rm ${CONTAINER} || true
                    fi
                """
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

        stage('Run New Container') {
            steps {
                sh """
                    docker run -d \
                        --name ${CONTAINER} \
                        --env-file ${ENV_FILE} \
                        --restart unless-stopped \
                        ${IMAGE}
                """
                echo "🤖 Nexa bot is now running"
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
