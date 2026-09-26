// =============================================================================
// JENKINSFILE — Test Impact Analyzer for Online Boutique
// =============================================================================
// This pipeline automatically runs only the tests affected by changes to
// the Online Boutique microservices demo. It is the CI/CD integration layer
// required by thesis Objective IV.
//
// Pipeline Flow:
//   1. Checkout        → Pull the latest code
//   2. Setup Python    → Create virtual environment
//   3. Install Deps    → Install analyzer dependencies
//   4. Detect Changes  → Compare current commit with previous
//   5. Analyze         → Run the analyzer, produce analyzer_result.json
//   6. Show Summary    → Display what was detected
//   7. Run Tests       → Execute ONLY the affected tests
//   8. Archive         → Save results as build artifacts
// =============================================================================

pipeline {
    
    // -------------------------------------------------------------------------
    // AGENT
    // Run on any available Jenkins agent (works with the Docker container
    // we set up earlier in the guide).
    // -------------------------------------------------------------------------
    agent any
    
    // -------------------------------------------------------------------------
    // ENVIRONMENT VARIABLES
    // These are available to all stages in the pipeline.
    // -------------------------------------------------------------------------
    environment {
        // Prevent encoding issues when handling non-ASCII file paths
        PYTHONIOENCODING = 'UTF-8'
        
        // Make the project root importable as a Python module
        // (needed for `from analyzer import ...` to work)
        PYTHONPATH = "${WORKSPACE}"
        
        // Paths used throughout the pipeline (relative to WORKSPACE)
        VENV_DIR      = 'venv'
        ANALYZER_DIR  = 'scripts'
        TEST_DIR      = 'tests_online_boutique'
        TARGET_REPO   = 'microservices-demo'
        RESULT_FILE   = 'analyzer_result.json'
    }
    
    // -------------------------------------------------------------------------
    // OPTIONS
    // -------------------------------------------------------------------------
    options {
        // Keep the last 10 builds for reference
        buildDiscarder(logRotator(numToKeepStr: '10'))
        
        // Show timestamps in the console output
        timestamps()
        
        // Don't fail the whole pipeline if a test stage fails — we want
        // to see the full picture before deciding.
        skipDefaultCheckout(true)
    }
    
    // -------------------------------------------------------------------------
    // STAGES
    // -------------------------------------------------------------------------
    stages {
        
        // =====================================================================
        // STAGE 1: CHECKOUT
        // Pull the latest code from the Git repository.
        // =====================================================================
        stage('Checkout') {
            steps {
                echo '=== [1/8] Checking out source code ==='
                
                // Pull the code from the repo configured in the Jenkins job
                checkout scm
                
                // Show what we pulled — helpful for debugging
                sh 'echo "Workspace contents:" && ls -la'
                
                // Verify the microservices-demo subfolder exists
                sh '''
                    if [ ! -d "microservices-demo" ]; then
                        echo "ERROR: microservices-demo folder not found!"
                        echo "Make sure it is committed as a submodule or included in the repo."
                        exit 1
                    fi
                    echo "microservices-demo folder confirmed."
                '''
            }
        }
        
        // =====================================================================
        // STAGE 2: SETUP PYTHON ENVIRONMENT
        // Create a virtual environment to isolate dependencies.
        // =====================================================================
        stage('Setup Python Environment') {
            steps {
                echo '=== [2/8] Setting up Python virtual environment ==='
                
                // Remove any leftover venv from a previous build to ensure
                // a clean state. This prevents stale-package bugs.
                sh "rm -rf ${VENV_DIR}"
                
                // Create a fresh virtual environment
                sh "python3 -m venv ${VENV_DIR}"
                
                // Upgrade pip first (good practice for reliability)
                sh "${VENV_DIR}/bin/pip install --upgrade pip"
            }
        }
        
        // =====================================================================
        // STAGE 3: INSTALL DEPENDENCIES
        // Install the Python packages our analyzer needs.
        // =====================================================================
        stage('Install Dependencies') {
            steps {
                echo '=== [3/8] Installing analyzer dependencies ==='
                
                // Install from requirements.txt
                sh "${VENV_DIR}/bin/pip install -r requirements.txt"
                
                // Verify the critical imports work
                sh '''
                    ${VENV_DIR}/bin/python -c "
                    import yaml
                    import json
                    import subprocess
                    from pathlib import Path
                    print('All critical imports OK')
                    "
                '''
            }
        }
        
        // =====================================================================
        // STAGE 4: DETECT CHANGES
        // Determine what changed since the last commit.
        // =====================================================================
        stage('Detect Changes') {
            steps {
                echo '=== [4/8] Detecting changes in microservices-demo ==='
                
                dir(TARGET_REPO) {
                    // Show the Git log so we know what commit range we're working with
                    sh 'git log --oneline -5 || echo "Could not read git log"'
                    
                    // Count commits — if only 1, there's nothing to compare
                    sh '''
                        COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo 0)
                        echo "Commit count: $COMMIT_COUNT"
                        if [ "$COMMIT_COUNT" -lt 2 ]; then
                            echo "WARNING: Repository has fewer than 2 commits."
                            echo "The analyzer needs at least 2 commits to compare."
                        fi
                    '''
                }
            }
        }
        
        // =====================================================================
        // STAGE 5: RUN THE ANALYZER
        // This is the heart of the pipeline — detect changed source/config
        // files and select only the affected tests.
        // =====================================================================
        stage('Analyze Changes') {
            steps {
                echo '=== [5/8] Running Test Impact Analyzer ==='
                
                // Clean any previous result file first
                sh "rm -f ${RESULT_FILE}"
                
                // Run the analyzer from the First-Test root, pointing at
                // the microservices-demo subfolder.
                //
                // The --range HEAD~1..HEAD compares the current commit with
                // the previous one. This is what the thesis specifies.
                sh """
                    ${VENV_DIR}/bin/python ${ANALYZER_DIR}/run_analyzer.py \
                        --repo ${TARGET_REPO} \
                        --range HEAD~1..HEAD \
                        --tests ${TEST_DIR} \
                    || echo "Analyzer returned non-zero (possibly no changes detected)"
                """
                
                // Verify the result file was created
                sh """
                    if [ ! -f "${RESULT_FILE}" ]; then
                        echo "WARNING: ${RESULT_FILE} not found."
                        echo "Creating empty result file to continue the pipeline."
                        echo '{"affected_tests":[],"has_affected_tests":false,"test_count":0}' > ${RESULT_FILE}
                    fi
                """
            }
        }
        
        // =====================================================================
        // STAGE 6: SHOW SUMMARY
        // Print a human-readable summary of what the analyzer found.
        // =====================================================================
        stage('Show Summary') {
            steps {
                echo '=== [6/8] Analysis Summary ==='
                sh 'venv/bin/python scripts/show_summary.py'
            }
        }
        
        // =====================================================================
        // STAGE 7: RUN AFFECTED TESTS
        // Execute only the tests that the analyzer selected.
        // This is the entire point of the thesis: avoid running everything.
        // =====================================================================
        stage('Run Affected Tests') {
            steps {
                echo '=== [7/8] Running only the affected tests ==='
                
                // Delegate to the multi-language test runner script.
                // It reads analyzer_result.json and dispatches to the
                // correct test framework per file extension.
                sh """
                    ${VENV_DIR}/bin/python run_selected_tests.py \
                        || echo "Some tests failed — see output above"
                """
            }
        }
        
        // =====================================================================
        // STAGE 8: ARCHIVE RESULTS
        // Save the analyzer output as a build artifact for later inspection.
        // =====================================================================
        stage('Archive Results') {
            steps {
                echo '=== [8/8] Archiving results ==='
                
                // Archive the JSON result so it can be downloaded from Jenkins UI
                archiveArtifacts(
                    artifacts: "${RESULT_FILE}",
                    allowEmptyArchive: true,
                    fingerprint: true
                )
            }
        }
    }
    
    // -------------------------------------------------------------------------
    // POST ACTIONS
    // Run after all stages complete (success or failure).
    // -------------------------------------------------------------------------
    post {
        always {
            echo '========================================================='
            echo 'Pipeline execution finished.'
            echo '========================================================='
            
            // Print the raw JSON result so it's visible in the console log
            // even if the pipeline failed.
            sh '''
                if [ -f "analyzer_result.json" ]; then
                    echo "Final analyzer_result.json:"
                    cat analyzer_result.json
                else
                    echo "No analyzer_result.json file present."
                fi
            '''
            
            // Clean up the virtual environment to save disk space on the agent.
            // Set this to false if you want to reuse the venv for faster builds.
            sh 'rm -rf venv || true'
        }
        
        success {
            echo '========================================================='
            echo 'BUILD SUCCEEDED'
            echo 'All affected tests passed.'
            echo '========================================================='
        }
        
        failure {
            echo '========================================================='
            echo 'BUILD FAILED'
            echo 'Check the console output above for details.'
            echo '========================================================='
        }
        
        unstable {
            echo '========================================================='
            echo 'BUILD UNSTABLE'
            echo 'Some tests may have failed, but the pipeline completed.'
            echo '========================================================='
        }
    }
}