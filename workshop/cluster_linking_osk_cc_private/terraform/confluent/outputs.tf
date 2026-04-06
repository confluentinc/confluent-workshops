output "confluent_bootstrap_servers" {
  value       = confluent_kafka_cluster.enterprise_cluster.bootstrap_endpoint
  description = "The bootstrap server endpoint for the Kafka Cluster"
}

output "aws_vpc_endpoint_id" {
  value       = aws_vpc_endpoint.confluent_vpce.id
  description = "The ID of the AWS VPC Endpoint"
}