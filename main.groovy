pipeline {
    agent {
        label 'kubeagent'
    }
    
    environment {
        DOCKER_HUB_CREDENTIAL = credentials('docker-hub')
        DOCKER_HUB_USERNAME = "rohit055428181"
        VERSION = "latest" // or you can use a specific version
        KUBE_NAMESPACE = "devops-tools" // Update with your Kubernetes namespace
    }
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'patch-1', url: 'https://github.com/rohit200207/Test.git'
            }
        }
        
        stage('Build & Push Image') {
            steps {
                container(name: "kaniko", shell: "/busybox/sh") {
                    script {
                        sh 'mkdir -p /kaniko/.docker'
                        sh "echo '{\"auths\":{\"https://index.docker.io/v1/\":{\"username\":\"${DOCKER_HUB_CREDENTIAL_USR}\",\"password\":\"${DOCKER_HUB_CREDENTIAL_PSW}\"}}}' > /kaniko/.docker/config.json"

                        sh '/kaniko/executor --dockerfile=Dockerfile --context `pwd` --destination="${DOCKER_HUB_USERNAME}/pipeline:${VERSION}"'
                    }
                }
            }
        }
        
        stage('Deploy') {
            steps {
                container(name: "kubectl") {
                    script {
                        sh "sed -i 's|image: .*|image: ${DOCKER_HUB_USERNAME}/pipeline:${VERSION}|' deploymentservice.yml"
                        sh 'kubectl apply -f deploymentservice.yml -n $KUBE_NAMESPACE'
                    }
                }
            }
        }
    }
}
