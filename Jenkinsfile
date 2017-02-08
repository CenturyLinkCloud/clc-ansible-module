node {
        stage("Main build") {

            checkout scm

            docker.image('alpine:latest').inside {

              stage("Setup") {
                sh "python setup.py build"
              }

           }

        }

        // Clean up workspace
        step([$class: 'WsCleanup'])

}
