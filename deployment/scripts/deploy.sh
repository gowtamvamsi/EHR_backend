#!/bin/bash
set -e

# Build and push Docker image
docker build -t ehs-backend .
docker tag ehs-backend:latest $ECR_REPO/ehs-backend:$IMAGE_TAG
docker push $ECR_REPO/ehs-backend:$IMAGE_TAG

# Apply Terraform changes
cd deployment/terraform
terraform init
terraform apply -var-file=env/${ENVIRONMENT}.tfvars -auto-approve

# Run database migrations
aws ecs run-task \
    --cluster ehs-cluster-${ENVIRONMENT} \
    --task-definition ehs-migration-${ENVIRONMENT} \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_IDS}],securityGroups=[${SECURITY_GROUP_IDS}]}"

# Update ECS services
aws ecs update-service \
    --cluster ehs-cluster-${ENVIRONMENT} \
    --service ehs-api-${ENVIRONMENT} \
    --force-new-deployment

# Update Celery workers
aws ecs update-service \
    --cluster ehs-cluster-${ENVIRONMENT} \
    --service ehs-celery-high-${ENVIRONMENT} \
    --force-new-deployment

aws ecs update-service \
    --cluster ehs-cluster-${ENVIRONMENT} \
    --service ehs-celery-default-${ENVIRONMENT} \
    --force-new-deployment