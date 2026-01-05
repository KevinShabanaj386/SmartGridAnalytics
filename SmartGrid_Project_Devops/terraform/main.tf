# Terraform Configuration për Smart Grid Analytics Infrastructure
# Kjo konfigurim krijon infrastrukturën në cloud (AWS si shembull)

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
  }
  
  # Backend configuration (opsionale)
  # backend "s3" {
  #   bucket = "smartgrid-terraform-state"
  #   key    = "terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

# VPC për Smart Grid Analytics
resource "aws_vpc" "smartgrid_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "smartgrid-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "smartgrid_igw" {
  vpc_id = aws_vpc.smartgrid_vpc.id

  tags = {
    Name = "smartgrid-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public_subnets" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.smartgrid_vpc.id
  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "smartgrid-public-subnet-${count.index + 1}"
  }
}

# Private Subnets
resource "aws_subnet" "private_subnets" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.smartgrid_vpc.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "smartgrid-private-subnet-${count.index + 1}"
  }
}

# Route Table për Public Subnets
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.smartgrid_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.smartgrid_igw.id
  }

  tags = {
    Name = "smartgrid-public-rt"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public_rta" {
  count          = length(aws_subnet.public_subnets)
  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_rt.id
}

# EKS Cluster për Kubernetes
resource "aws_eks_cluster" "smartgrid_cluster" {
  name     = "smartgrid-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.28"

  vpc_config {
    subnet_ids = concat(aws_subnet.public_subnets[*].id, aws_subnet.private_subnets[*].id)
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]

  tags = {
    Name = "smartgrid-eks-cluster"
    Environment = var.environment
  }
}

# EKS Node Group
resource "aws_eks_node_group" "smartgrid_nodes" {
  cluster_name    = aws_eks_cluster.smartgrid_cluster.name
  node_group_name = "smartgrid-nodes"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = aws_subnet.private_subnets[*].id

  scaling_config {
    desired_size = 3
    max_size     = 10
    min_size     = 2
  }

  instance_types = ["t3.medium"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]

  tags = {
    Name = "smartgrid-node-group"
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "smartgrid_postgres" {
  identifier     = "smartgrid-postgres"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  storage_encrypted      = true

  db_name  = "smartgrid_db"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.smartgrid_db_subnet.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "smartgrid-postgres-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = {
    Name = "smartgrid-postgres"
    Environment = var.environment
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "smartgrid_db_subnet" {
  name       = "smartgrid-db-subnet"
  subnet_ids = aws_subnet.private_subnets[*].id

  tags = {
    Name = "smartgrid-db-subnet-group"
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "smartgrid_redis" {
  cluster_id           = "smartgrid-redis"
  engine               = "redis"
  node_type            = "cache.t3.medium"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.smartgrid_redis_subnet.name
  security_group_ids   = [aws_security_group.redis_sg.id]

  tags = {
    Name = "smartgrid-redis"
  }
}

resource "aws_elasticache_subnet_group" "smartgrid_redis_subnet" {
  name       = "smartgrid-redis-subnet"
  subnet_ids = aws_subnet.private_subnets[*].id
}

# MSK (Managed Kafka) Cluster
resource "aws_msk_cluster" "smartgrid_kafka" {
  cluster_name           = "smartgrid-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    ebs_volume_size = 100
    client_subnets  = aws_subnet.private_subnets[*].id
    security_groups = [aws_security_group.kafka_sg.id]
  }

  encryption_info {
    encryption_at_rest_kms_key_id = aws_kms_key.kafka_key.arn
  }

  tags = {
    Name = "smartgrid-kafka"
    Environment = var.environment
  }
}

# KMS Key për Kafka encryption
resource "aws_kms_key" "kafka_key" {
  description = "KMS key for Kafka encryption"
  
  tags = {
    Name = "smartgrid-kafka-key"
  }
}

# Security Groups
resource "aws_security_group" "rds_sg" {
  name_prefix = "smartgrid-rds-"
  vpc_id      = aws_vpc.smartgrid_vpc.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "smartgrid-rds-sg"
  }
}

resource "aws_security_group" "redis_sg" {
  name_prefix = "smartgrid-redis-"
  vpc_id      = aws_vpc.smartgrid_vpc.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "smartgrid-redis-sg"
  }
}

resource "aws_security_group" "kafka_sg" {
  name_prefix = "smartgrid-kafka-"
  vpc_id      = aws_vpc.smartgrid_vpc.id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "smartgrid-kafka-sg"
  }
}

# IAM Roles
resource "aws_iam_role" "eks_cluster_role" {
  name = "smartgrid-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

resource "aws_iam_role" "eks_node_role" {
  name = "smartgrid-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node_role.name
}

# Data Sources
data "aws_availability_zones" "available" {
  state = "available"
}

