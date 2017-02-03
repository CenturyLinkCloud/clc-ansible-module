pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building..'
                def app = docker.build "runner/clc-ansible-module:${env.BUILD_NUMBER}"
            }
        }
        stage('Test'){
            steps {
                echo 'Testing..'
            }
        }
    }
}
