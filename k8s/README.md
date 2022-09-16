# Deploying Label Studio to an EKS Cluster

## One-Time AWS Load Balancer Controller add-on installation

The service is load balanced by an AWS Application Load Balancer created via a Kubernetes Ingress. The creation of the Ingress will not do anything unless there is a load balancer controller watching for it. Follow the [instructions](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html) to install the Load Balancer Controller into the cluster. `kubectl get deployment -n kube-system aws-load-balancer-controller` will tell you whether this has already been done assuming it is installed into the namespace and with the name as described below.

```sh
# Download the IAM policy for the load balancer controller
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.4.2/docs/install/iam_policy.json

# Create the IAM policy
aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

# Create the service account using eksctl
eksctl create iamserviceaccount \
  --cluster=dev-cortex \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name "AmazonEKSLoadBalancerControllerRole" \
  --attach-policy-arn=arn:aws:iam::516490962685:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Add the EKS Charts Helm repo
helm repo add eks https://aws.github.io/eks-charts
helm repo update


# Install the Load Balancer Controller using Helm
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=dev-cortex \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set image.repository=602401143452.dkr.ecr.us-east-1.amazonaws.com/amazon/aws-load-balancer-controller

# Verify that the deployment exists and is healthy
kubectl get deployment -n kube-system aws-load-balancer-controller
```

## Basic Deployment

1. Ensure your kubectl context is pointed to the intended cluster.
2. `kubectl apply -f label-studio-manifest.yaml`

## Checking Status

1. `kubectl get statefulsets.apps --namespace label-studio`
2. `kubectl get services --namespace label-studio`
3. `kubectl get pods --namespace label-studio`
4. `kubectl get ingress --namespace label-studio`

## Using Custom DNS

1. In the AWS Console, create an ACM Certificate for the desired domain.
2. Replace with the certificate ARN in the Ingress resource in `label-studio-manifest.yaml`
3. Follow the instructions to satisfy the DNS challenge by adding the CNAME records as instructed via your DNS provider (e.g., Cloudflare).
