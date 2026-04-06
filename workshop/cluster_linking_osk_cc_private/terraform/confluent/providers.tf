terraform {
  required_version = ">= 1.0.0"
  required_providers {
    confluent = {
      source  = "confluentinc/confluent"
      version = "~> 2.65.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "confluent" {
  cloud_api_key    = var.confluent_api_key
  cloud_api_secret = var.confluent_api_secret
}

provider "aws" {
  region = var.aws_region
}