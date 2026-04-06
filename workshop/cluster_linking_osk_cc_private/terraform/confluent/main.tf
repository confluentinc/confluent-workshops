# 1. Confluent Environment & Private Link Attachment
resource "confluent_environment" "main" {
  display_name = "osk-cc-workshop-env"
}

resource "confluent_private_link_attachment" "aws_attachment" {
  display_name = "aws-enterprise-attachment"
  cloud        = "AWS"
  region       = var.aws_region
  
  environment {
    id = confluent_environment.main.id
  }
}

# 2. Confluent Enterprise Cluster
resource "confluent_kafka_cluster" "enterprise_cluster" {
  display_name = "core-enterprise-cluster"
  availability = "MULTI_ZONE"
  cloud        = "AWS"
  region       = var.aws_region
  enterprise {}

  environment {
    id = confluent_environment.main.id
  }
}

# 3. AWS Security Group for VPC Endpoint
resource "aws_security_group" "confluent_endpoint_sg" {
  name        = "confluent-privatelink-sg"
  vpc_id      = var.vpc_id
  description = "Allow Kafka traffic to Confluent Cloud"

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }
}

# 4. AWS VPC Endpoint
resource "aws_vpc_endpoint" "confluent_vpce" {
  vpc_id             = var.vpc_id
  
  # Pulls the endpoint service name from the attachment
  service_name       = confluent_private_link_attachment.aws_attachment.aws[0].vpc_endpoint_service_name
  
  vpc_endpoint_type  = "Interface"
  subnet_ids         = var.subnet_ids
  security_group_ids = [aws_security_group.confluent_endpoint_sg.id]
  private_dns_enabled = false 
}

# 5. Connect the AWS Endpoint to the Confluent Attachment
resource "confluent_private_link_attachment_connection" "aws_connection" {
  display_name = "aws-vpc-endpoint-connection"
  
  environment {
    id = confluent_environment.main.id
  }
  aws {
    vpc_endpoint_id = aws_vpc_endpoint.confluent_vpce.id
  }
  private_link_attachment {
    id = confluent_private_link_attachment.aws_attachment.id
  }
}

# 6. Route 53 Private Hosted Zone & Records (Simplified for Enterprise)
resource "aws_route53_zone" "confluent_zone" {
  name = confluent_private_link_attachment.aws_attachment.dns_domain

  vpc {
    vpc_id = var.vpc_id
  }
}

resource "aws_route53_record" "confluent_wildcard" {
  zone_id = aws_route53_zone.confluent_zone.zone_id
  name    = "*.${confluent_private_link_attachment.aws_attachment.dns_domain}"
  type    = "CNAME"
  ttl     = 60
  records = [aws_vpc_endpoint.confluent_vpce.dns_entry[0].dns_name]
}

