data "aws_caller_identity" "current" {}

output "aws_account_id" {
  description = "The AWS Account ID."
  value       = data.aws_caller_identity.current.account_id
}

output "vpc_id" {
  description = "The ID of the VPC."
  value       = aws_vpc.main.id
}

output "kafka_public_dns" {
  description = "The public dns address of the Kafka EC2 instance."
  value       = aws_instance.kafka_ec2.public_dns
}

output "jumpbox_public_dns" {
  description = "The public dns address of the Jumpbox EC2 instance."
  value       = aws_instance.jumpbox_ec2.public_dns
}

output "aws_zones" {
  description = "The AWS Availability Zone IDs where the subnets are deployed."
  value       = [
    aws_subnet.public_1.availability_zone_id, 
    aws_subnet.public_2.availability_zone_id, 
    aws_subnet.public_3.availability_zone_id
  ]
}

output "subnet_ids" {
  description = "The IDs of the 3 created subnets."
  value       = [
    aws_subnet.public_1.id, 
    aws_subnet.public_2.id, 
    aws_subnet.public_3.id
  ]
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC."
  value       = aws_vpc.main.cidr_block
}

