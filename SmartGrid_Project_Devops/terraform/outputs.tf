# Outputs për Terraform

output "vpc_id" {
  description = "ID e VPC-së"
  value       = aws_vpc.smartgrid_vpc.id
}

output "eks_cluster_name" {
  description = "Emri i EKS cluster"
  value       = aws_eks_cluster.smartgrid_cluster.name
}

output "eks_cluster_endpoint" {
  description = "Endpoint i EKS cluster"
  value       = aws_eks_cluster.smartgrid_cluster.endpoint
}

output "rds_endpoint" {
  description = "Endpoint i RDS PostgreSQL"
  value       = aws_db_instance.smartgrid_postgres.endpoint
}

output "redis_endpoint" {
  description = "Endpoint i Redis"
  value       = aws_elasticache_cluster.smartgrid_redis.cache_nodes[0].address
}

output "kafka_brokers" {
  description = "Kafka broker endpoints"
  value       = aws_msk_cluster.smartgrid_kafka.bootstrap_brokers
}

output "public_subnet_ids" {
  description = "IDs e public subnets"
  value       = aws_subnet.public_subnets[*].id
}

output "private_subnet_ids" {
  description = "IDs e private subnets"
  value       = aws_subnet.private_subnets[*].id
}

