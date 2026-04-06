variable "confluent_api_key" {
  type        = string
  sensitive   = true
  description = "Confluent Cloud API Key"
}

variable "confluent_api_secret" {
  type        = string
  sensitive   = true
  description = "Confluent Cloud API Secret"
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for the VPC and Confluent Cluster"
}

variable "aws_account_id" {
  type        = string
  description = "Your 12-digit AWS Account ID"
}

variable "aws_zones" {
  type        = list(string)
  description = "AWS AZ IDs (not names) corresponding to your subnets (e.g., use1-az1, use1-az2, use1-az4)"
}

variable "vpc_id" {
  type        = string
  description = "The ID of the AWS VPC where the Endpoint will be created"
}

variable "subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs in your AWS VPC to attach the Endpoint to"
}

variable "vpc_cidr_block" {
  type        = string
  description = "The CIDR block of your VPC to whitelist in the Security Group"
}