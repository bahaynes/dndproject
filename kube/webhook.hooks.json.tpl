[
  {
    "id": "deploy",
    "execute-command": "${DEPLOY_SCRIPT}",
    "command-working-directory": "${REPO_DIR}",
    "response-message": "Deploy triggered",
    "trigger-rule": {
      "and": [
        {
          "match": {
            "type": "payload-hmac-sha256",
            "secret": "${WEBHOOK_SECRET}",
            "parameter": {
              "source": "header",
              "name": "X-Hub-Signature-256"
            }
          }
        },
        {
          "match": {
            "type": "value",
            "value": "refs/heads/main",
            "parameter": {
              "source": "payload",
              "name": "ref"
            }
          }
        }
      ]
    }
  }
]
