#!/bin/bash

# Configuration
GITHUB_USERNAME="Fokoue22"
REPO_NAME="Systeme-de-reservation-plateaux-sportifs"
PIPELINE_NAME="reservation-app-pipeline"
BUCKET_NAME="systeme-de-reservation-plateaux-sportifs"
REGION="us-east-1"

# Créer le pipeline
aws codepipeline create-pipeline \
  --cli-input-json file://codepipeline-config.json \
  --region $REGION

# Remplacer les valeurs dans la configuration
sed -i "s/YOUR_GITHUB_USERNAME/$GITHUB_USERNAME/g" codepipeline-config.json
sed -i "s/YOUR_REPO_NAME/$REPO_NAME/g" codepipeline-config.json

echo "Pipeline créé avec succès: $PIPELINE_NAME"
echo "Le pipeline se déclenchera automatiquement lors de push sur la branche main"
